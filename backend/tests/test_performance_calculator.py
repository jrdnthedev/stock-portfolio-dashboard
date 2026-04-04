from uuid import uuid4

import pytest

from domains.portfolio.services.performance_calculator import PerformanceCalculator


@pytest.fixture
def calculator() -> PerformanceCalculator:
    return PerformanceCalculator()


class TestPerformanceCalculatorPriceManagement:
    def test_update_price(self, calculator: PerformanceCalculator) -> None:
        ticker_id = uuid4()
        calculator.update_price(ticker_id, 100.50)
        assert calculator.current_prices[ticker_id] == 100.50

    def test_update_price_overwrites_existing(self, calculator: PerformanceCalculator) -> None:
        ticker_id = uuid4()
        calculator.update_price(ticker_id, 100.0)
        calculator.update_price(ticker_id, 105.0)
        assert calculator.current_prices[ticker_id] == 105.0

    def test_set_ticker_sector(self, calculator: PerformanceCalculator) -> None:
        ticker_id = uuid4()
        calculator.set_ticker_sector(ticker_id, "Technology")
        assert calculator.ticker_sectors[ticker_id] == "Technology"


class TestPerformanceCalculatorHoldingPerformance:
    def test_calculate_holding_performance(self, calculator: PerformanceCalculator) -> None:
        ticker_id = uuid4()
        calculator.update_price(ticker_id, 100.0)

        result = calculator.calculate_holding_performance(
            ticker_id=ticker_id,
            quantity=10.0,
            avg_cost_basis=80.0,
            total_portfolio_value=5000.0,
        )

        assert result is not None
        assert result.ticker_id == ticker_id
        assert result.quantity == 10.0
        assert result.avg_cost_basis == 80.0
        assert result.current_price == 100.0
        assert result.market_value == 1000.0  # 10 * 100
        assert result.unrealized_pnl == 200.0  # (10 * 100) - (10 * 80)
        assert result.unrealized_pnl_pct == 25.0  # 200 / 800 * 100
        assert result.weight == 20.0  # 1000 / 5000 * 100

    def test_calculate_holding_performance_returns_none_if_no_price(
        self, calculator: PerformanceCalculator
    ) -> None:
        ticker_id = uuid4()
        result = calculator.calculate_holding_performance(
            ticker_id=ticker_id,
            quantity=10.0,
            avg_cost_basis=80.0,
            total_portfolio_value=5000.0,
        )
        assert result is None

    def test_calculate_holding_performance_with_loss(
        self, calculator: PerformanceCalculator
    ) -> None:
        ticker_id = uuid4()
        calculator.update_price(ticker_id, 50.0)

        result = calculator.calculate_holding_performance(
            ticker_id=ticker_id,
            quantity=10.0,
            avg_cost_basis=80.0,
            total_portfolio_value=5000.0,
        )

        assert result is not None
        assert result.market_value == 500.0
        assert result.unrealized_pnl == -300.0  # 500 - 800
        assert result.unrealized_pnl_pct == -37.5  # -300 / 800 * 100

    def test_calculate_holding_performance_handles_zero_cost_basis(
        self, calculator: PerformanceCalculator
    ) -> None:
        ticker_id = uuid4()
        calculator.update_price(ticker_id, 100.0)

        result = calculator.calculate_holding_performance(
            ticker_id=ticker_id,
            quantity=10.0,
            avg_cost_basis=0.0,
            total_portfolio_value=5000.0,
        )

        assert result is not None
        assert result.unrealized_pnl_pct == 0.0

    def test_calculate_holding_performance_handles_zero_portfolio_value(
        self, calculator: PerformanceCalculator
    ) -> None:
        ticker_id = uuid4()
        calculator.update_price(ticker_id, 100.0)

        result = calculator.calculate_holding_performance(
            ticker_id=ticker_id,
            quantity=10.0,
            avg_cost_basis=80.0,
            total_portfolio_value=0.0,
        )

        assert result is not None
        assert result.weight == 0.0


