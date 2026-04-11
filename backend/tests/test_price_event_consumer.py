import time
from typing import Any, cast
from unittest.mock import MagicMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from domains.portfolio.models.models import Holding, Portfolio
from domains.portfolio.repositories.portfolio_repository import (
    HoldingRepository,
    PortfolioRepository,
)
from domains.portfolio.services.performance_calculator import PerformanceCalculator
from domains.portfolio.services.portfolio_service import PortfolioService
from domains.portfolio.services.price_event_consumer import (
    PortfolioPerformanceOrchestrator,
    PriceEventConsumer,
)


class DummyKafkaConsumer:
    """Mock Kafka consumer for testing."""

    def __init__(
        self,
        *topics: str,
        bootstrap_servers: list[str] | None = None,
        group_id: str | None = None,
        value_deserializer: object = None,
        auto_offset_reset: str | None = None,
        enable_auto_commit: bool = True,
    ) -> None:
        _ = topics, bootstrap_servers, group_id, value_deserializer
        _ = auto_offset_reset, enable_auto_commit
        self.messages: list[Any] = []
        self._index = 0
        self.closed = False

    def __iter__(self) -> "DummyKafkaConsumer":
        return self

    def __next__(self) -> Any:
        if self._index >= len(self.messages):
            time.sleep(0.01)  # Prevent tight loop
            raise StopIteration
        msg = MagicMock()
        msg.value = self.messages[self._index]
        self._index += 1
        return msg

    def add_message(self, value: Any) -> None:
        """Add a message to be consumed."""
        self.messages.append(value)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def mock_kafka_consumer() -> DummyKafkaConsumer:
    return DummyKafkaConsumer()


@pytest.fixture
def consumer(mock_kafka_consumer: DummyKafkaConsumer) -> PriceEventConsumer:
    with patch(
        "domains.portfolio.services.price_event_consumer.KafkaConsumer",
        return_value=mock_kafka_consumer,
    ):
        return PriceEventConsumer(["localhost:9092"], "test.topic")


@pytest.fixture
def mock_portfolio_repo() -> Mock:
    """Mock PortfolioRepository with in-memory storage."""
    repo = Mock(spec=PortfolioRepository)
    storage: dict[UUID, Portfolio] = {}

    def create(portfolio: Portfolio) -> Portfolio:
        storage[portfolio.id] = portfolio
        return portfolio

    def get_by_id(portfolio_id: UUID) -> Portfolio | None:
        return storage.get(portfolio_id)

    def list_by_owner(owner: str) -> list[Portfolio]:
        return [p for p in storage.values() if p.owner == owner]

    def list_all() -> list[Portfolio]:
        return list(storage.values())

    def update(portfolio: Portfolio) -> Portfolio:
        if portfolio.id not in storage:
            raise ValueError(f"Portfolio {portfolio.id} not found")
        storage[portfolio.id] = portfolio
        return portfolio

    def delete(portfolio_id: UUID) -> bool:
        if portfolio_id in storage:
            del storage[portfolio_id]
            return True
        return False

    repo.create.side_effect = create
    repo.get_by_id.side_effect = get_by_id
    repo.list_by_owner.side_effect = list_by_owner
    repo.list_all.side_effect = list_all
    repo.update.side_effect = update
    repo.delete.side_effect = delete
    return repo


@pytest.fixture
def mock_holding_repo() -> Mock:
    """Mock HoldingRepository with in-memory storage."""
    repo = Mock(spec=HoldingRepository)
    storage: dict[UUID, Holding] = {}

    def create(holding: Holding) -> Holding:
        storage[holding.id] = holding
        return holding

    def get_by_id(holding_id: UUID) -> Holding | None:
        return storage.get(holding_id)

    def list_by_portfolio(portfolio_id: UUID) -> list[Holding]:
        return [h for h in storage.values() if h.portfolio_id == portfolio_id]

    def list_by_ticker(ticker_id: UUID) -> list[Holding]:
        return [h for h in storage.values() if h.ticker_id == ticker_id]

    def update(holding: Holding) -> Holding:
        if holding.id not in storage:
            raise ValueError(f"Holding {holding.id} not found")
        storage[holding.id] = holding
        return holding

    def delete(holding_id: UUID) -> bool:
        if holding_id in storage:
            del storage[holding_id]
            return True
        return False

    def delete_by_portfolio(portfolio_id: UUID) -> int:
        to_delete = [h_id for h_id, h in storage.items() if h.portfolio_id == portfolio_id]
        for h_id in to_delete:
            del storage[h_id]
        return len(to_delete)

    repo.create.side_effect = create
    repo.get_by_id.side_effect = get_by_id
    repo.list_by_portfolio.side_effect = list_by_portfolio
    repo.list_by_ticker.side_effect = list_by_ticker
    repo.update.side_effect = update
    repo.delete.side_effect = delete
    repo.delete_by_portfolio.side_effect = delete_by_portfolio
    return repo


