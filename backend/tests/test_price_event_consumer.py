import time
from typing import Any, cast
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

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
    def portfolio_service(self) -> PortfolioService:
        with patch("domains.portfolio.services.portfolio_service.KafkaProducer"):
            return PortfolioService(["localhost:9092"])

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
            portfolio_service, performance_calculator, price_consumer, websocket_publisher
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
