# This file was moved from market_data_models.py for consistency and to avoid mypy duplicate module errors.
from pydantic import BaseModel, Field


# Ticker model
class Ticker(BaseModel):
    id: int = Field(..., description="Unique identifier for the ticker")
    symbol: str = Field(..., description="Stock ticker symbol, e.g., AAPL")
    company_name: str = Field(..., description="Full company name")
    exchange: str = Field(..., description="Exchange where the stock is listed")
    sector: str = Field(..., description="Sector of the company")
    asset_class: str = Field(..., description="Asset class, e.g., Equity")


# PricePoint model
class PricePoint(BaseModel):
    id: int = Field(..., description="Unique identifier for the price point")
    ticker_id: int = Field(..., description="Reference to Ticker id")
    date: str = Field(..., description="Date of the price point (YYYY-MM-DD)")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")


# Fundamental model
class Fundamental(BaseModel):
    id: int = Field(..., description="Unique identifier for the fundamental record")
    ticker_id: int = Field(..., description="Reference to Ticker id")
    period: str = Field(..., description="Reporting period (e.g., Q1 2024)")
    revenue: float = Field(..., description="Total revenue for the period")
    eps: float = Field(..., description="Earnings per share")
    pe_ratio: float = Field(..., description="Price to earnings ratio")
    dividend_yield: float = Field(..., description="Dividend yield as a percentage")
    market_cap: float = Field(..., description="Market capitalization")