class TestPriceEventConsumerInit:
    def test_init_creates_consumer(self, consumer: PriceEventConsumer) -> None:
        assert consumer.topic == "test.topic"
        assert consumer.consumer is not None

    def test_init_with_custom_group_id(self) -> None:
        mock = DummyKafkaConsumer()
        with patch(
            "domains.portfolio.services.price_event_consumer.KafkaConsumer", return_value=mock
        ):
            consumer = PriceEventConsumer(["localhost:9092"], "test.topic", group_id="custom-group")
            assert consumer.consumer == mock


class TestPriceEventConsumerCallback:
    def test_set_callback(self, consumer: PriceEventConsumer) -> None:
        called = []

        def callback(data: dict[str, Any]) -> None:
            called.append(data)

        consumer.set_callback(callback)
        assert consumer._on_price_update_callback == callback

    def test_callback_invoked_on_price_update(
        self, consumer: PriceEventConsumer, mock_kafka_consumer: DummyKafkaConsumer
    ) -> None:
        called: list[dict[str, Any]] = []

        def callback(data: dict[str, Any]) -> None:
            called.append(data)

        consumer.set_callback(callback)

        # Add a PriceUpdated event
        mock_kafka_consumer.add_message(
            {
                "event": "PriceUpdated",
                "data": {"ticker_id": 123, "date": "2024-01-15", "close": 100.0},
            }
        )

        consumer.start()
        time.sleep(0.05)
        consumer.stop()

        assert len(called) == 1
        assert called[0]["ticker_id"] == 123
        assert called[0]["close"] == 100.0


class TestPriceEventConsumerLifecycle:
    def test_start_and_stop(
        self, consumer: PriceEventConsumer, mock_kafka_consumer: DummyKafkaConsumer
    ) -> None:
        consumer.start()
        assert consumer._thread is not None
        assert consumer._thread.is_alive()

        consumer.stop()
        assert mock_kafka_consumer.closed

    def test_handles_invalid_events(
        self, consumer: PriceEventConsumer, mock_kafka_consumer: DummyKafkaConsumer
    ) -> None:
        called: list[dict[str, Any]] = []

        def callback(data: dict[str, Any]) -> None:
            called.append(data)

        consumer.set_callback(callback)

        # Add invalid events
        mock_kafka_consumer.add_message({"event": "OtherEvent"})
        mock_kafka_consumer.add_message({"event": "PriceUpdated"})  # Missing data
        mock_kafka_consumer.add_message("invalid")  # Not a dict

        consumer.start()
        time.sleep(0.05)
        consumer.stop()

        # Should not call callback for invalid events
        assert len(called) == 0


