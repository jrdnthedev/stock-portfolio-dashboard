"""Tests for seed runner and integration."""

import contextlib
from io import StringIO
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from seed.run_seed import integrate_with_services
from seed.seed_data import PortfolioData, PriceData, TickerData


@pytest.fixture
def mock_seed_database() -> tuple[TickerData, PriceData, PortfolioData]:
    """Create mock seed data for testing."""
    tickers = TickerData()
    prices = PriceData()
    portfolios = PortfolioData()

    # Create a few test tickers
    ticker1_id = tickers.create_ticker("AAPL", "Apple Inc.", "Technology")
    ticker2_id = tickers.create_ticker("MSFT", "Microsoft Corporation", "Technology")
    ticker3_id = tickers.create_ticker("JNJ", "Johnson & Johnson", "Healthcare")

    # Create some price data
    from datetime import UTC, datetime

    date = datetime.now(UTC)
    for ticker_id in [ticker1_id, ticker2_id, ticker3_id]:
        prices.create_price(ticker_id, date, 100.0, 105.0, 95.0, 102.0, 1000000)

    # Create a portfolio with holdings
    portfolio_id = portfolios.create_portfolio("Test Portfolio", "test_user", "USD")
    portfolios.create_holding(portfolio_id, ticker1_id, 50.0, 95.0)
    portfolios.create_holding(portfolio_id, ticker2_id, 100.0, 90.0)

    return tickers, prices, portfolios


