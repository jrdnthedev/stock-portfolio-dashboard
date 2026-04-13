"""Unit tests for market data routes."""

from fastapi.testclient import TestClient

# Uses the seeded_client fixture from conftest.py which provides a test app
# with mocked authentication, database, and pre-seeded test data


class TestHistoricalPrices:
    """Test historical prices endpoint."""

    def test_get_historical_prices_success(self, seeded_client: TestClient) -> None:
        """Test retrieving historical prices without date filters."""
        response = seeded_client.get("/v1/market/prices/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Historical prices for AAPL" in data["message"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        assert data["metadata"]["ticker"] == "AAPL"
        assert data["metadata"]["count"] == len(data["data"])

    def test_get_historical_prices_with_date_range(self, seeded_client: TestClient) -> None:
        """Test retrieving historical prices with date range."""
        response = seeded_client.get("/v1/market/prices/AAPL?from=2026-04-01&to=2026-04-02")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["from"] == "2026-04-01"
        assert data["metadata"]["to"] == "2026-04-02"
        # Should only return prices within the date range
        for price in data["data"]:
            assert "2026-04-01" <= price["date"] <= "2026-04-02"

    def test_get_historical_prices_ticker_not_found(self, seeded_client: TestClient) -> None:
        """Test retrieving historical prices for non-existent ticker."""
        response = seeded_client.get("/v1/market/prices/INVALID")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Ticker not found" in data["message"]
        assert data["errors"] is not None
        assert data["errors"][0]["code"] == "NOT_FOUND"


class TestLatestPrice:
    """Test latest price endpoint."""

    def test_get_latest_price_success(self, seeded_client: TestClient) -> None:
        """Test retrieving latest price."""
        response = seeded_client.get("/v1/market/prices/AAPL/latest")
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

    def test_get_latest_price_ticker_not_found(self, seeded_client: TestClient) -> None:
        """Test retrieving latest price for non-existent ticker."""
        response = seeded_client.get("/v1/market/prices/INVALID/latest")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Ticker not found" in data["message"]


class TestFundamentals:
    """Test fundamentals endpoint."""

    def test_get_fundamentals_success(self, seeded_client: TestClient) -> None:
        """Test retrieving fundamentals."""
        response = seeded_client.get("/v1/market/fundamentals/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Fundamentals for AAPL" in data["message"]
        assert data["data"]["ticker"] == "AAPL"
        assert data["data"]["company_name"] == "Apple Inc."
        assert "sector" in data["data"]
        assert "industry" in data["data"]
        assert "market_cap" in data["data"]
        assert "pe_ratio" in data["data"]

    def test_get_fundamentals_ticker_not_found(self, seeded_client: TestClient) -> None:
        """Test retrieving fundamentals for non-existent ticker."""
        response = seeded_client.get("/v1/market/fundamentals/INVALID")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Ticker not found" in data["message"]


class TestTickers:
    """Test tickers listing endpoint."""

    def test_get_all_tickers(self, seeded_client: TestClient) -> None:
        """Test retrieving all tickers without filters."""
        response = seeded_client.get("/v1/market/tickers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Tickers retrieved successfully" in data["message"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        assert data["metadata"]["count"] == len(data["data"])

    def test_get_tickers_filter_by_sector(self, seeded_client: TestClient) -> None:
        """Test retrieving tickers filtered by sector."""
        response = seeded_client.get("/v1/market/tickers?sector=Technology")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["filters"]["sector"] == "Technology"
        # All returned tickers should be in Technology sector
        for ticker in data["data"]:
            assert ticker["sector"] == "Technology"

    def test_get_tickers_filter_by_exchange(self, seeded_client: TestClient) -> None:
        """Test retrieving tickers filtered by exchange."""
        response = seeded_client.get("/v1/market/tickers?exchange=NASDAQ")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["filters"]["exchange"] == "NASDAQ"
        # All returned tickers should be on NASDAQ
        for ticker in data["data"]:
            assert ticker["exchange"] == "NASDAQ"

    def test_get_tickers_filter_by_asset_class(self, seeded_client: TestClient) -> None:
        """Test retrieving tickers filtered by asset class."""
        response = seeded_client.get("/v1/market/tickers?asset_class=Stock")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["filters"]["asset_class"] == "Stock"
        # All returned tickers should be stocks
        for ticker in data["data"]:
            assert ticker["asset_class"] == "Stock"

    def test_get_tickers_multiple_filters(self, seeded_client: TestClient) -> None:
        """Test retrieving tickers with multiple filters."""
        response = seeded_client.get("/v1/market/tickers?sector=Financial&exchange=NYSE")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # All returned tickers should match all filters
        for ticker in data["data"]:
            assert ticker["sector"] == "Financial"
            assert ticker["exchange"] == "NYSE"
