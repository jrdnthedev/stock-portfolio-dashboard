"""Tests for PortfolioService using Repository Pattern with mock repositories."""

from unittest.mock import MagicMock, Mock
from uuid import UUID, uuid4

import pytest

from domains.portfolio.services.portfolio_service import PortfolioService

# noqa comments prevent ruff from removing these fixture imports
from tests.test_fixtures import (  # noqa: F401
    mock_holding_repo,
    mock_kafka_producer,
    mock_portfolio_repo,
)


@pytest.fixture
def service(
    mock_portfolio_repo: Mock,
    mock_holding_repo: Mock,
    mock_kafka_producer: MagicMock,
) -> PortfolioService:
    """Create PortfolioService with mock repositories."""
    _ = mock_kafka_producer
    return PortfolioService(
        portfolio_repo=mock_portfolio_repo,
        holding_repo=mock_holding_repo,
        kafka_bootstrap_servers=["localhost:9092"],
        topic="test.topic",
    )


class TestPortfolioServiceInit:
    def test_init_creates_kafka_producer(
        self,
        mock_portfolio_repo: Mock,
        mock_holding_repo: Mock,
        mock_kafka_producer: MagicMock,
    ) -> None:
        service = PortfolioService(
            portfolio_repo=mock_portfolio_repo,
            holding_repo=mock_holding_repo,
            kafka_bootstrap_servers=["localhost:9092"],
            topic="test.topic",
        )
        assert service.topic == "test.topic"
        assert service.producer == mock_kafka_producer
        assert service.portfolio_repo == mock_portfolio_repo
        assert service.holding_repo == mock_holding_repo


class TestPortfolioServicePortfolioCRUD:
    def test_create_portfolio(self, service: PortfolioService) -> None:
        portfolio = service.create_portfolio("My Portfolio", "user1", "EUR")
        assert portfolio.name == "My Portfolio"
        assert portfolio.owner == "user1"
        assert portfolio.currency == "EUR"
        assert isinstance(portfolio.id, UUID)
        service.portfolio_repo.create.assert_called_once()

    def test_create_portfolio_defaults_to_usd(self, service: PortfolioService) -> None:
        portfolio = service.create_portfolio("My Portfolio", "user1")
        assert portfolio.currency == "USD"

    def test_get_portfolio_returns_existing(self, service: PortfolioService) -> None:
        created = service.create_portfolio("Test", "user1")
        retrieved = service.get_portfolio(created.id)
        assert retrieved == created

    def test_get_portfolio_returns_none_if_not_found(self, service: PortfolioService) -> None:
        result = service.get_portfolio(uuid4())
        assert result is None

    def test_list_portfolios_returns_all(self, service: PortfolioService) -> None:
        p1 = service.create_portfolio("Portfolio 1", "user1")
        p2 = service.create_portfolio("Portfolio 2", "user2")
        portfolios = service.list_portfolios()
        assert len(portfolios) == 2
        assert p1 in portfolios
        assert p2 in portfolios

    def test_list_portfolios_filters_by_owner(self, service: PortfolioService) -> None:
        p1 = service.create_portfolio("Portfolio 1", "user1")
        _ = service.create_portfolio("Portfolio 2", "user2")
        user1_portfolios = service.list_portfolios(owner="user1")
        assert len(user1_portfolios) == 1
        assert user1_portfolios[0] == p1

    def test_update_portfolio_name(self, service: PortfolioService) -> None:
        portfolio = service.create_portfolio("Old Name", "user1")
        updated = service.update_portfolio(portfolio.id, name="New Name")
        assert updated is not None
        assert updated.name == "New Name"
        assert updated.currency == "USD"

    def test_update_portfolio_currency(self, service: PortfolioService) -> None:
        portfolio = service.create_portfolio("Test", "user1", "USD")
        updated = service.update_portfolio(portfolio.id, currency="EUR")
        assert updated is not None
        assert updated.currency == "EUR"

    def test_update_portfolio_returns_none_if_not_found(self, service: PortfolioService) -> None:
        result = service.update_portfolio(uuid4(), name="New Name")
        assert result is None

    def test_delete_portfolio(self, service: PortfolioService) -> None:
        portfolio = service.create_portfolio("Test", "user1")
        result = service.delete_portfolio(portfolio.id)
        assert result is True
        service.holding_repo.delete_by_portfolio.assert_called_with(portfolio.id)
        service.portfolio_repo.delete.assert_called_with(portfolio.id)

    def test_delete_portfolio_returns_false_if_not_found(self, service: PortfolioService) -> None:
        result = service.delete_portfolio(uuid4())
        assert result is False

    def test_delete_portfolio_deletes_associated_holdings(self, service: PortfolioService) -> None:
        portfolio = service.create_portfolio("Test", "user1")
        _ = service.create_holding(portfolio.id, uuid4(), 100.0, 50.0)
        _ = service.create_holding(portfolio.id, uuid4(), 200.0, 75.0)
        service.delete_portfolio(portfolio.id)
        service.holding_repo.delete_by_portfolio.assert_called_with(portfolio.id)