class TestPortfolioPerformanceOrchestrator:
    @pytest.fixture
    def portfolio_service(
        self, mock_portfolio_repo: Mock, mock_holding_repo: Mock
    ) -> PortfolioService:
        with patch("domains.portfolio.services.portfolio_service.KafkaProducer"):
            return PortfolioService(
                portfolio_repo=mock_portfolio_repo,
                holding_repo=mock_holding_repo,
                kafka_bootstrap_servers=["localhost:9092"],
            )

    @pytest.fixture
    def performance_calculator(self) -> PerformanceCalculator:
        return PerformanceCalculator()

    @pytest.fixture
    def price_consumer(self) -> PriceEventConsumer:
        mock = DummyKafkaConsumer()
        with patch(
            "domains.portfolio.services.price_event_consumer.KafkaConsumer", return_value=mock
        ):
            return PriceEventConsumer(["localhost:9092"])

    @pytest.fixture
    def websocket_publisher(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def orchestrator(
        self,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
        price_consumer: PriceEventConsumer,
        websocket_publisher: MagicMock,
    ) -> PortfolioPerformanceOrchestrator:
        return PortfolioPerformanceOrchestrator(
            portfolio_service,
            performance_calculator,
            price_consumer,
            alert_publisher=None,
            websocket_publisher=websocket_publisher,
        )

    def test_init_registers_callback(self, orchestrator: PortfolioPerformanceOrchestrator) -> None:
        assert orchestrator.price_consumer._on_price_update_callback is not None

    def test_start_and_stop(self, orchestrator: PortfolioPerformanceOrchestrator) -> None:
        orchestrator.start()
        orchestrator.stop()
        assert cast(DummyKafkaConsumer, orchestrator.price_consumer.consumer).closed

    def test_price_update_triggers_recomputation(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
        websocket_publisher: MagicMock,
    ) -> None:
        # Create portfolio with holding
        portfolio = portfolio_service.create_portfolio("Test", "user1")
        ticker_id = uuid4()
        portfolio_service.create_holding(portfolio.id, ticker_id, 100.0, 50.0)
        performance_calculator.set_ticker_sector(ticker_id, "Technology")

        # Simulate price update
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": 75.0})

        # Verify price was updated
        assert performance_calculator.current_prices[ticker_id] == 75.0

        # Verify WebSocket publish was called
        websocket_publisher.assert_called_once()
        args = websocket_publisher.call_args[0]
        assert args[0] == str(portfolio.id)
        assert args[1]["event"] == "PortfolioPerformanceUpdated"

    def test_price_update_only_affects_relevant_portfolios(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
        websocket_publisher: MagicMock,
    ) -> None:
        # Create two portfolios
        p1 = portfolio_service.create_portfolio("Portfolio 1", "user1")
        p2 = portfolio_service.create_portfolio("Portfolio 2", "user1")

        ticker1 = uuid4()
        ticker2 = uuid4()

        # Portfolio 1 holds ticker1
        portfolio_service.create_holding(p1.id, ticker1, 100.0, 50.0)
        # Portfolio 2 holds ticker2
        portfolio_service.create_holding(p2.id, ticker2, 100.0, 50.0)

        performance_calculator.set_ticker_sector(ticker1, "Technology")

        # Update price for ticker1
        orchestrator._on_price_updated({"ticker_id": ticker1, "close": 75.0})

        # Only portfolio 1 should be recomputed
        websocket_publisher.assert_called_once()
        args = websocket_publisher.call_args[0]
        assert args[0] == str(p1.id)

    def test_price_update_with_multiple_holdings(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
        websocket_publisher: MagicMock,
    ) -> None:
        # Create portfolio with multiple holdings
        portfolio = portfolio_service.create_portfolio("Test", "user1")
        ticker1 = uuid4()
        ticker2 = uuid4()

        portfolio_service.create_holding(portfolio.id, ticker1, 100.0, 50.0)
        portfolio_service.create_holding(portfolio.id, ticker2, 200.0, 75.0)

        performance_calculator.set_ticker_sector(ticker1, "Technology")
        performance_calculator.set_ticker_sector(ticker2, "Healthcare")

        # Set initial prices
        performance_calculator.update_price(ticker1, 60.0)
        performance_calculator.update_price(ticker2, 80.0)

        # Update ticker1 price
        orchestrator._on_price_updated({"ticker_id": ticker1, "close": 70.0})

        # Verify performance includes both holdings
        args = websocket_publisher.call_args[0]
        performance_data = args[1]["data"]
        assert len(performance_data["holdings"]) == 2

    def test_price_update_handles_missing_data(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        websocket_publisher: MagicMock,
    ) -> None:
        # Missing ticker_id
        orchestrator._on_price_updated({"close": 75.0})
        websocket_publisher.assert_not_called()

        # Missing close price
        orchestrator._on_price_updated({"ticker_id": uuid4()})
        websocket_publisher.assert_not_called()

    def test_price_update_without_websocket_publisher(
        self,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
        price_consumer: PriceEventConsumer,
    ) -> None:
        # Create orchestrator without websocket publisher
        orchestrator = PortfolioPerformanceOrchestrator(
            portfolio_service, performance_calculator, price_consumer, None
        )

        portfolio = portfolio_service.create_portfolio("Test", "user1")
        ticker_id = uuid4()
        portfolio_service.create_holding(portfolio.id, ticker_id, 100.0, 50.0)

        # Should not raise exception
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": 75.0})

    def test_orchestrator_with_no_holdings_for_ticker(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        websocket_publisher: MagicMock,
    ) -> None:
        # Update price for ticker that no portfolio holds
        orchestrator._on_price_updated({"ticker_id": uuid4(), "close": 75.0})

        # Should not call WebSocket publisher
        websocket_publisher.assert_not_called()


class TestPriceEventConsumerPnLRecalculation:
    """Test suite for verifying correct P&L recalculation logic."""

    @pytest.fixture
    def portfolio_service(
        self, mock_portfolio_repo: Mock, mock_holding_repo: Mock
    ) -> PortfolioService:
        with patch("domains.portfolio.services.portfolio_service.KafkaProducer"):
            return PortfolioService(
                portfolio_repo=mock_portfolio_repo,
                holding_repo=mock_holding_repo,
                kafka_bootstrap_servers=["localhost:9092"],
            )

    @pytest.fixture
    def performance_calculator(self) -> PerformanceCalculator:
        return PerformanceCalculator()

    @pytest.fixture
    def price_consumer(self) -> PriceEventConsumer:
        mock = DummyKafkaConsumer()
        with patch(
            "domains.portfolio.services.price_event_consumer.KafkaConsumer", return_value=mock
        ):
            return PriceEventConsumer(["localhost:9092"])

    @pytest.fixture
    def orchestrator(
        self,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
        price_consumer: PriceEventConsumer,
    ) -> PortfolioPerformanceOrchestrator:
        websocket_publisher = MagicMock()
        return PortfolioPerformanceOrchestrator(
            portfolio_service,
            performance_calculator,
            price_consumer,
            alert_publisher=None,
            websocket_publisher=websocket_publisher,
        )

    def test_pnl_calculation_with_price_increase(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
    ) -> None:
        """Test P&L calculation when price increases."""
        # Setup: Portfolio with 100 shares bought at $50
        portfolio = portfolio_service.create_portfolio("Test Portfolio", "user1")
        ticker_id = uuid4()
        quantity = 100.0
        avg_cost = 50.0
        portfolio_service.create_holding(portfolio.id, ticker_id, quantity, avg_cost)
        performance_calculator.set_ticker_sector(ticker_id, "Technology")

        # Initial price: $60 (gain of $10 per share)
        performance_calculator.update_price(ticker_id, 60.0)

        # Trigger recalculation via price update to $75
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": 75.0})

        # Verify P&L calculation
        # Cost basis: 100 * 50 = $5,000
        # Market value: 100 * 75 = $7,500
        # Unrealized P&L: $2,500
        # P&L %: (2500 / 5000) * 100 = 50%

        performance = performance_calculator.calculate_portfolio_performance(
            portfolio.id, [(ticker_id, quantity, avg_cost)]
        )
        assert performance is not None
        assert performance.total_cost_basis == 5000.0
        assert performance.total_market_value == 7500.0
        assert performance.total_unrealized_pnl == 2500.0
        assert abs(performance.total_unrealized_pnl_pct - 50.0) < 0.01

    def test_pnl_calculation_with_price_decrease(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
    ) -> None:
        """Test P&L calculation when price decreases (loss scenario)."""
        # Setup: Portfolio with 200 shares bought at $100
        portfolio = portfolio_service.create_portfolio("Loss Portfolio", "user1")
        ticker_id = uuid4()
        quantity = 200.0
        avg_cost = 100.0
        portfolio_service.create_holding(portfolio.id, ticker_id, quantity, avg_cost)
        performance_calculator.set_ticker_sector(ticker_id, "Healthcare")

        # Price drops to $80
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": 80.0})

        # Verify P&L calculation
        # Cost basis: 200 * 100 = $20,000
        # Market value: 200 * 80 = $16,000
        # Unrealized P&L: -$4,000 (loss)
        # P&L %: (-4000 / 20000) * 100 = -20%

        performance = performance_calculator.calculate_portfolio_performance(
            portfolio.id, [(ticker_id, quantity, avg_cost)]
        )
        assert performance is not None
        assert performance.total_cost_basis == 20000.0
        assert performance.total_market_value == 16000.0
        assert performance.total_unrealized_pnl == -4000.0
        assert abs(performance.total_unrealized_pnl_pct - (-20.0)) < 0.01

    def test_pnl_calculation_multiple_price_updates(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
    ) -> None:
        """Test P&L recalculation with multiple sequential price updates."""
        # Setup
        portfolio = portfolio_service.create_portfolio("Dynamic Portfolio", "user1")
        ticker_id = uuid4()
        quantity = 50.0
        avg_cost = 100.0
        portfolio_service.create_holding(portfolio.id, ticker_id, quantity, avg_cost)
        performance_calculator.set_ticker_sector(ticker_id, "Technology")

        # First update: price increases to $120
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": 120.0})
        perf1 = performance_calculator.calculate_portfolio_performance(
            portfolio.id, [(ticker_id, quantity, avg_cost)]
        )
        assert perf1 is not None
        assert perf1.total_unrealized_pnl == 1000.0  # (120-100)*50

        # Second update: price increases to $150
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": 150.0})
        perf2 = performance_calculator.calculate_portfolio_performance(
            portfolio.id, [(ticker_id, quantity, avg_cost)]
        )
        assert perf2 is not None
        assert perf2.total_unrealized_pnl == 2500.0  # (150-100)*50

        # Third update: price decreases to $90
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": 90.0})
        perf3 = performance_calculator.calculate_portfolio_performance(
            portfolio.id, [(ticker_id, quantity, avg_cost)]
        )
        assert perf3 is not None
        assert perf3.total_unrealized_pnl == -500.0  # (90-100)*50

    def test_pnl_calculation_multiple_holdings(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
    ) -> None:
        """Test P&L calculation for portfolio with multiple holdings."""
        portfolio = portfolio_service.create_portfolio("Diversified Portfolio", "user1")

        # Holding 1: 100 shares @ $50
        ticker1 = uuid4()
        portfolio_service.create_holding(portfolio.id, ticker1, 100.0, 50.0)
        performance_calculator.set_ticker_sector(ticker1, "Technology")

        # Holding 2: 200 shares @ $75
        ticker2 = uuid4()
        portfolio_service.create_holding(portfolio.id, ticker2, 200.0, 75.0)
        performance_calculator.set_ticker_sector(ticker2, "Healthcare")

        # Holding 3: 50 shares @ $200
        ticker3 = uuid4()
        portfolio_service.create_holding(portfolio.id, ticker3, 50.0, 200.0)
        performance_calculator.set_ticker_sector(ticker3, "Finance")

        # Update all prices
        performance_calculator.update_price(ticker1, 60.0)  # +$10/share = +$1000
        performance_calculator.update_price(ticker2, 80.0)  # +$5/share = +$1000
        performance_calculator.update_price(ticker3, 190.0)  # -$10/share = -$500

        # Calculate aggregate P&L
        holdings = [
            (ticker1, 100.0, 50.0),
            (ticker2, 200.0, 75.0),
            (ticker3, 50.0, 200.0),
        ]
        performance = performance_calculator.calculate_portfolio_performance(portfolio.id, holdings)

        assert performance is not None
        # Total cost: (100*50) + (200*75) + (50*200) = 5000 + 15000 + 10000 = $30,000
        # Total value: (100*60) + (200*80) + (50*190) = 6000 + 16000 + 9500 = $31,500
        # Total P&L: $1,500
        assert performance.total_cost_basis == 30000.0
        assert performance.total_market_value == 31500.0
        assert performance.total_unrealized_pnl == 1500.0
        assert abs(performance.total_unrealized_pnl_pct - 5.0) < 0.01  # 5% gain

    def test_pnl_calculation_isolated_ticker_updates(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
    ) -> None:
        """Test that updating one ticker's price only affects its holdings."""
        # Two portfolios
        portfolio1 = portfolio_service.create_portfolio("Portfolio 1", "user1")
        portfolio2 = portfolio_service.create_portfolio("Portfolio 2", "user2")

        ticker1 = uuid4()
        ticker2 = uuid4()

        # Portfolio 1 holds ticker1
        portfolio_service.create_holding(portfolio1.id, ticker1, 100.0, 100.0)
        performance_calculator.set_ticker_sector(ticker1, "Technology")

        # Portfolio 2 holds ticker2
        portfolio_service.create_holding(portfolio2.id, ticker2, 100.0, 100.0)
        performance_calculator.set_ticker_sector(ticker2, "Healthcare")

        # Set initial prices
        performance_calculator.update_price(ticker1, 100.0)
        performance_calculator.update_price(ticker2, 100.0)

        # Update only ticker1
        orchestrator._on_price_updated({"ticker_id": ticker1, "close": 150.0})

        # Verify ticker1 price updated
        assert performance_calculator.current_prices[ticker1] == 150.0
        # Verify ticker2 price unchanged
        assert performance_calculator.current_prices[ticker2] == 100.0

        # Portfolio 1 should show gain
        perf1 = performance_calculator.calculate_portfolio_performance(
            portfolio1.id, [(ticker1, 100.0, 100.0)]
        )
        assert perf1 is not None
        assert perf1.total_unrealized_pnl == 5000.0

        # Portfolio 2 should show no gain
        perf2 = performance_calculator.calculate_portfolio_performance(
            portfolio2.id, [(ticker2, 100.0, 100.0)]
        )
        assert perf2 is not None
        assert perf2.total_unrealized_pnl == 0.0

    def test_pnl_calculation_with_fractional_shares(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
    ) -> None:
        """Test P&L calculation with fractional share quantities."""
        portfolio = portfolio_service.create_portfolio("Fractional Portfolio", "user1")
        ticker_id = uuid4()
        quantity = 10.5  # Fractional shares
        avg_cost = 100.25
        portfolio_service.create_holding(portfolio.id, ticker_id, quantity, avg_cost)
        performance_calculator.set_ticker_sector(ticker_id, "Technology")

        # Update price to $125.50
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": 125.50})

        performance = performance_calculator.calculate_portfolio_performance(
            portfolio.id, [(ticker_id, quantity, avg_cost)]
        )
        assert performance is not None

        # Cost basis: 10.5 * 100.25 = 1052.625
        # Market value: 10.5 * 125.50 = 1317.75
        # P&L: 265.125
        expected_cost = 10.5 * 100.25
        expected_value = 10.5 * 125.50
        expected_pnl = expected_value - expected_cost

        assert abs(performance.total_cost_basis - expected_cost) < 0.01
        assert abs(performance.total_market_value - expected_value) < 0.01
        assert abs(performance.total_unrealized_pnl - expected_pnl) < 0.01

    def test_pnl_breakeven_scenario(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
    ) -> None:
        """Test P&L when current price equals cost basis (breakeven)."""
        portfolio = portfolio_service.create_portfolio("Breakeven Portfolio", "user1")
        ticker_id = uuid4()
        quantity = 100.0
        avg_cost = 50.0
        portfolio_service.create_holding(portfolio.id, ticker_id, quantity, avg_cost)
        performance_calculator.set_ticker_sector(ticker_id, "Technology")

        # Price equals cost basis
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": 50.0})

        performance = performance_calculator.calculate_portfolio_performance(
            portfolio.id, [(ticker_id, quantity, avg_cost)]
        )
        assert performance is not None
        assert performance.total_unrealized_pnl == 0.0
        assert performance.total_unrealized_pnl_pct == 0.0

    def test_pnl_calculation_verifies_websocket_data(
        self,
        orchestrator: PortfolioPerformanceOrchestrator,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
    ) -> None:
        """Test that WebSocket messages contain accurate P&L data."""
        portfolio = portfolio_service.create_portfolio("WebSocket Portfolio", "user1")
        ticker_id = uuid4()
        quantity = 75.0
        avg_cost = 80.0
        portfolio_service.create_holding(portfolio.id, ticker_id, quantity, avg_cost)
        performance_calculator.set_ticker_sector(ticker_id, "Technology")

        # Update price
        new_price = 100.0
        orchestrator._on_price_updated({"ticker_id": ticker_id, "close": new_price})

        # Get WebSocket publisher from orchestrator
        ws_publisher = cast(MagicMock, orchestrator.websocket_publisher)
        assert ws_publisher is not None

        # Verify WebSocket was called
        ws_publisher.assert_called_once()
        call_args = ws_publisher.call_args[0]
        portfolio_id_str = call_args[0]
        _ = portfolio_id_str
        event_data = call_args[1]

        # Verify event structure
        assert event_data["event"] == "PortfolioPerformanceUpdated"
        assert "data" in event_data

        # Verify P&L data in WebSocket message
        perf_data = event_data["data"]
        expected_cost = quantity * avg_cost  # 75 * 80 = 6000
        expected_value = quantity * new_price  # 75 * 100 = 7500
        expected_pnl = expected_value - expected_cost  # 1500

        assert abs(perf_data["total_cost_basis"] - expected_cost) < 0.01
        assert abs(perf_data["total_market_value"] - expected_value) < 0.01
        assert abs(perf_data["total_unrealized_pnl"] - expected_pnl) < 0.01