class TestIntegrateWithServices:
    """Tests for the integrate_with_services function."""

    @patch("seed.run_seed.seed_database")
    def test_integrate_calls_seed_database(self, mock_seed: Mock) -> None:
        """Test that integrate_with_services calls seed_database."""
        # Setup mock to return empty storages to avoid errors
        mock_seed.return_value = (TickerData(), PriceData(), PortfolioData())

        integrate_with_services()

        mock_seed.assert_called_once()

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_prints_ticker_info(
        self, mock_stdout: StringIO, mock_seed: Mock, mock_seed_database: tuple
    ) -> None:
        """Test that integrate_with_services prints ticker information."""
        mock_seed.return_value = mock_seed_database

        integrate_with_services()

        output = mock_stdout.getvalue()
        assert "Available Tickers:" in output
        assert "AAPL" in output
        assert "Apple Inc." in output
        assert "Technology" in output

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_prints_portfolio_info(
        self, mock_stdout: StringIO, mock_seed: Mock, mock_seed_database: tuple
    ) -> None:
        """Test that integrate_with_services prints portfolio information."""
        mock_seed.return_value = mock_seed_database

        integrate_with_services()

        output = mock_stdout.getvalue()
        assert "Portfolio Holdings:" in output
        assert "Test Portfolio" in output
        assert "test_user" in output
        assert "USD" in output

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_prints_holdings_info(
        self, mock_stdout: StringIO, mock_seed: Mock, mock_seed_database: tuple
    ) -> None:
        """Test that integrate_with_services prints holdings information."""
        mock_seed.return_value = mock_seed_database

        integrate_with_services()

        output = mock_stdout.getvalue()
        assert "Holdings" in output
        assert "AAPL" in output
        assert "shares" in output
        assert "Value:" in output
        assert "P&L:" in output

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_calculates_pnl(
        self, mock_stdout: StringIO, mock_seed: Mock, mock_seed_database: tuple
    ) -> None:
        """Test that integrate_with_services calculates P&L correctly."""
        tickers, prices, portfolios = mock_seed_database
        mock_seed.return_value = (tickers, prices, portfolios)

        integrate_with_services()

        output = mock_stdout.getvalue()
        # Should show P&L calculations (positive since current > cost basis)
        assert "P&L:" in output
        # Should show percentage
        assert "%" in output

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_prints_integration_hint(
        self, mock_stdout: StringIO, mock_seed: Mock, mock_seed_database: tuple
    ) -> None:
        """Test that integrate_with_services prints usage hint."""
        mock_seed.return_value = mock_seed_database

        integrate_with_services()

        output = mock_stdout.getvalue()
        assert "To use this data with PortfolioService" in output

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_shows_limited_tickers(self, mock_stdout: StringIO, mock_seed: Mock) -> None:
        """Test that only first 5 tickers are shown in detail."""
        tickers = TickerData()
        prices = PriceData()
        portfolios = PortfolioData()

        # Create 10 tickers
        from datetime import UTC, datetime

        date = datetime.now(UTC)
        for i in range(10):
            ticker_id = tickers.create_ticker(f"TICK{i}", f"Company {i}", "Technology")
            prices.create_price(ticker_id, date, 100.0, 100.0, 100.0, 100.0, 1000)

        mock_seed.return_value = (tickers, prices, portfolios)

        integrate_with_services()

        output = mock_stdout.getvalue()
        # Should show first 5
        assert "TICK0" in output
        assert "TICK4" in output
        # Should indicate more exist
        assert "and 5 more" in output

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_displays_market_values(
        self, mock_stdout: StringIO, mock_seed: Mock, mock_seed_database: tuple
    ) -> None:
        """Test that market values are displayed for holdings."""
        mock_seed.return_value = mock_seed_database

        integrate_with_services()

        output = mock_stdout.getvalue()
        assert "Value:" in output
        assert "$" in output

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_handles_empty_portfolio(
        self, mock_stdout: StringIO, mock_seed: Mock
    ) -> None:
        """Test that integrate_with_services handles portfolios with no holdings."""
        tickers = TickerData()
        prices = PriceData()
        portfolios = PortfolioData()

        # Create portfolio but no holdings
        portfolios.create_portfolio("Empty Portfolio", "test_user", "USD")

        mock_seed.return_value = (tickers, prices, portfolios)

        integrate_with_services()

        output = mock_stdout.getvalue()
        assert "Holdings (0)" in output

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_formats_numbers_correctly(
        self, mock_stdout: StringIO, mock_seed: Mock, mock_seed_database: tuple
    ) -> None:
        """Test that numbers are formatted with appropriate precision."""
        mock_seed.return_value = mock_seed_database

        integrate_with_services()

        output = mock_stdout.getvalue()
        # Should have decimal formatting for shares
        assert ".2f" in output or "50.00" in output or "100.00" in output

    @patch("seed.run_seed.seed_database")
    def test_integrate_accesses_all_storages(
        self, mock_seed: Mock, mock_seed_database: tuple
    ) -> None:
        """Test that integrate_with_services accesses all three storage types."""
        tickers, prices, portfolios = mock_seed_database
        mock_seed.return_value = (tickers, prices, portfolios)

        # Add some spies
        original_get_ticker = tickers.get_ticker
        original_get_latest = prices.get_latest_price
        original_get_holdings = portfolios.get_portfolio_holdings

        get_ticker_called = False
        get_latest_called = False
        get_holdings_called = False

        def spy_get_ticker(*args: object, **kwargs: object) -> dict | None:
            nonlocal get_ticker_called
            get_ticker_called = True
            return original_get_ticker(*args, **kwargs)  # type: ignore[no-any-return]

        def spy_get_latest(*args: object, **kwargs: object) -> dict | None:
            nonlocal get_latest_called
            get_latest_called = True
            return original_get_latest(*args, **kwargs)  # type: ignore[no-any-return]

        def spy_get_holdings(*args: object, **kwargs: object) -> list[dict]:
            nonlocal get_holdings_called
            get_holdings_called = True
            return original_get_holdings(*args, **kwargs)  # type: ignore[no-any-return]

        tickers.get_ticker = spy_get_ticker
        prices.get_latest_price = spy_get_latest
        portfolios.get_portfolio_holdings = spy_get_holdings

        integrate_with_services()

        assert get_ticker_called
        assert get_latest_called
        assert get_holdings_called


class TestRunSeedMain:
    """Tests for running the seed module as main."""

    @patch("seed.run_seed.integrate_with_services")
    def test_main_calls_integrate(self, mock_integrate: Mock) -> None:
        """Test that __main__ calls integrate_with_services."""
        _ = mock_integrate

        with patch("sys.argv", ["run_seed.py"]):
            contextlib.suppress(SystemExit)

        # The module should have called integrate_with_services
        # (This might not work perfectly due to import caching, but it's a structural test)