class TestPortfolioServiceHoldingCRUD:
    def test_create_holding(
        self, service: PortfolioService, mock_kafka_producer: MagicMock
    ) -> None:
        portfolio = service.create_portfolio("Test", "user1")
        ticker_id = uuid4()
        holding = service.create_holding(portfolio.id, ticker_id, 150.0, 45.5)

        assert holding is not None
        assert holding.portfolio_id == portfolio.id
        assert holding.ticker_id == ticker_id
        assert holding.quantity == 150.0
        assert holding.avg_cost_basis == 45.5
        assert isinstance(holding.id, UUID)

        service.holding_repo.create.assert_called_once()
        mock_kafka_producer.send.assert_called()
        mock_kafka_producer.flush.assert_called()

    def test_create_holding_publishes_event(
        self, service: PortfolioService, mock_kafka_producer: MagicMock
    ) -> None:
        portfolio = service.create_portfolio("Test", "user1")
        holding = service.create_holding(portfolio.id, uuid4(), 100.0, 50.0)

        assert holding is not None
        args, _ = mock_kafka_producer.send.call_args
        assert args[0] == "test.topic"
        event = args[1]
        assert event["event"] == "HoldingChanged"
        assert event["event_type"] == "created"
        assert "timestamp" in event
        assert event["data"]["id"] == str(holding.id)

    def test_create_holding_returns_none_if_portfolio_not_found(
        self, service: PortfolioService
    ) -> None:
        result = service.create_holding(uuid4(), uuid4(), 100.0, 50.0)
        assert result is None

    def test_get_holding_returns_existing(self, service: PortfolioService) -> None:
        portfolio = service.create_portfolio("Test", "user1")
        created = service.create_holding(portfolio.id, uuid4(), 100.0, 50.0)
        assert created is not None
        retrieved = service.get_holding(created.id)
        assert retrieved == created

    def test_get_holding_returns_none_if_not_found(self, service: PortfolioService) -> None:
        result = service.get_holding(uuid4())
        assert result is None

    def test_list_holdings(self, service: PortfolioService) -> None:
        p1 = service.create_portfolio("Portfolio 1", "user1")
        p2 = service.create_portfolio("Portfolio 2", "user1")
        h1 = service.create_holding(p1.id, uuid4(), 100.0, 50.0)
        h2 = service.create_holding(p1.id, uuid4(), 200.0, 75.0)
        h3 = service.create_holding(p2.id, uuid4(), 300.0, 100.0)

        p1_holdings = service.list_holdings(p1.id)
        assert len(p1_holdings) == 2
        assert h1 in p1_holdings
        assert h2 in p1_holdings
        assert h3 not in p1_holdings

    def test_update_holding_quantity(
        self, service: PortfolioService, mock_kafka_producer: MagicMock
    ) -> None:
        portfolio = service.create_portfolio("Test", "user1")
        holding = service.create_holding(portfolio.id, uuid4(), 100.0, 50.0)
        assert holding is not None

        mock_kafka_producer.reset_mock()
        updated = service.update_holding(holding.id, quantity=150.0)
        assert updated is not None
        assert updated.quantity == 150.0
        assert updated.avg_cost_basis == 50.0

        args, _ = mock_kafka_producer.send.call_args
        event = args[1]
        assert event["event_type"] == "updated"

    def test_update_holding_avg_cost_basis(self, service: PortfolioService) -> None:
        portfolio = service.create_portfolio("Test", "user1")
        holding = service.create_holding(portfolio.id, uuid4(), 100.0, 50.0)
        assert holding is not None

        updated = service.update_holding(holding.id, avg_cost_basis=55.0)
        assert updated is not None
        assert updated.quantity == 100.0
        assert updated.avg_cost_basis == 55.0

    def test_update_holding_returns_none_if_not_found(self, service: PortfolioService) -> None:
        result = service.update_holding(uuid4(), quantity=100.0)
        assert result is None

    def test_delete_holding(
        self, service: PortfolioService, mock_kafka_producer: MagicMock
    ) -> None:
        portfolio = service.create_portfolio("Test", "user1")
        holding = service.create_holding(portfolio.id, uuid4(), 100.0, 50.0)
        assert holding is not None

        mock_kafka_producer.reset_mock()
        result = service.delete_holding(holding.id)
        assert result is True
        service.holding_repo.delete.assert_called_with(holding.id)

    def test_delete_holding_returns_false_if_not_found(self, service: PortfolioService) -> None:
        result = service.delete_holding(uuid4())
        assert result is False
