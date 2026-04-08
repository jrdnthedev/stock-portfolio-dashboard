"""Integration tests for market data API endpoints using testcontainers."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database.models import PricePoint, Ticker

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def market_tickers(db_session: Session) -> list[Ticker]:
    """Create sample market tickers for testing."""
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
        Ticker(
            id=uuid4(),
            symbol="JPM",
            company_name="JPMorgan Chase & Co.",
            exchange="NYSE",
            sector="Financial",
            asset_class="Stock",
        ),
        Ticker(
            id=uuid4(),
            symbol="V",
            company_name="Visa Inc.",
            exchange="NYSE",
            sector="Financial",
            asset_class="Stock",
        ),
    ]

    for ticker in tickers:
        db_session.add(ticker)
    db_session.commit()

    return tickers


@pytest.fixture
def sample_price_data(db_session: Session, market_tickers: list[Ticker]) -> list[PricePoint]:
    """Create sample historical price data for testing."""
    aapl_ticker = next(t for t in market_tickers if t.symbol == "AAPL")

    prices = [
        PricePoint(
            id=uuid4(),
            ticker_id=aapl_ticker.id,
            date=date(2026, 4, 1),
            open_price=176.25,
            high=178.50,
            low=175.80,
            close=178.50,
            volume=52340000,
        ),
        PricePoint(
            id=uuid4(),
            ticker_id=aapl_ticker.id,
            date=date(2026, 4, 2),
            open_price=178.50,
            high=180.25,
            low=177.90,
            close=179.80,
            volume=48920000,
        ),
        PricePoint(
            id=uuid4(),
            ticker_id=aapl_ticker.id,
            date=date(2026, 4, 3),
            open_price=179.80,
            high=181.00,
            low=178.50,
            close=180.25,
            volume=51200000,
        ),
    ]

    for price in prices:
        db_session.add(price)
    db_session.commit()

    return prices


class TestHistoricalPricesIntegration:
    """Integration tests for GET /v1/market/prices/{ticker}."""

    def test_get_historical_prices_success(
        self,
        client: TestClient,
        market_tickers: list[Ticker],
        sample_price_data: list[PricePoint],
        disable_cache,
    ):
        """Test retrieving historical prices from database."""
        response = client.get("/v1/market/prices/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Historical prices for AAPL" in data["message"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 3
        assert data["metadata"]["ticker"] == "AAPL"
        assert data["metadata"]["count"] == 3

        # Verify price data structure
        first_price = data["data"][0]
        assert "date" in first_price
        assert "open" in first_price
        assert "high" in first_price
        assert "low" in first_price
        assert "close" in first_price
        assert "volume" in first_price

    def test_get_historical_prices_with_date_range(
        self,
        client: TestClient,
        market_tickers: list[Ticker],
        sample_price_data: list[PricePoint],
        disable_cache,
    ):
        """Test retrieving historical prices with date range filter."""
        response = client.get("/v1/market/prices/AAPL?from=2026-04-01&to=2026-04-02")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["from"] == "2026-04-01"
        assert data["metadata"]["to"] == "2026-04-02"
        assert len(data["data"]) == 2

        # Verify dates are within range
        for price in data["data"]:
            price_date = datetime.strptime(price["date"], "%Y-%m-%d").date()
            assert date(2026, 4, 1) <= price_date <= date(2026, 4, 2)

    def test_get_historical_prices_with_from_date_only(
        self,
        client: TestClient,
        market_tickers: list[Ticker],
        sample_price_data: list[PricePoint],
        disable_cache,
    ):
        """Test retrieving historical prices with only from date."""
        response = client.get("/v1/market/prices/AAPL?from=2026-04-02")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["from"] == "2026-04-02"
        assert len(data["data"]) == 2  # 4/2 and 4/3

    def test_get_historical_prices_with_to_date_only(
        self,
        client: TestClient,
        market_tickers: list[Ticker],
        sample_price_data: list[PricePoint],
        disable_cache,
    ):
        """Test retrieving historical prices with only to date."""
        response = client.get("/v1/market/prices/AAPL?to=2026-04-02")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["to"] == "2026-04-02"
        assert len(data["data"]) == 2  # 4/1 and 4/2

    def test_get_historical_prices_case_insensitive(
        self,
        client: TestClient,
        market_tickers: list[Ticker],
        sample_price_data: list[PricePoint],
        disable_cache,
    ):
        """Test that ticker symbol is case-insensitive."""
        response = client.get("/v1/market/prices/aapl")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["ticker"] == "AAPL"

    def test_get_historical_prices_ticker_not_found(self, client: TestClient, disable_cache):
        """Test retrieving historical prices for non-existent ticker."""
        response = client.get("/v1/market/prices/INVALID")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Ticker not found" in data["message"]
        assert data["errors"] is not None

    def test_get_historical_prices_no_data(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test retrieving historical prices for ticker with no price data."""
        response = client.get("/v1/market/prices/GOOGL")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0
        assert data["metadata"]["count"] == 0


