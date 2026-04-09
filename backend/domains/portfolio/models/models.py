from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class Portfolio(BaseModel):
    id: UUID
    name: str
    owner: str
    currency: str
    created_at: datetime


class Holding(BaseModel):
    id: UUID
    portfolio_id: UUID
    ticker_id: UUID
    quantity: float
    avg_cost_basis: float
    opened_at: datetime


class PerformanceSnapshot(BaseModel):
    id: UUID
    portfolio_id: UUID
    date: date
    total_value: float
    daily_return: float
    cumulative_return: float


class AlertConfig(BaseModel):
    """Configuration for price movement alerts on a holding."""

    id: UUID
    portfolio_id: UUID
    ticker_id: UUID
    threshold_pct: float  # Alert when price changes by this percentage
    enabled: bool = True


class PriceAlert(BaseModel):
    """Alert triggered when price movement exceeds threshold."""

    ticker_id: UUID
    portfolio_id: UUID
    previous_price: float
    current_price: float
    change_pct: float
    threshold_pct: float
    timestamp: datetime