class TestPerformanceCalculatorPortfolioPerformance:
    def test_calculate_portfolio_performance_single_holding(
        self, calculator: PerformanceCalculator
    ) -> None:
        portfolio_id = uuid4()
        ticker_id = uuid4()
        calculator.update_price(ticker_id, 100.0)
        calculator.set_ticker_sector(ticker_id, "Technology")

        holdings = [(ticker_id, 10.0, 80.0)]
        result = calculator.calculate_portfolio_performance(portfolio_id, holdings)

        assert result is not None
        assert result.portfolio_id == portfolio_id
        assert result.total_market_value == 1000.0
        assert result.total_cost_basis == 800.0
        assert result.total_unrealized_pnl == 200.0
        assert result.total_unrealized_pnl_pct == 25.0
        assert len(result.holdings) == 1
        assert result.sector_allocation["Technology"] == 100.0

    def test_calculate_portfolio_performance_multiple_holdings(
        self, calculator: PerformanceCalculator
    ) -> None:
        portfolio_id = uuid4()
        ticker1 = uuid4()
        ticker2 = uuid4()
        ticker3 = uuid4()

        calculator.update_price(ticker1, 100.0)
        calculator.update_price(ticker2, 50.0)
        calculator.update_price(ticker3, 200.0)
        calculator.set_ticker_sector(ticker1, "Technology")
        calculator.set_ticker_sector(ticker2, "Healthcare")
        calculator.set_ticker_sector(ticker3, "Technology")

        holdings = [
            (ticker1, 10.0, 80.0),  # MV: 1000, cost: 800, P&L: +200
            (ticker2, 20.0, 60.0),  # MV: 1000, cost: 1200, P&L: -200
            (ticker3, 5.0, 150.0),  # MV: 1000, cost: 750, P&L: +250
        ]

        result = calculator.calculate_portfolio_performance(portfolio_id, holdings)

        assert result is not None
        assert result.total_market_value == 3000.0
        assert result.total_cost_basis == 2750.0
        assert result.total_unrealized_pnl == 250.0
        assert abs(result.total_unrealized_pnl_pct - 9.09) < 0.01
        assert len(result.holdings) == 3

        # Each holding should have weight of ~33.33%
        for holding in result.holdings:
            assert abs(holding.weight - 33.33) < 0.01

        # Sector allocation: Technology 66.67%, Healthcare 33.33%
        assert abs(result.sector_allocation["Technology"] - 66.67) < 0.01
        assert abs(result.sector_allocation["Healthcare"] - 33.33) < 0.01

    def test_calculate_portfolio_performance_returns_none_if_missing_price(
        self, calculator: PerformanceCalculator
    ) -> None:
        portfolio_id = uuid4()
        ticker1 = uuid4()
        ticker2 = uuid4()

        calculator.update_price(ticker1, 100.0)
        # ticker2 has no price

        holdings = [(ticker1, 10.0, 80.0), (ticker2, 20.0, 60.0)]

        result = calculator.calculate_portfolio_performance(portfolio_id, holdings)
        assert result is None

    def test_calculate_portfolio_performance_empty_holdings(
        self, calculator: PerformanceCalculator
    ) -> None:
        portfolio_id = uuid4()
        result = calculator.calculate_portfolio_performance(portfolio_id, [])

        assert result is not None
        assert result.total_market_value == 0.0
        assert result.total_cost_basis == 0.0
        assert result.total_unrealized_pnl == 0.0
        assert result.total_unrealized_pnl_pct == 0.0
        assert len(result.holdings) == 0
        assert result.sector_allocation == {}

    def test_calculate_portfolio_performance_unknown_sector(
        self, calculator: PerformanceCalculator
    ) -> None:
        portfolio_id = uuid4()
        ticker_id = uuid4()
        calculator.update_price(ticker_id, 100.0)
        # Not setting a sector for this ticker

        holdings = [(ticker_id, 10.0, 80.0)]
        result = calculator.calculate_portfolio_performance(portfolio_id, holdings)

        assert result is not None
        assert "Unknown" in result.sector_allocation
        assert result.sector_allocation["Unknown"] == 100.0

    def test_calculate_portfolio_performance_handles_zero_cost_basis(
        self, calculator: PerformanceCalculator
    ) -> None:
        portfolio_id = uuid4()
        ticker_id = uuid4()
        calculator.update_price(ticker_id, 100.0)

        holdings = [(ticker_id, 10.0, 0.0)]
        result = calculator.calculate_portfolio_performance(portfolio_id, holdings)

        assert result is not None
        assert result.total_market_value == 1000.0
        assert result.total_cost_basis == 0.0
        assert result.total_unrealized_pnl_pct == 0.0
