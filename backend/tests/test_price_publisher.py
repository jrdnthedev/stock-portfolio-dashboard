import json
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from domains.market_data.models.models import PricePoint
from domains.market_data.service.price_publisher import PricePublisher


class DummyPricingAdapter:
    """Mock pricing adapter that captures published messages."""

    instances: list["DummyPricingAdapter"] = []

    def __init__(self, kafka_bootstrap_servers: object = None, topic: object = None) -> None:
        _ = kafka_bootstrap_servers, topic
        self.called: list[tuple[int, str, int]] = []
        self.published_messages: list[dict[str, Any]] = []
        self.producer = MagicMock()
        self.topic = topic or "test.topic"
        DummyPricingAdapter.instances.append(self)

    def generate_mock_ohlcv(self, ticker_id: int, start_date: str, days: int = 1) -> None:
        self.called.append((ticker_id, start_date, days))

    def publish_price_updated(self, price_point: PricePoint) -> None:
        """Capture published messages for verification."""
        event = {"event": "PriceUpdated", "data": price_point.model_dump()}
        self.published_messages.append(event)

    def close(self) -> None:
        """Mock close method for cleanup."""
        pass


@patch("domains.market_data.service.price_publisher.PricingAdapter", DummyPricingAdapter)
def test_price_publisher_starts_and_stops() -> None:
    DummyPricingAdapter.instances.clear()
    publisher = PricePublisher(["localhost:9092"], interval_sec=0.1)
    ticker_ids = [1, 2]
    start_date = "2024-01-01"
    publisher.start(ticker_ids, start_date)
    time.sleep(0.25)  # Let it run a couple of intervals
    publisher.stop()
    # Check that generate_mock_ohlcv was called for each ticker at least once
    assert DummyPricingAdapter.instances, "No DummyPricingAdapter instance created"
    calls = DummyPricingAdapter.instances[0].called
    assert any(call[0] == 1 for call in calls)
    assert any(call[0] == 2 for call in calls)
    # Ensure the thread is stopped
    assert publisher._thread is None


@patch("domains.market_data.service.price_publisher.PricingAdapter", DummyPricingAdapter)
def test_price_publisher_multiple_starts_and_stops() -> None:
    DummyPricingAdapter.instances.clear()
    publisher = PricePublisher(["localhost:9092"], interval_sec=0.05)
    ticker_ids = [1]
    start_date = "2024-01-01"
    for _ in range(2):
        publisher.start(ticker_ids, start_date)
        time.sleep(0.12)
        publisher.stop()
        assert publisher._thread is None