class TestLatestPriceIntegration:
    """Integration tests for GET /v1/market/prices/{ticker}/latest."""

    def test_get_latest_price_success(
        self,
        client: TestClient,
        market_tickers: list[Ticker],
        sample_price_data: list[PricePoint],
        disable_cache,
    ):
        """Test retrieving latest price for a ticker."""
        response = client.get("/v1/market/prices/AAPL/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Latest price for AAPL" in data["message"]
        assert data["data"]["ticker"] == "AAPL"
        assert "price" in data["data"]
        assert "change" in data["data"]
        assert "change_percent" in data["data"]
        assert "volume" in data["data"]
        assert "timestamp" in data["data"]

        # Latest price should be from most recent date (2026-04-03)
        assert data["data"]["price"] == 180.25

    def test_get_latest_price_case_insensitive(
        self,
        client: TestClient,
        market_tickers: list[Ticker],
        sample_price_data: list[PricePoint],
        disable_cache,
    ):
        """Test that ticker symbol is case-insensitive."""
        response = client.get("/v1/market/prices/aapl/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["ticker"] == "AAPL"

    def test_get_latest_price_ticker_not_found(self, client: TestClient, disable_cache):
        """Test retrieving latest price for non-existent ticker."""
        response = client.get("/v1/market/prices/INVALID/latest")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Ticker not found" in data["message"]

    def test_get_latest_price_no_data(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test retrieving latest price for ticker with no price data."""
        response = client.get("/v1/market/prices/MSFT/latest")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestFundamentalsIntegration:
    """Integration tests for GET /v1/market/fundamentals/{ticker}."""

    def test_get_fundamentals_success(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test retrieving fundamental data for a ticker."""
        response = client.get("/v1/market/fundamentals/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Fundamentals for AAPL" in data["message"]
        assert data["data"]["ticker"] == "AAPL"
        assert data["data"]["company_name"] == "Apple Inc."
        assert data["data"]["sector"] == "Technology"
        assert data["data"]["industry"] is not None
        assert "market_cap" in data["data"]
        assert "pe_ratio" in data["data"]
        assert "dividend_yield" in data["data"]

    def test_get_fundamentals_case_insensitive(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test that ticker symbol is case-insensitive."""
        response = client.get("/v1/market/fundamentals/aapl")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["ticker"] == "AAPL"

    def test_get_fundamentals_ticker_not_found(self, client: TestClient, disable_cache):
        """Test retrieving fundamentals for non-existent ticker."""
        response = client.get("/v1/market/fundamentals/INVALID")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Ticker not found" in data["message"]


class TestGetTickersIntegration:
    """Integration tests for GET /v1/market/tickers."""

    def test_get_tickers_all(self, client: TestClient, market_tickers: list[Ticker], disable_cache):
        """Test retrieving all tickers without filters."""
        response = client.get("/v1/market/tickers")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Tickers retrieved successfully" in data["message"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 5
        assert data["metadata"]["count"] == 5

        # Verify ticker structure
        ticker_symbols = {t["symbol"] for t in data["data"]}
        assert "AAPL" in ticker_symbols
        assert "GOOGL" in ticker_symbols
        assert "MSFT" in ticker_symbols
        assert "JPM" in ticker_symbols
        assert "V" in ticker_symbols

    def test_get_tickers_filter_by_sector(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test retrieving tickers filtered by sector."""
        response = client.get("/v1/market/tickers?sector=Technology")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3
        assert data["metadata"]["count"] == 3
        assert data["metadata"]["filters"]["sector"] == "Technology"

        # Verify all returned tickers are from Technology sector
        for ticker in data["data"]:
            assert ticker["sector"] == "Technology"

    def test_get_tickers_filter_by_exchange(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test retrieving tickers filtered by exchange."""
        response = client.get("/v1/market/tickers?exchange=NYSE")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["metadata"]["count"] == 2
        assert data["metadata"]["filters"]["exchange"] == "NYSE"

        # Verify all returned tickers are from NYSE
        for ticker in data["data"]:
            assert ticker["exchange"] == "NYSE"

    def test_get_tickers_filter_by_asset_class(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test retrieving tickers filtered by asset class."""
        response = client.get("/v1/market/tickers?asset_class=Stock")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 5
        assert data["metadata"]["filters"]["asset_class"] == "Stock"

    def test_get_tickers_multiple_filters(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test retrieving tickers with multiple filters."""
        response = client.get("/v1/market/tickers?sector=Financial&exchange=NYSE")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["metadata"]["filters"]["sector"] == "Financial"
        assert data["metadata"]["filters"]["exchange"] == "NYSE"

        # Verify returned tickers match both filters
        for ticker in data["data"]:
            assert ticker["sector"] == "Financial"
            assert ticker["exchange"] == "NYSE"

    def test_get_tickers_case_insensitive_filters(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test that filters are case-insensitive."""
        response = client.get("/v1/market/tickers?sector=technology")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3

    def test_get_tickers_no_matches(
        self, client: TestClient, market_tickers: list[Ticker], disable_cache
    ):
        """Test retrieving tickers with filters that match nothing."""
        response = client.get("/v1/market/tickers?sector=RealEstate")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0
        assert data["metadata"]["count"] == 0

    def test_get_tickers_empty_database(self, client: TestClient, disable_cache):
        """Test retrieving tickers from empty database."""
        response = client.get("/v1/market/tickers")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0


class TestMarketDataEdgeCases:
    """Integration tests for edge cases and error handling."""

    def test_invalid_date_format(
        self,
        client: TestClient,
        market_tickers: list[Ticker],
        sample_price_data: list[PricePoint],
        disable_cache,
    ):
        """Test handling of invalid date format in query parameters."""
        response = client.get("/v1/market/prices/AAPL?from=invalid-date")

        assert response.status_code == 422  # Validation error

    def test_from_date_after_to_date(
        self,
        client: TestClient,
        market_tickers: list[Ticker],
        sample_price_data: list[PricePoint],
        disable_cache,
    ):
        """Test handling when from date is after to date."""
        response = client.get("/v1/market/prices/AAPL?from=2026-04-05&to=2026-04-01")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0  # No data within that range
