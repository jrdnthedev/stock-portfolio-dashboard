from unittest.mock import MagicMock, patch
from uuid import uuid4

from domains.market_data.models.models import Fundamental
from domains.market_data.service.market_data_service import MarketDataService


@patch("domains.market_data.service.market_data_service.PricingAdapter")
def test_get_fundamental_snapshot(mock_pricing_adapter: MagicMock) -> None:
    _ = mock_pricing_adapter
    service = MarketDataService(["localhost:9092"], "market.prices.live")
    ticker_id = uuid4()
    result = service.get_fundamental_snapshot(ticker_id, "Q1 2024")
    assert isinstance(result, Fundamental)
    assert result.ticker_id == ticker_id
    assert result.period == "Q1 2024"


@patch("domains.market_data.service.market_data_service.PricingAdapter")
def test_start_and_stop_price_simulation(mock_pricing_adapter: MagicMock) -> None:
    _ = mock_pricing_adapter
    service = MarketDataService(["localhost:9092"], "market.prices.live")
    service.pricing_adapter.generate_mock_ohlcv = MagicMock()  # type: ignore[method-assign]
    ticker_id = uuid4()
    service.start_price_simulation(ticker_id, "2024-01-01", days=2, interval_sec=0.01)
    # Let the simulation run a bit
    import time

    time.sleep(0.03)
    service.stop_price_simulation()
    # Should have called generate_mock_ohlcv at least once
    assert service.pricing_adapter.generate_mock_ohlcv.called
    assert service._simulation_thread is None