# Tests for message format validation
class TestPricePublisherMessageFormat:
    """Test suite for verifying correct message format from PricePublisher."""

    @pytest.fixture
    def captured_messages(self) -> list[dict[str, Any]]:
        """List to capture published messages."""
        return []

    @pytest.fixture
    def mock_producer(self, captured_messages: list[dict[str, Any]]) -> MagicMock:
        """Create a mock Kafka producer that captures messages."""
        producer = MagicMock()

        def capture_send(topic: str, value: dict[str, Any]) -> None:
            _ = topic
            captured_messages.append(value)

        producer.send = MagicMock(side_effect=capture_send)
        producer.flush = MagicMock()
        return producer

    @pytest.fixture
    def pricing_adapter(self, mock_producer: MagicMock) -> Any:
        """Create a pricing adapter with mocked producer."""
        with patch(
            "domains.market_data.service.pricing_adapter.KafkaProducer", return_value=mock_producer
        ):
            from domains.market_data.service.pricing_adapter import PricingAdapter

            return PricingAdapter(["localhost:9092"], "test.topic")

    def test_published_message_has_correct_structure(
        self, pricing_adapter: Any, captured_messages: list[dict[str, Any]]
    ) -> None:
        """Test that published messages have the correct event structure."""
        # Generate mock OHLCV data
        pricing_adapter.generate_mock_ohlcv(ticker_id=123, start_date="2024-01-15", days=1)

        # Verify at least one message was published
        assert len(captured_messages) >= 1

        # Check message structure
        message = captured_messages[0]
        assert "event" in message
        assert "data" in message
        assert message["event"] == "PriceUpdated"

    def test_published_message_data_contains_required_fields(
        self, pricing_adapter: Any, captured_messages: list[dict[str, Any]]
    ) -> None:
        """Test that the data field contains all required OHLCV fields."""
        pricing_adapter.generate_mock_ohlcv(ticker_id=456, start_date="2024-02-01", days=1)

        message = captured_messages[0]
        data = message["data"]

        # Verify all required fields are present
        required_fields = ["id", "ticker_id", "date", "open", "high", "low", "close", "volume"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_published_message_data_types(
        self, pricing_adapter: Any, captured_messages: list[dict[str, Any]]
    ) -> None:
        """Test that published message fields have correct data types."""
        pricing_adapter.generate_mock_ohlcv(ticker_id=789, start_date="2024-03-10", days=1)

        message = captured_messages[0]
        data = message["data"]

        # Verify data types
        assert isinstance(data["id"], int), "id should be an integer"
        assert isinstance(data["ticker_id"], int), "ticker_id should be an integer"
        assert isinstance(data["date"], str), "date should be a string"
        assert isinstance(data["open"], int | float), "open should be a number"
        assert isinstance(data["high"], int | float), "high should be a number"
        assert isinstance(data["low"], int | float), "low should be a number"
        assert isinstance(data["close"], int | float), "close should be a number"
        assert isinstance(data["volume"], int), "volume should be an integer"

    def test_published_message_ticker_id_matches(
        self, pricing_adapter: Any, captured_messages: list[dict[str, Any]]
    ) -> None:
        """Test that the ticker_id in the message matches the requested ticker."""
        ticker_id = 999
        pricing_adapter.generate_mock_ohlcv(ticker_id=ticker_id, start_date="2024-04-01", days=1)

        message = captured_messages[0]
        assert message["data"]["ticker_id"] == ticker_id

    def test_published_message_date_format(
        self, pricing_adapter: Any, captured_messages: list[dict[str, Any]]
    ) -> None:
        """Test that the date field is in the correct format (YYYY-MM-DD)."""
        start_date = "2024-05-15"
        pricing_adapter.generate_mock_ohlcv(ticker_id=111, start_date=start_date, days=1)

        message = captured_messages[0]
        date_str = message["data"]["date"]

        # Verify date format
        assert len(date_str) == 10, "Date should be in YYYY-MM-DD format"
        assert date_str.count("-") == 2, "Date should have two hyphens"
        assert date_str == start_date, "Date should match the start_date"

    def test_published_message_ohlcv_relationships(
        self, pricing_adapter: Any, captured_messages: list[dict[str, Any]]
    ) -> None:
        """Test that OHLCV values follow expected relationships (high >= low, etc.)."""
        pricing_adapter.generate_mock_ohlcv(ticker_id=222, start_date="2024-06-01", days=5)

        for message in captured_messages:
            data = message["data"]
            high = data["high"]
            low = data["low"]
            open_price = data["open"]
            close_price = data["close"]

            # Verify OHLCV relationships
            assert high >= low, f"High ({high}) should be >= Low ({low})"
            assert high >= open_price, f"High ({high}) should be >= Open ({open_price})"
            assert high >= close_price, f"High ({high}) should be >= Close ({close_price})"
            assert low <= open_price, f"Low ({low}) should be <= Open ({open_price})"
            assert low <= close_price, f"Low ({low}) should be <= Close ({close_price})"

    def test_published_message_volume_positive(
        self, pricing_adapter: Any, captured_messages: list[dict[str, Any]]
    ) -> None:
        """Test that volume is always positive."""
        pricing_adapter.generate_mock_ohlcv(ticker_id=333, start_date="2024-07-01", days=3)

        for message in captured_messages:
            data = message["data"]
            assert data["volume"] > 0, "Volume should be positive"

    def test_published_message_serializable_as_json(
        self, pricing_adapter: Any, captured_messages: list[dict[str, Any]]
    ) -> None:
        """Test that published messages can be serialized to JSON."""
        pricing_adapter.generate_mock_ohlcv(ticker_id=444, start_date="2024-08-01", days=1)

        message = captured_messages[0]

        # Should not raise an exception
        json_str = json.dumps(message)
        assert len(json_str) > 0

        # Should be deserializable back
        deserialized = json.loads(json_str)
        assert deserialized["event"] == "PriceUpdated"
        assert "data" in deserialized

    def test_multiple_days_generates_multiple_messages(
        self, pricing_adapter: Any, captured_messages: list[dict[str, Any]]
    ) -> None:
        """Test that generating multiple days produces separate messages."""
        days = 5
        pricing_adapter.generate_mock_ohlcv(ticker_id=555, start_date="2024-09-01", days=days)

        assert len(captured_messages) == days, f"Should generate {days} messages"

        # Verify dates are sequential
        dates = [msg["data"]["date"] for msg in captured_messages]
        assert len(set(dates)) == days, "All dates should be unique"

    def test_price_publisher_integration_with_adapter(self) -> None:
        """Integration test: PricePublisher correctly uses PricingAdapter."""
        DummyPricingAdapter.instances.clear()

        with patch(
            "domains.market_data.service.price_publisher.PricingAdapter", DummyPricingAdapter
        ):
            publisher = PricePublisher(["localhost:9092"], interval_sec=0.1)
            publisher.start([1, 2, 3], "2024-10-01")
            time.sleep(0.25)
            publisher.stop()

            # Verify adapter was created and used
            assert len(DummyPricingAdapter.instances) > 0
            adapter = DummyPricingAdapter.instances[0]
            assert len(adapter.called) > 0

            # Verify all tickers were processed
            ticker_ids_called = {call[0] for call in adapter.called}
            assert 1 in ticker_ids_called
            assert 2 in ticker_ids_called
            assert 3 in ticker_ids_called
