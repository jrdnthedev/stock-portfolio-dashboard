import time
from unittest.mock import patch

from domains.market_data.service.price_publisher import PricePublisher


class DummyPricingAdapter:
    instances: list["DummyPricingAdapter"] = []

    def __init__(self, kafka_bootstrap_servers: object = None, topic: object = None) -> None:
        _ = kafka_bootstrap_servers, topic
        self.called: list[tuple[int, str, int]] = []
        DummyPricingAdapter.instances.append(self)

    def generate_mock_ohlcv(self, ticker_id: int, start_date: str, days: int = 1) -> None:
        self.called.append((ticker_id, start_date, days))


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