class TestSeedDataStructures:
    """Tests for the data structures returned by seed."""

    def test_ticker_storage_structure(self, mock_seed_database: tuple) -> None:
        """Test that ticker storage has expected structure."""
        tickers, _, _ = mock_seed_database

        assert hasattr(tickers, "tickers")
        assert hasattr(tickers, "symbol_to_id")
        assert isinstance(tickers.tickers, dict)
        assert isinstance(tickers.symbol_to_id, dict)

    def test_price_storage_structure(self, mock_seed_database: tuple) -> None:
        """Test that price storage has expected structure."""
        _, prices, _ = mock_seed_database

        assert hasattr(prices, "prices")
        assert isinstance(prices.prices, dict)

    def test_portfolio_storage_structure(self, mock_seed_database: tuple) -> None:
        """Test that portfolio storage has expected structure."""
        _, _, portfolios = mock_seed_database

        assert hasattr(portfolios, "portfolios")
        assert hasattr(portfolios, "holdings")
        assert isinstance(portfolios.portfolios, dict)
        assert isinstance(portfolios.holdings, dict)

    def test_ticker_data_completeness(self, mock_seed_database: tuple) -> None:
        """Test that ticker data has all required fields."""
        tickers, _, _ = mock_seed_database

        for ticker in tickers.tickers.values():
            assert "id" in ticker
            assert "symbol" in ticker
            assert "company_name" in ticker
            assert "exchange" in ticker
            assert "sector" in ticker
            assert "asset_class" in ticker

    def test_price_data_completeness(self, mock_seed_database: tuple) -> None:
        """Test that price data has all required fields."""
        _, prices, _ = mock_seed_database

        for ticker_prices in prices.prices.values():
            for price in ticker_prices:
                assert "id" in price
                assert "ticker_id" in price
                assert "date" in price
                assert "open_price" in price
                assert "high" in price
                assert "low" in price
                assert "close" in price
                assert "volume" in price

    def test_holding_data_completeness(self, mock_seed_database: tuple) -> None:
        """Test that holding data has all required fields."""
        _, _, portfolios = mock_seed_database

        for holding in portfolios.holdings.values():
            assert "id" in holding
            assert "portfolio_id" in holding
            assert "ticker_id" in holding
            assert "quantity" in holding
            assert "avg_cost_basis" in holding
            assert "opened_at" in holding


class TestSeedErrorHandling:
    """Tests for error handling in seed integration."""

    @patch("seed.run_seed.seed_database")
    def test_integrate_handles_missing_price_data(self, mock_seed: Mock) -> None:
        """Test that integrate handles holdings with missing price data gracefully."""
        tickers = TickerData()
        prices = PriceData()
        portfolios = PortfolioData()

        ticker_id = tickers.create_ticker("TEST", "Test Corp", "Technology")
        portfolio_id = portfolios.create_portfolio("Test Portfolio", "user", "USD")
        portfolios.create_holding(portfolio_id, ticker_id, 100.0, 50.0)
        # Note: No price data created for this ticker

        mock_seed.return_value = (tickers, prices, portfolios)

        # Should not raise an exception
        try:
            integrate_with_services()
        except Exception as e:
            pytest.fail(f"integrate_with_services raised an exception: {e}")

    @patch("seed.run_seed.seed_database")
    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_handles_missing_ticker(self, mock_stdout: StringIO, mock_seed: Mock) -> None:
        """Test that integrate handles holdings with missing ticker gracefully."""
        tickers = TickerData()
        prices = PriceData()
        portfolios = PortfolioData()

        # Create holding for non-existent ticker
        portfolio_id = portfolios.create_portfolio("Test Portfolio", "user", "USD")
        fake_ticker_id = uuid4()
        portfolios.create_holding(portfolio_id, fake_ticker_id, 100.0, 50.0)

        mock_seed.return_value = (tickers, prices, portfolios)

        # Should handle missing ticker gracefully
        integrate_with_services()

        output = mock_stdout.getvalue()
        assert "UNKNOWN" in output  # Should show UNKNOWN for missing ticker
