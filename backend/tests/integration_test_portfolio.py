"""Integration tests for portfolio API endpoints using testcontainers."""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database.models import Holding, Portfolio, Ticker

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def sample_tickers(db_session: Session) -> list[Ticker]:
    """Create sample tickers for testing."""
    tickers = [
        Ticker(
            id=uuid4(),
            symbol="AAPL",
            company_name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            asset_class="Stock",
        ),
        Ticker(
            id=uuid4(),
            symbol="GOOGL",
            company_name="Alphabet Inc.",
            exchange="NASDAQ",
            sector="Technology",
            asset_class="Stock",
        ),
        Ticker(
            id=uuid4(),
            symbol="MSFT",
            company_name="Microsoft Corporation",
            exchange="NASDAQ",
            sector="Technology",
            asset_class="Stock",
        ),
    ]

    for ticker in tickers:
        db_session.add(ticker)
    db_session.commit()

    return tickers


@pytest.fixture
def sample_portfolio(db_session: Session) -> Portfolio:
    """Create a sample portfolio for testing."""
    portfolio = Portfolio(
        id=uuid4(),
        name="Test Growth Portfolio",
        owner="test_user",
        currency="USD",
        created_at=datetime.now(),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    return portfolio


@pytest.fixture
def sample_holdings(
    db_session: Session, sample_portfolio: Portfolio, sample_tickers: list[Ticker]
) -> list[Holding]:
    """Create sample holdings for testing."""
    holdings = [
        Holding(
            id=uuid4(),
            portfolio_id=sample_portfolio.id,
            ticker_id=sample_tickers[0].id,  # AAPL
            quantity=100.0,
            avg_cost_basis=150.0,
            opened_at=datetime.now(),
        ),
        Holding(
            id=uuid4(),
            portfolio_id=sample_portfolio.id,
            ticker_id=sample_tickers[1].id,  # GOOGL
            quantity=50.0,
            avg_cost_basis=2800.0,
            opened_at=datetime.now(),
        ),
    ]

    for holding in holdings:
        db_session.add(holding)
    db_session.commit()

    return holdings


class TestGetPortfolioIntegration:
    """Integration tests for GET /v1/portfolio/{id}."""

    def test_get_portfolio_success(
        self, client: TestClient, sample_portfolio: Portfolio, disable_cache
    ):
        """Test retrieving an existing portfolio from database."""
        response = client.get(f"/v1/portfolio/{sample_portfolio.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Portfolio" in data["message"]
        assert data["data"]["id"] == str(sample_portfolio.id)
        assert data["data"]["name"] == "Test Growth Portfolio"
        assert data["data"]["owner"] == "test_user"

    def test_get_portfolio_not_found(self, client: TestClient, disable_cache):
        """Test retrieving a non-existent portfolio."""
        fake_id = uuid4()
        response = client.get(f"/v1/portfolio/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()


class TestGetHoldingsIntegration:
    """Integration tests for GET /v1/portfolio/{id}/holdings."""

    def test_get_holdings_success(
        self,
        client: TestClient,
        sample_portfolio: Portfolio,
        sample_holdings: list[Holding],
        disable_cache,
    ):
        """Test retrieving holdings for a portfolio."""
        response = client.get(f"/v1/portfolio/{sample_portfolio.id}/holdings")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2
        assert data["metadata"]["portfolio_id"] == str(sample_portfolio.id)
        assert data["metadata"]["count"] == 2

        # Verify holding details
        holding_tickers = {h["ticker"]["symbol"] for h in data["data"]}
        assert "AAPL" in holding_tickers
        assert "GOOGL" in holding_tickers

    def test_get_holdings_empty_portfolio(
        self, client: TestClient, sample_portfolio: Portfolio, disable_cache
    ):
        """Test retrieving holdings from a portfolio with no holdings."""
        response = client.get(f"/v1/portfolio/{sample_portfolio.id}/holdings")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0
        assert data["metadata"]["count"] == 0

    def test_get_holdings_portfolio_not_found(self, client: TestClient, disable_cache):
        """Test retrieving holdings for a non-existent portfolio."""
        fake_id = uuid4()
        response = client.get(f"/v1/portfolio/{fake_id}/holdings")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestCreateHoldingIntegration:
    """Integration tests for POST /v1/portfolio/{id}/holdings."""

    def test_create_holding_success(
        self,
        client: TestClient,
        sample_portfolio: Portfolio,
        sample_tickers: list[Ticker],
        disable_cache,
    ):
        """Test creating a new holding in a portfolio."""
        holding_data = {
            "ticker": "AAPL",
            "quantity": 150.0,
            "average_cost": 175.50,
            "purchased_at": "2026-04-01T10:00:00Z",
        }

        response = client.post(
            f"/v1/portfolio/{sample_portfolio.id}/holdings",
            json=holding_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "created" in data["message"].lower()
        assert data["data"]["ticker"]["symbol"] == "AAPL"
        assert data["data"]["quantity"] == 150.0
        assert data["data"]["avg_cost_basis"] == 175.50

    def test_create_holding_invalid_ticker(
        self, client: TestClient, sample_portfolio: Portfolio, disable_cache
    ):
        """Test creating a holding with an invalid ticker."""
        holding_data = {
            "ticker": "INVALID",
            "quantity": 100.0,
            "average_cost": 50.0,
        }

        response = client.post(
            f"/v1/portfolio/{sample_portfolio.id}/holdings",
            json=holding_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "ticker" in data["message"].lower()

    def test_create_holding_invalid_quantity(
        self,
        client: TestClient,
        sample_portfolio: Portfolio,
        sample_tickers: list[Ticker],
        disable_cache,
    ):
        """Test creating a holding with invalid quantity."""
        holding_data = {
            "ticker": "AAPL",
            "quantity": -10.0,  # Invalid negative quantity
            "average_cost": 175.50,
        }

        response = client.post(
            f"/v1/portfolio/{sample_portfolio.id}/holdings",
            json=holding_data,
        )

        assert response.status_code == 422  # Validation error

    def test_create_holding_portfolio_not_found(
        self, client: TestClient, sample_tickers: list[Ticker], disable_cache
    ):
        """Test creating a holding in a non-existent portfolio."""
        fake_id = uuid4()
        holding_data = {
            "ticker": "AAPL",
            "quantity": 100.0,
            "average_cost": 150.0,
        }

        response = client.post(
            f"/v1/portfolio/{fake_id}/holdings",
            json=holding_data,
        )

        assert response.status_code == 404


class TestUpdateHoldingIntegration:
    """Integration tests for PUT /v1/portfolio/{id}/holdings/{hid}."""

    def test_update_holding_success(
        self,
        client: TestClient,
        sample_portfolio: Portfolio,
        sample_holdings: list[Holding],
        disable_cache,
    ):
        """Test updating an existing holding."""
        holding_id = sample_holdings[0].id
        update_data = {
            "quantity": 200.0,
            "average_cost": 160.0,
        }

        response = client.put(
            f"/v1/portfolio/{sample_portfolio.id}/holdings/{holding_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["quantity"] == 200.0
        assert data["data"]["avg_cost_basis"] == 160.0

    def test_update_holding_partial_update(
        self,
        client: TestClient,
        sample_portfolio: Portfolio,
        sample_holdings: list[Holding],
        disable_cache,
    ):
        """Test partial update of a holding (only quantity)."""
        holding_id = sample_holdings[0].id
        update_data = {"quantity": 75.0}

        response = client.put(
            f"/v1/portfolio/{sample_portfolio.id}/holdings/{holding_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["quantity"] == 75.0
        assert data["data"]["avg_cost_basis"] == 150.0  # Unchanged

    def test_update_holding_not_found(
        self, client: TestClient, sample_portfolio: Portfolio, disable_cache
    ):
        """Test updating a non-existent holding."""
        fake_holding_id = uuid4()
        update_data = {"quantity": 100.0}

        response = client.put(
            f"/v1/portfolio/{sample_portfolio.id}/holdings/{fake_holding_id}",
            json=update_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestDeleteHoldingIntegration:
    """Integration tests for DELETE /v1/portfolio/{id}/holdings/{hid}."""

    def test_delete_holding_success(
        self,
        client: TestClient,
        db_session: Session,
        sample_portfolio: Portfolio,
        sample_holdings: list[Holding],
        disable_cache,
    ):
        """Test deleting an existing holding."""
        holding_id = sample_holdings[0].id

        response = client.delete(f"/v1/portfolio/{sample_portfolio.id}/holdings/{holding_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted"] is True

        # Verify holding is deleted from database
        deleted_holding = db_session.query(Holding).filter_by(id=holding_id).first()
        assert deleted_holding is None

    def test_delete_holding_not_found(
        self, client: TestClient, sample_portfolio: Portfolio, disable_cache
    ):
        """Test deleting a non-existent holding."""
        fake_holding_id = uuid4()

        response = client.delete(f"/v1/portfolio/{sample_portfolio.id}/holdings/{fake_holding_id}")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_delete_holding_portfolio_not_found(self, client: TestClient, disable_cache):
        """Test deleting a holding from a non-existent portfolio."""
        fake_portfolio_id = uuid4()
        fake_holding_id = uuid4()

        response = client.delete(f"/v1/portfolio/{fake_portfolio_id}/holdings/{fake_holding_id}")

        assert response.status_code == 404


class TestGetPerformanceIntegration:
    """Integration tests for GET /v1/portfolio/{id}/performance."""

    def test_get_performance_success(
        self,
        client: TestClient,
        sample_portfolio: Portfolio,
        sample_holdings: list[Holding],
        disable_cache,
    ):
        """Test retrieving performance metrics for a portfolio."""
        response = client.get(f"/v1/portfolio/{sample_portfolio.id}/performance")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert data["metadata"]["portfolio_id"] == str(sample_portfolio.id)

    def test_get_performance_with_date_range(
        self,
        client: TestClient,
        sample_portfolio: Portfolio,
        sample_holdings: list[Holding],
        disable_cache,
    ):
        """Test retrieving performance with date range filter."""
        response = client.get(
            f"/v1/portfolio/{sample_portfolio.id}/performance" f"?from=2026-04-01&to=2026-04-05"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["from"] == "2026-04-01"
        assert data["metadata"]["to"] == "2026-04-05"

    def test_get_performance_portfolio_not_found(self, client: TestClient, disable_cache):
        """Test retrieving performance for a non-existent portfolio."""
        fake_id = uuid4()
        response = client.get(f"/v1/portfolio/{fake_id}/performance")

        assert response.status_code == 404


class TestGetAllocationIntegration:
    """Integration tests for GET /v1/portfolio/{id}/allocation."""

    def test_get_allocation_success(
        self,
        client: TestClient,
        sample_portfolio: Portfolio,
        sample_holdings: list[Holding],
        disable_cache,
    ):
        """Test retrieving allocation breakdown for a portfolio."""
        response = client.get(f"/v1/portfolio/{sample_portfolio.id}/allocation")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert data["metadata"]["portfolio_id"] == str(sample_portfolio.id)

        # Verify percentage totals to 100%
        total_percentage = sum(item["percentage"] for item in data["data"])
        assert 99.0 <= total_percentage <= 101.0  # Allow small rounding errors

    def test_get_allocation_empty_portfolio(
        self, client: TestClient, sample_portfolio: Portfolio, disable_cache
    ):
        """Test retrieving allocation for a portfolio with no holdings."""
        response = client.get(f"/v1/portfolio/{sample_portfolio.id}/allocation")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_allocation_portfolio_not_found(self, client: TestClient, disable_cache):
        """Test retrieving allocation for a non-existent portfolio."""
        fake_id = uuid4()
        response = client.get(f"/v1/portfolio/{fake_id}/allocation")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
