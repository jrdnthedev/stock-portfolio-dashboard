from uuid import UUID

from pydantic import BaseModel


class HoldingPerformance(BaseModel):
    """Performance metrics for a single holding."""

    ticker_id: UUID
    quantity: float
    avg_cost_basis: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight: float  # Portfolio weight percentage


class PortfolioPerformance(BaseModel):
    """Aggregate performance metrics for an entire portfolio."""

    portfolio_id: UUID
    total_market_value: float
    total_cost_basis: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    holdings: list[HoldingPerformance]
    sector_allocation: dict[str, float]  # sector -> weight percentage


class PerformanceCalculator:
    """
    Joins holdings with current prices to compute market value, unrealized P&L,
    weights, and sector allocation.
    """

    def __init__(self) -> None:
        # Cache for current prices: ticker_id -> price
        self.current_prices: dict[UUID, float] = {}
        # Cache for sector mapping: ticker_id -> sector
        self.ticker_sectors: dict[UUID, str] = {}

    def update_price(self, ticker_id: UUID, price: float) -> None:
        """Update the current price for a ticker."""
        self.current_prices[ticker_id] = price

    def set_ticker_sector(self, ticker_id: UUID, sector: str) -> None:
        """Set the sector for a ticker."""
        self.ticker_sectors[ticker_id] = sector

    def calculate_holding_performance(
        self, ticker_id: UUID, quantity: float, avg_cost_basis: float, total_portfolio_value: float
    ) -> HoldingPerformance | None:
        """Calculate performance metrics for a single holding."""
        current_price = self.current_prices.get(ticker_id)
        if current_price is None:
            return None

        market_value = quantity * current_price
        cost_basis = quantity * avg_cost_basis
        unrealized_pnl = market_value - cost_basis
        unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis != 0 else 0.0
        weight = (market_value / total_portfolio_value * 100) if total_portfolio_value != 0 else 0.0

        return HoldingPerformance(
            ticker_id=ticker_id,
            quantity=quantity,
            avg_cost_basis=avg_cost_basis,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            weight=weight,
        )

    def calculate_portfolio_performance(
        self, portfolio_id: UUID, holdings: list[tuple[UUID, float, float]]
    ) -> PortfolioPerformance | None:
        """
        Calculate aggregate performance for an entire portfolio.

        Args:
            portfolio_id: UUID of the portfolio
            holdings: List of (ticker_id, quantity, avg_cost_basis) tuples

        Returns:
            PortfolioPerformance or None if any required prices are missing
        """
        # First pass: calculate total market value
        total_market_value = 0.0
        total_cost_basis = 0.0

        for ticker_id, quantity, avg_cost_basis in holdings:
            current_price = self.current_prices.get(ticker_id)
            if current_price is None:
                return None  # Missing price data

            market_value = quantity * current_price
            cost_basis = quantity * avg_cost_basis
            total_market_value += market_value
            total_cost_basis += cost_basis

        # Second pass: calculate individual holding performance with weights
        holding_performances: list[HoldingPerformance] = []
        sector_values: dict[str, float] = {}

        for ticker_id, quantity, avg_cost_basis in holdings:
            holding_perf = self.calculate_holding_performance(
                ticker_id, quantity, avg_cost_basis, total_market_value
            )
            if holding_perf:
                holding_performances.append(holding_perf)

                # Aggregate sector allocation
                sector = self.ticker_sectors.get(ticker_id, "Unknown")
                sector_values[sector] = sector_values.get(sector, 0.0) + holding_perf.market_value

        # Calculate sector allocation percentages
        sector_allocation = {
            sector: (value / total_market_value * 100) if total_market_value != 0 else 0.0
            for sector, value in sector_values.items()
        }

        total_unrealized_pnl = total_market_value - total_cost_basis
        total_unrealized_pnl_pct = (
            (total_unrealized_pnl / total_cost_basis * 100) if total_cost_basis != 0 else 0.0
        )

        return PortfolioPerformance(
            portfolio_id=portfolio_id,
            total_market_value=total_market_value,
            total_cost_basis=total_cost_basis,
            total_unrealized_pnl=total_unrealized_pnl,
            total_unrealized_pnl_pct=total_unrealized_pnl_pct,
            holdings=holding_performances,
            sector_allocation=sector_allocation,
        )
