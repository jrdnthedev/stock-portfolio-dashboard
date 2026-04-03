from typing import Any
from unittest.mock import ANY, MagicMock, patch

from domains.market_data.models.models import PricePoint
from domains.market_data.service.pricing_adapter import PricingAdapter


def make_price_point(**kwargs: Any) -> PricePoint:
    defaults: dict[str, Any] = {
        "id": 1,
        "ticker_id": 1,
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
    )


def test_generate_mock_ohlcv_calls_publish(monkeypatch: object) -> None:
    _ = monkeypatch  # noqa: ARG002
    adapter = PricingAdapter.__new__(PricingAdapter)
    adapter.publish_price_updated = MagicMock()  # type: ignore[method-assign]
    # Bypass __init__
    days = 3
    adapter.generate_mock_ohlcv(1, "2024-01-01", days=days)
    assert adapter.publish_price_updated.call_count == days


@patch("domains.market_data.service.pricing_adapter.KafkaProducer")
def test_publish_price_updated_sends_event(mock_kafka_producer: MagicMock) -> None:
    _ = mock_kafka_producer  # noqa: ARG002
    adapter = PricingAdapter(["localhost:9092"], "topic42")
    adapter.producer.send = MagicMock()
    adapter.producer.flush = MagicMock()
    price_point = make_price_point()
    adapter.publish_price_updated(price_point)
    adapter.producer.send.assert_called_once()
    adapter.producer.flush.assert_called_once()
    args, kwargs = adapter.producer.send.call_args
    assert args[0] == "topic42"
    assert "event" in args[1]
    assert "data" in args[1]
