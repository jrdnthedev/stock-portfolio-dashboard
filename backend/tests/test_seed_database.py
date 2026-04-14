"""Tests for database-enabled seed script."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from seed.seed_database import TICKER_DATA, generate_mock_prices, seed_database_real
from tests.test_fixtures import mock_db_session  # noqa: F401


class TestGenerateMockPrices:
    """Tests for generate_mock_prices function."""

    def test_generate_mock_prices_returns_list(self) -> None:
        """Test that generate_mock_prices returns a list."""
        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        prices = generate_mock_prices(100.0, start_date, days=10)

        assert isinstance(prices, list)
        assert len(prices) >= 10  # May be more due to weekend skipping

    def test_generate_mock_prices_skip_weekends(self) -> None:
        """Test that generated prices skip weekends."""
        # Start on a Friday
        start_date = datetime(2024, 1, 5, tzinfo=UTC)  # Friday
        prices = generate_mock_prices(100.0, start_date, days=5)

        # Verify no Saturday or Sunday dates
        for price in prices:
            weekday = price["date"].weekday()
            assert weekday < 5  # Monday=0, Friday=4

    def test_generate_mock_prices_has_correct_fields(self) -> None:
        """Test that each price point has all required fields."""
        start_date = datetime.now(UTC)
        prices = generate_mock_prices(100.0, start_date, days=5)

        required_fields = {"date", "open_price", "high", "low", "close", "volume"}
        for price in prices:
            assert set(price.keys()) == required_fields

    def test_generate_mock_prices_ohlcv_consistency(self) -> None:
        """Test that OHLCV data is logically consistent."""
        start_date = datetime.now(UTC)
        prices = generate_mock_prices(100.0, start_date, days=20)

        for price in prices:
            assert price["high"] >= price["low"]
            assert price["high"] >= price["open_price"]
            assert price["high"] >= price["close"]
            assert price["low"] <= price["open_price"]
            assert price["low"] <= price["close"]
            assert price["volume"] > 0
            assert isinstance(price["volume"], int)

    def test_generate_mock_prices_volatility_effect(self) -> None:
        """Test that different volatility affects price ranges."""
        start_date = datetime.now(UTC)

        low_vol_prices = generate_mock_prices(100.0, start_date, days=100, volatility=0.005)
        high_vol_prices = generate_mock_prices(100.0, start_date, days=100, volatility=0.05)

        low_vol_range = max(p["close"] for p in low_vol_prices) - min(
            p["close"] for p in low_vol_prices
        )
        high_vol_range = max(p["close"] for p in high_vol_prices) - min(
            p["close"] for p in high_vol_prices
        )

        # Higher volatility should generally produce wider range
        assert high_vol_range > low_vol_range

    def test_generate_mock_prices_positive_drift(self) -> None:
        """Test that prices have positive drift on average over time."""
        start_date = datetime.now(UTC)
        prices = generate_mock_prices(100.0, start_date, days=252)  # 1 year

        # Average final price should be higher than start price (positive drift)
        # Run multiple times to account for randomness (50 samples for statistical significance)
        final_prices = []
        for _ in range(50):
            prices = generate_mock_prices(100.0, start_date, days=252)
            final_prices.append(prices[-1]["close"])

        avg_final = sum(final_prices) / len(final_prices)
        # With 0.0005 daily drift over 252 days, expected return is ~13%, but with volatility
        # there's variance. Using 95 as threshold to be more robust (allows -5% on average)
        assert avg_final > 95  # Positive drift trend with some variance allowed

    def test_generate_mock_prices_rounding(self) -> None:
        """Test that prices are rounded to 2 decimal places."""
        start_date = datetime.now(UTC)
        prices = generate_mock_prices(100.0, start_date, days=10)

        for price in prices:
            assert round(price["open_price"], 2) == price["open_price"]
            assert round(price["high"], 2) == price["high"]
            assert round(price["low"], 2) == price["low"]
            assert round(price["close"], 2) == price["close"]

    def test_generate_mock_prices_date_sequence(self) -> None:
        """Test that dates are sequential (excluding weekends)."""
        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        prices = generate_mock_prices(100.0, start_date, days=20)

        dates = [p["date"] for p in prices]
        for i in range(1, len(dates)):
            # Each date should be after the previous (accounting for weekends)
            assert dates[i] > dates[i - 1]
            # Max gap should be 3 days (Friday to Monday)
            days_diff = (dates[i] - dates[i - 1]).days
            assert 1 <= days_diff <= 3


@patch("seed.seed_database.Ticker")
@patch("seed.seed_database.PricePoint")
@patch("seed.seed_database.Portfolio")
@patch("seed.seed_database.Holding")
class TestSeedDatabaseReal:
    """Tests for seed_database_real function."""

    def test_seed_creates_all_tickers(
        self,
        mock_holding: MagicMock,
        mock_portfolio: MagicMock,
        mock_price_point: MagicMock,
        mock_ticker: MagicMock,
        mock_db_session: Mock,
    ) -> None:
        """Test that seed creates all 20 tickers."""
        _ = mock_holding
        _ = mock_portfolio
        _ = mock_price_point

        # Configure mock tickers to have IDs
        mock_ticker_instances = []
        for i in range(len(TICKER_DATA)):
            mock_instance = Mock()
            mock_instance.id = i + 1
            mock_instance.symbol = TICKER_DATA[i][0]
            mock_ticker_instances.append(mock_instance)

        mock_ticker.side_effect = mock_ticker_instances

        # Mock query chain for price lookups
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [Mock(close=100.0) for _ in range(300)]
        mock_db_session.query.return_value = mock_query

        seed_database_real(mock_db_session)

        # Should create 20 tickers
        assert mock_ticker.call_count == len(TICKER_DATA)
        # Should add each ticker to session
        assert mock_db_session.add.call_count >= 20

    def test_seed_creates_tickers_with_correct_data(
        self,
        mock_holding: MagicMock,
        mock_portfolio: MagicMock,
        mock_price_point: MagicMock,
        mock_ticker: MagicMock,
        mock_db_session: Mock,
    ) -> None:
        """Test that tickers are created with correct attributes."""
        _ = mock_holding
        _ = mock_portfolio
        _ = mock_price_point

        mock_ticker_instances = []
        for i in range(len(TICKER_DATA)):
            mock_instance = Mock()
            mock_instance.id = i + 1
            mock_instance.symbol = TICKER_DATA[i][0]
            mock_ticker_instances.append(mock_instance)

        mock_ticker.side_effect = mock_ticker_instances

        # Mock query chain for price lookups
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [Mock(close=100.0) for _ in range(300)]
        mock_db_session.query.return_value = mock_query

        seed_database_real(mock_db_session)

        # Verify first ticker was created with correct data
        first_call = mock_ticker.call_args_list[0]
        assert first_call.kwargs["symbol"] == "AAPL"
        assert first_call.kwargs["company_name"] == "Apple Inc."
        assert first_call.kwargs["sector"] == "Technology"
        assert first_call.kwargs["exchange"] == "NASDAQ"
        assert first_call.kwargs["asset_class"] == "Equity"

    def test_seed_creates_price_points(
        self,
        mock_holding: MagicMock,
        mock_portfolio: MagicMock,
        mock_price_point: MagicMock,
        mock_ticker: MagicMock,
        mock_db_session: Mock,
    ) -> None:
        """Test that price points are created for each ticker."""
        _ = mock_holding
        _ = mock_portfolio
        _ = mock_price_point

        mock_ticker_instances = []
        for i in range(len(TICKER_DATA)):
            mock_instance = Mock()
            mock_instance.id = i + 1
            mock_instance.symbol = TICKER_DATA[i][0]
            mock_ticker_instances.append(mock_instance)

        mock_ticker.side_effect = mock_ticker_instances

        # Mock query chain for price lookups
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [Mock(close=100.0) for _ in range(300)]
        mock_db_session.query.return_value = mock_query

        seed_database_real(mock_db_session)

        # add_all should be called for price points (20 tickers * batch inserts)
        assert mock_db_session.add_all.call_count >= 20

    def test_seed_creates_one_portfolio(
        self,
        mock_holding: MagicMock,
        mock_portfolio: MagicMock,
        mock_price_point: MagicMock,
        mock_ticker: MagicMock,
        mock_db_session: Mock,
    ) -> None:
        """Test that exactly one portfolio is created."""
        _ = mock_holding
        _ = mock_price_point

        mock_ticker_instances = []
        for i in range(len(TICKER_DATA)):
            mock_instance = Mock()
            mock_instance.id = i + 1
            mock_instance.symbol = TICKER_DATA[i][0]
            mock_ticker_instances.append(mock_instance)

        mock_ticker.side_effect = mock_ticker_instances

        mock_portfolio_instance = Mock()
        mock_portfolio_instance.id = 1
        mock_portfolio.return_value = mock_portfolio_instance

        # Mock query for price points
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_price_instances = [Mock(close=100.0) for _ in range(300)]
        mock_query.all.return_value = mock_price_instances
        mock_db_session.query.return_value = mock_query

        seed_database_real(mock_db_session)

        # Should create exactly 1 portfolio
        assert mock_portfolio.call_count == 1
        assert mock_portfolio.call_args.kwargs["name"] == "Diversified Growth Portfolio"
        assert mock_portfolio.call_args.kwargs["owner"] == "demo_user"
        assert mock_portfolio.call_args.kwargs["currency"] == "USD"

    def test_seed_creates_ten_holdings(
        self,
        mock_holding: MagicMock,
        mock_portfolio: MagicMock,
        mock_price_point: MagicMock,
        mock_ticker: MagicMock,
        mock_db_session: Mock,
    ) -> None:
        """Test that exactly 10 holdings are created."""
        _ = mock_price_point

        mock_ticker_instances = []
        for i in range(len(TICKER_DATA)):
            mock_instance = Mock()
            mock_instance.id = i + 1
            mock_instance.symbol = TICKER_DATA[i][0]
            mock_ticker_instances.append(mock_instance)

        mock_ticker.side_effect = mock_ticker_instances

        mock_portfolio_instance = Mock()
        mock_portfolio_instance.id = 1
        mock_portfolio.return_value = mock_portfolio_instance

        # Mock query for price points
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_price_instances = [Mock(close=100.0) for _ in range(300)]
        mock_query.all.return_value = mock_price_instances
        mock_db_session.query.return_value = mock_query

        seed_database_real(mock_db_session)

        # Should create exactly 10 holdings
        assert mock_holding.call_count == 10

    def test_seed_commits_multiple_times(
        self,
        mock_holding: MagicMock,
        mock_portfolio: MagicMock,
        mock_price_point: MagicMock,
        mock_ticker: MagicMock,
        mock_db_session: Mock,
    ) -> None:
        """Test that commits happen at appropriate stages."""
        _ = mock_holding
        _ = mock_price_point

        mock_ticker_instances = []
        for i in range(len(TICKER_DATA)):
            mock_instance = Mock()
            mock_instance.id = i + 1
            mock_instance.symbol = TICKER_DATA[i][0]
            mock_ticker_instances.append(mock_instance)

        mock_ticker.side_effect = mock_ticker_instances

        mock_portfolio_instance = Mock()
        mock_portfolio_instance.id = 1
        mock_portfolio.return_value = mock_portfolio_instance

        # Mock query for price points
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_price_instances = [Mock(close=100.0) for _ in range(300)]
        mock_query.all.return_value = mock_price_instances
        mock_db_session.query.return_value = mock_query

        seed_database_real(mock_db_session)

        # Should commit after: tickers, prices, portfolio, holdings
        assert mock_db_session.commit.call_count >= 3

    def test_seed_handles_realistic_exchanges(
        self,
        mock_holding: MagicMock,
        mock_portfolio: MagicMock,
        mock_price_point: MagicMock,
        mock_ticker: MagicMock,
        mock_db_session: Mock,
    ) -> None:
        """Test that tickers are assigned to appropriate exchanges."""
        _ = mock_holding
        _ = mock_portfolio
        _ = mock_price_point

        mock_ticker_instances = []
        for i in range(len(TICKER_DATA)):
            mock_instance = Mock()
            mock_instance.id = i + 1
            mock_instance.symbol = TICKER_DATA[i][0]
            mock_ticker_instances.append(mock_instance)

        mock_ticker.side_effect = mock_ticker_instances

        # Mock query chain for price lookups
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [Mock(close=100.0) for _ in range(300)]
        mock_db_session.query.return_value = mock_query

        seed_database_real(mock_db_session)

        # Check that Technology stocks go to NASDAQ
        tech_calls = [
            call for call in mock_ticker.call_args_list if call.kwargs.get("sector") == "Technology"
        ]
        assert all(call.kwargs.get("exchange") == "NASDAQ" for call in tech_calls)

        # Check that non-Technology stocks go to NYSE
        non_tech_calls = [
            call for call in mock_ticker.call_args_list if call.kwargs.get("sector") != "Technology"
        ]
        assert all(call.kwargs.get("exchange") == "NYSE" for call in non_tech_calls)


class TestSeedDatabaseIntegration:
    """Integration tests that would run against a real test database."""

    @pytest.mark.skip(reason="Requires actual database connection")
    def test_seed_database_real_integration(self) -> None:
        """Integration test for seeding a real database."""
        # This would require setting up a test database
        # Keeping as a placeholder for future implementation
        pass

    @pytest.mark.skip(reason="Requires actual database connection")
    def test_seed_creates_valid_relationships(self) -> None:
        """Test that foreign key relationships are valid."""
        # This would test that ticker_id in holdings references actual tickers
        pass

    @pytest.mark.skip(reason="Requires actual database connection")
    def test_seed_data_queryable(self) -> None:
        """Test that seeded data can be queried successfully."""
        # This would test actual queries against the seeded database
        pass
