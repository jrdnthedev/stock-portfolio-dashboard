from typing import Any
from unittest.mock import ANY, MagicMock, patch
from uuid import uuid4

from kafka.errors import NoBrokersAvailable

from domains.market_data.models.models import PricePoint
from domains.market_data.service.pricing_adapter import PricingAdapter


def make_price_point(**kwargs: Any) -> PricePoint:
    defaults: dict[str, Any] = {
        "id": 1,
        "ticker_id": uuid4(),
        "date": "2024-01-01",
        "open": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": 105.0,
        "volume": 1000,
    }
    defaults.update(kwargs)
    return PricePoint(**defaults)


@patch("domains.market_data.service.pricing_adapter.KafkaProducer")
def test_init_sets_topic_and_producer(mock_kafka_producer: MagicMock) -> None:
    instance = mock_kafka_producer.return_value
    adapter = PricingAdapter(["localhost:9092"], "topic1")
    assert adapter.topic == "topic1"
    assert adapter.producer == instance
    mock_kafka_producer.assert_called_once_with(
        bootstrap_servers=["localhost:9092"],
        value_serializer=ANY,
        request_timeout_ms=10000,
        max_block_ms=10000,
    )


def test_generate_mock_ohlcv_calls_publish(monkeypatch: object) -> None:
    _ = monkeypatch  # noqa: ARG002
    from uuid import uuid4

    adapter = PricingAdapter.__new__(PricingAdapter)
    adapter.publish_price_updated = MagicMock()  # type: ignore[method-assign]
    # Bypass __init__
    days = 3
    ticker_id = uuid4()
    adapter.generate_mock_ohlcv(ticker_id, "2024-01-01", days=days)
    assert adapter.publish_price_updated.call_count == days


@patch("domains.market_data.service.pricing_adapter.KafkaProducer")
def test_publish_price_updated_sends_event(mock_kafka_producer: MagicMock) -> None:
    _ = mock_kafka_producer  # noqa: ARG002
    adapter = PricingAdapter(["localhost:9092"], "topic42")
    # Mock the future returned by send
    mock_future = MagicMock()
    mock_future.get = MagicMock(return_value=None)
    adapter.producer.send = MagicMock(return_value=mock_future)
    price_point = make_price_point()
    adapter.publish_price_updated(price_point)
    adapter.producer.send.assert_called_once()
    mock_future.get.assert_called_once_with(timeout=10)
    args, kwargs = adapter.producer.send.call_args
    assert args[0] == "topic42"
    assert "event" in args[1]
    assert "data" in args[1]


@patch("domains.market_data.service.pricing_adapter.KafkaProducer")
def test_close_flushes_and_closes_producer(mock_kafka_producer: MagicMock) -> None:
    _ = mock_kafka_producer  # noqa: ARG002
    adapter = PricingAdapter(["localhost:9092"], "topic1")
    adapter.producer.flush = MagicMock()
    adapter.producer.close = MagicMock()
    adapter.close()
    adapter.producer.flush.assert_called_once_with(timeout=5)
    adapter.producer.close.assert_called_once_with(timeout=5)


@patch("domains.market_data.service.pricing_adapter.time.sleep")
@patch("domains.market_data.service.pricing_adapter.KafkaProducer")
def test_retry_logic_on_kafka_unavailable(
    mock_kafka_producer: MagicMock, mock_sleep: MagicMock
) -> None:
    """Test that PricingAdapter retries connection with exponential backoff."""
    # Simulate failure on first 2 attempts, success on 3rd
    mock_kafka_producer.side_effect = [
        NoBrokersAvailable("No brokers"),
        NoBrokersAvailable("No brokers"),
        MagicMock(),  # Success on 3rd attempt
    ]
    adapter = PricingAdapter(["localhost:9092"], "topic1", max_retries=5)
    # Should have called KafkaProducer 3 times
    assert mock_kafka_producer.call_count == 3
    # Should have slept twice with exponential backoff: 2^1=2, 2^2=4
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(2)
    mock_sleep.assert_any_call(4)
    assert adapter.producer is not None


@patch("domains.market_data.service.pricing_adapter.time.sleep")
@patch("domains.market_data.service.pricing_adapter.KafkaProducer")
def test_retry_logic_fails_after_max_retries(
    mock_kafka_producer: MagicMock, mock_sleep: MagicMock
) -> None:
    """Test that PricingAdapter raises KafkaConnectionError after max retries."""
    from backend.common.exceptions import KafkaConnectionError

    # Always fail
    mock_kafka_producer.side_effect = NoBrokersAvailable("No brokers")
    try:
        PricingAdapter(["localhost:9092"], "topic1", max_retries=3)
        raise AssertionError("Expected KafkaConnectionError to be raised")
    except KafkaConnectionError as e:
        # Verify exception details
        assert "No brokers" in str(e)
        # Should have tried 3 times
        assert mock_kafka_producer.call_count == 3
        # Should have slept 2 times (no sleep after last failure)
        assert mock_sleep.call_count == 2
