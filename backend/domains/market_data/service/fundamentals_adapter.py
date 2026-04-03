import random

from ..models.models import Fundamental


class FundamentalsAdapter:
    def __init__(self) -> None:
        pass

    def generate_mock_fundamental(self, ticker_id: int, period: str) -> Fundamental:
        """
        Generate a mock Fundamental snapshot for a given ticker and reporting period.
        """
        return Fundamental(
            id=random.randint(1, 1_000_000),
            ticker_id=ticker_id,
            period=period,
            revenue=round(random.uniform(1e7, 1e10), 2),
            eps=round(random.uniform(0.1, 10.0), 2),
            pe_ratio=round(random.uniform(5.0, 50.0), 2),
            dividend_yield=round(random.uniform(0.0, 5.0), 2),
            market_cap=round(random.uniform(1e8, 1e12), 2),
        )

    def get_fundamental_snapshot(self, ticker_id: int, period: str) -> Fundamental:
        """
        Return a mock fundamental snapshot for the given ticker and period.
        """
        return self.generate_mock_fundamental(ticker_id, period)
