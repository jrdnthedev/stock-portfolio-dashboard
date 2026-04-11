from uuid import uuid4

from domains.market_data.models.models import Fundamental
from domains.market_data.service.fundamentals_adapter import FundamentalsAdapter


def test_generate_mock_fundamental() -> None:
    adapter = FundamentalsAdapter()
    ticker_id = uuid4()
    result = adapter.generate_mock_fundamental(ticker_id, "Q1 2024")
    assert isinstance(result, Fundamental)
    assert result.ticker_id == ticker_id
    assert result.period == "Q1 2024"
    assert result.revenue > 0
    assert result.eps > 0
    assert result.pe_ratio > 0
    assert result.market_cap > 0


def test_get_fundamental_snapshot() -> None:
    adapter = FundamentalsAdapter()
    ticker_id = uuid4()
    result = adapter.get_fundamental_snapshot(ticker_id, "Q2 2025")
    assert isinstance(result, Fundamental)
    assert result.ticker_id == ticker_id
    assert result.period == "Q2 2025"
