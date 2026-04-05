"""Tests for in-memory seed data generation."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from seed.seed_data import (
    TICKER_DATA,
    PortfolioData,
    PriceData,
    TickerData,
    generate_mock_prices,
    seed_database,
)


class TestTickerData:
    """Tests for TickerData class."""

    def test_create_ticker(self) -> None:
        """Test creating a ticker."""
        storage = TickerData()
        ticker_id = storage.create_ticker("AAPL", "Apple Inc.", "Technology")

        assert isinstance(ticker_id, UUID)
        ticker = storage.get_ticker(ticker_id)
        assert ticker is not None
        assert ticker["symbol"] == "AAPL"
        assert ticker["company_name"] == "Apple Inc."
        assert ticker["sector"] == "Technology"
        assert ticker["exchange"] == "NASDAQ"  # Technology sector defaults to NASDAQ
        assert ticker["asset_class"] == "Equity"

    def test_create_ticker_non_tech_sector(self) -> None:
        """Test creating a ticker with non-tech sector gets NYSE exchange."""
        storage = TickerData()
        ticker_id = storage.create_ticker("JNJ", "Johnson & Johnson", "Healthcare")

        ticker = storage.get_ticker(ticker_id)
        assert ticker is not None
        assert ticker["exchange"] == "NYSE"  # Non-tech sector defaults to NYSE

    def test_get_ticker_by_symbol(self) -> None:
        """Test retrieving a ticker by symbol."""
        storage = TickerData()
        ticker_id = storage.create_ticker("MSFT", "Microsoft Corporation", "Technology")

        ticker = storage.get_ticker_by_symbol("MSFT")
        assert ticker is not None
        assert ticker["id"] == ticker_id
        assert ticker["symbol"] == "MSFT"

    def test_get_nonexistent_ticker(self) -> None:
        """Test retrieving a non-existent ticker returns None."""
        storage = TickerData()
        from uuid import uuid4

        ticker = storage.get_ticker(uuid4())
        assert ticker is None

    def test_get_ticker_by_nonexistent_symbol(self) -> None:
        """Test retrieving by non-existent symbol returns None."""
        storage = TickerData()
        ticker = storage.get_ticker_by_symbol("NONEXISTENT")
        assert ticker is None


class TestPriceData:
    """Tests for PriceData class."""

    def test_create_price(self) -> None:
        """Test creating a price point."""
        storage = PriceData()
        from uuid import uuid4

        ticker_id = uuid4()
        date = datetime.now(UTC)

        storage.create_price(
            ticker_id=ticker_id,
            date=date,
            open_price=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000,
        )

        prices = storage.get_prices(ticker_id)
        assert len(prices) == 1
        assert prices[0]["open_price"] == 100.0
        assert prices[0]["close"] == 103.0
        assert prices[0]["volume"] == 1000000

    def test_get_prices_sorted_by_date(self) -> None:
        """Test that prices are returned sorted by date."""
        storage = PriceData()
        from uuid import uuid4

        ticker_id = uuid4()
        base_date = datetime.now(UTC)

        # Add prices in random order
        storage.create_price(ticker_id, base_date + timedelta(days=2), 100, 100, 100, 100, 1000)
        storage.create_price(ticker_id, base_date, 100, 100, 100, 100, 1000)
        storage.create_price(ticker_id, base_date + timedelta(days=1), 100, 100, 100, 100, 1000)

        prices = storage.get_prices(ticker_id)
        assert len(prices) == 3
        assert prices[0]["date"] == base_date.date()
        assert prices[1]["date"] == (base_date + timedelta(days=1)).date()
        assert prices[2]["date"] == (base_date + timedelta(days=2)).date()

    def test_get_latest_price(self) -> None:
        """Test getting the latest price for a ticker."""
        storage = PriceData()
        from uuid import uuid4

        ticker_id = uuid4()
        base_date = datetime.now(UTC)

        storage.create_price(ticker_id, base_date, 100, 100, 100, 100, 1000)
        storage.create_price(ticker_id, base_date + timedelta(days=1), 105, 105, 105, 105, 1000)

        latest = storage.get_latest_price(ticker_id)
        assert latest is not None
        assert latest["close"] == 105
        assert latest["date"] == (base_date + timedelta(days=1)).date()

    def test_get_latest_price_empty(self) -> None:
        """Test getting latest price when no prices exist."""
        storage = PriceData()
        from uuid import uuid4

        latest = storage.get_latest_price(uuid4())
        assert latest is None

    def test_get_prices_for_multiple_tickers(self) -> None:
        """Test that prices are isolated per ticker."""
        storage = PriceData()
        from uuid import uuid4

        ticker1_id = uuid4()
        ticker2_id = uuid4()
        date = datetime.now(UTC)

        storage.create_price(ticker1_id, date, 100, 100, 100, 100, 1000)
        storage.create_price(ticker2_id, date, 200, 200, 200, 200, 2000)

        prices1 = storage.get_prices(ticker1_id)
        prices2 = storage.get_prices(ticker2_id)

        assert len(prices1) == 1
        assert len(prices2) == 1
        assert prices1[0]["close"] == 100
        assert prices2[0]["close"] == 200


class TestPortfolioData:
    """Tests for PortfolioData class."""

    def test_create_portfolio(self) -> None:
        """Test creating a portfolio."""
        storage = PortfolioData()
        portfolio_id = storage.create_portfolio("Test Portfolio", "test_user", "USD")

        assert isinstance(portfolio_id, UUID)
        portfolio = storage.portfolios[portfolio_id]
        assert portfolio["name"] == "Test Portfolio"
        assert portfolio["owner"] == "test_user"
        assert portfolio["currency"] == "USD"
        assert isinstance(portfolio["created_at"], datetime)

    def test_create_holding(self) -> None:
        """Test creating a holding."""
        storage = PortfolioData()
        from uuid import uuid4

        portfolio_id = storage.create_portfolio("Test Portfolio", "test_user")
        ticker_id = uuid4()

        holding_id = storage.create_holding(
            portfolio_id=portfolio_id,
            ticker_id=ticker_id,
            quantity=100.0,
            avg_cost_basis=50.0,
        )

        assert isinstance(holding_id, UUID)
        holding = storage.holdings[holding_id]
        assert holding["portfolio_id"] == portfolio_id
        assert holding["ticker_id"] == ticker_id
        assert holding["quantity"] == 100.0
        assert holding["avg_cost_basis"] == 50.0
        assert isinstance(holding["opened_at"], datetime)

    def test_get_portfolio_holdings(self) -> None:
        """Test retrieving all holdings for a portfolio."""
        storage = PortfolioData()
        from uuid import uuid4

        portfolio1_id = storage.create_portfolio("Portfolio 1", "user1")
        portfolio2_id = storage.create_portfolio("Portfolio 2", "user2")

        ticker1_id = uuid4()
        ticker2_id = uuid4()
        ticker3_id = uuid4()

        # Add holdings to portfolio 1
        storage.create_holding(portfolio1_id, ticker1_id, 100, 50)
        storage.create_holding(portfolio1_id, ticker2_id, 200, 60)

        # Add holding to portfolio 2
        storage.create_holding(portfolio2_id, ticker3_id, 300, 70)

        holdings1 = storage.get_portfolio_holdings(portfolio1_id)
        holdings2 = storage.get_portfolio_holdings(portfolio2_id)

        assert len(holdings1) == 2
        assert len(holdings2) == 1
        assert all(h["portfolio_id"] == portfolio1_id for h in holdings1)
        assert all(h["portfolio_id"] == portfolio2_id for h in holdings2)

    def test_get_portfolio_holdings_empty(self) -> None:
        """Test getting holdings for a portfolio with no holdings."""
        storage = PortfolioData()
        portfolio_id = storage.create_portfolio("Empty Portfolio", "user")

        holdings = storage.get_portfolio_holdings(portfolio_id)
        assert holdings == []


class TestGenerateMockPrices:
    """Tests for generate_mock_prices function."""

    def test_generate_mock_prices_basic(self) -> None:
        """Test generating mock prices returns correct number of items."""
        from uuid import uuid4

        ticker_id = uuid4()
        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        prices = generate_mock_prices(ticker_id, 100.0, start_date, days=10)

        # Should generate prices, but skipping weekends
        assert len(prices) >= 10
        assert all(isinstance(p["date"], datetime) for p in prices)
        assert all(p["ticker_id"] == ticker_id for p in prices)

    def test_generate_mock_prices_skip_weekends(self) -> None:
        """Test that generated prices skip weekends."""
        from uuid import uuid4

        ticker_id = uuid4()
        # Start on a Friday
        start_date = datetime(2024, 1, 5, tzinfo=UTC)  # Friday
        prices = generate_mock_prices(ticker_id, 100.0, start_date, days=5)

        # Verify no Saturday or Sunday dates
        for price in prices:
            weekday = price["date"].weekday()
            assert weekday < 5  # Monday=0, Friday=4

    def test_generate_mock_prices_ohlcv_consistency(self) -> None:
        """Test that OHLCV data is consistent (high >= low, etc.)."""
        from uuid import uuid4

        ticker_id = uuid4()
        start_date = datetime.now(UTC)
        prices = generate_mock_prices(ticker_id, 100.0, start_date, days=20)

        for price in prices:
            assert price["high"] >= price["low"]
            assert price["high"] >= price["open_price"]
            assert price["high"] >= price["close"]
            assert price["low"] <= price["open_price"]
            assert price["low"] <= price["close"]
            assert price["volume"] > 0

    def test_generate_mock_prices_volatility(self) -> None:
        """Test that higher volatility produces more price variation."""
        from uuid import uuid4

        ticker_id = uuid4()
        start_date = datetime.now(UTC)

        low_vol_prices = generate_mock_prices(
            ticker_id, 100.0, start_date, days=100, volatility=0.005
        )
        high_vol_prices = generate_mock_prices(
            ticker_id, 100.0, start_date, days=100, volatility=0.05
        )

        # Calculate price ranges
        low_vol_range = max(p["close"] for p in low_vol_prices) - min(
            p["close"] for p in low_vol_prices
        )
        high_vol_range = max(p["close"] for p in high_vol_prices) - min(
            p["close"] for p in high_vol_prices
        )

        # Higher volatility should generally produce wider range
        # (This is probabilistic, but with 100 days it's very likely)
        assert high_vol_range > low_vol_range

    def test_generate_mock_prices_rounding(self) -> None:
        """Test that prices are rounded to 2 decimal places."""
        from uuid import uuid4

        ticker_id = uuid4()
        start_date = datetime.now(UTC)
        prices = generate_mock_prices(ticker_id, 100.0, start_date, days=10)

        for price in prices:
            # Check that prices have at most 2 decimal places
            assert round(price["open_price"], 2) == price["open_price"]
            assert round(price["high"], 2) == price["high"]
            assert round(price["low"], 2) == price["low"]
            assert round(price["close"], 2) == price["close"]


class TestSeedDatabase:
    """Tests for the main seed_database function."""

    def test_seed_database_creates_all_tickers(self) -> None:
        """Test that seed_database creates all expected tickers."""
        tickers, _, _ = seed_database()

        assert len(tickers.tickers) == len(TICKER_DATA)

        for symbol, company_name, _ in TICKER_DATA:
            ticker = tickers.get_ticker_by_symbol(symbol)
            assert ticker is not None
            assert ticker["company_name"] == company_name

    def test_seed_database_creates_price_data(self) -> None:
        """Test that seed_database creates price data for all tickers."""
        tickers, prices, _ = seed_database()

        for ticker_id in tickers.tickers:
            ticker_prices = prices.get_prices(ticker_id)
            assert len(ticker_prices) > 0
            # Should have approximately 5 years * 252 trading days
            assert len(ticker_prices) >= 1000

    def test_seed_database_creates_portfolio(self) -> None:
        """Test that seed_database creates a portfolio."""
        _, _, portfolios = seed_database()

        assert len(portfolios.portfolios) == 1
        portfolio = list(portfolios.portfolios.values())[0]
        assert portfolio["name"] == "Diversified Growth Portfolio"
        assert portfolio["owner"] == "demo_user"
        assert portfolio["currency"] == "USD"

    def test_seed_database_creates_holdings(self) -> None:
        """Test that seed_database creates 10 holdings."""
        tickers, prices, portfolios = seed_database()

        portfolio_id = list(portfolios.portfolios.keys())[0]
        holdings = portfolios.get_portfolio_holdings(portfolio_id)

        assert len(holdings) == 10

        # Verify each holding has valid data
        for holding in holdings:
            assert holding["quantity"] > 0
            assert holding["avg_cost_basis"] > 0
            # Verify the ticker exists
            ticker = tickers.get_ticker(holding["ticker_id"])
            assert ticker is not None
            # Verify price data exists
            latest_price = prices.get_latest_price(holding["ticker_id"])
            assert latest_price is not None

    def test_seed_database_holdings_have_realistic_cost_basis(self) -> None:
        """Test that holdings have realistic cost basis (from historical prices)."""
        tickers, prices, portfolios = seed_database()

        portfolio_id = list(portfolios.portfolios.keys())[0]
        holdings = portfolios.get_portfolio_holdings(portfolio_id)

        for holding in holdings:
            # Cost basis should be within a reasonable range of current prices
            latest_price = prices.get_latest_price(holding["ticker_id"])
            assert latest_price is not None

            current_price = latest_price["close"]
            cost_basis = holding["avg_cost_basis"]

            # Cost basis should be positive and within a reasonable range
            # (could be higher or lower due to market movements)
            assert cost_basis > 0
            assert 0.1 < (cost_basis / current_price) < 10  # No more than 10x difference

    def test_seed_database_returns_correct_types(self) -> None:
        """Test that seed_database returns the correct data types."""
        tickers, prices, portfolios = seed_database()

        assert isinstance(tickers, TickerData)
        assert isinstance(prices, PriceData)
        assert isinstance(portfolios, PortfolioData)

    def test_seed_database_deterministic_ticker_count(self) -> None:
        """Test that running seed twice produces same ticker count."""
        tickers1, _, _ = seed_database()
        tickers2, _, _ = seed_database()

        assert len(tickers1.tickers) == len(tickers2.tickers)

    def test_seed_database_price_data_chronological(self) -> None:
        """Test that price data is in chronological order."""
        tickers, prices, _ = seed_database()

        for ticker_id in tickers.tickers:
            ticker_prices = prices.get_prices(ticker_id)
            dates = [p["date"] for p in ticker_prices]
            # Verify dates are sorted
            assert dates == sorted(dates)
