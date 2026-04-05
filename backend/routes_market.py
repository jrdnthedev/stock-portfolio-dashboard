"""Market data API routes."""

from datetime import date, datetime

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from backend.gateway.formatter import not_found_response, success_response
except ImportError:
    from gateway.formatter import not_found_response, success_response


class PricePoint(BaseModel):
    """Price data for a specific date."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class LatestPrice(BaseModel):
    """Latest price data."""

    ticker: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: str


class Fundamentals(BaseModel):
    """Fundamental data for a ticker."""

    ticker: str
    company_name: str
    sector: str
    industry: str
    market_cap: float
    pe_ratio: float | None
    dividend_yield: float | None
    eps: float | None
    revenue: float | None
    profit_margin: float | None


class Ticker(BaseModel):
    """Ticker information."""

    symbol: str
    name: str
    exchange: str
    sector: str
    asset_class: str


router = APIRouter(prefix="/v1/market", tags=["market"])

# Mock data for demonstration
MOCK_PRICES = {
    "AAPL": [
        {
            "date": "2026-04-01",
            "open": 176.25,
            "high": 178.50,
            "low": 175.80,
            "close": 178.50,
            "volume": 52340000,
        },
        {
            "date": "2026-04-02",
            "open": 178.50,
            "high": 180.25,
            "low": 177.90,
            "close": 179.80,
            "volume": 48920000,
        },
        {
            "date": "2026-04-03",
            "open": 179.80,
            "high": 181.00,
            "low": 178.50,
            "close": 180.25,
            "volume": 51200000,
        },
    ],
    "GOOGL": [
        {
            "date": "2026-04-01",
            "open": 141.15,
            "high": 142.30,
            "low": 140.80,
            "close": 142.30,
            "volume": 28450000,
        },
        {
            "date": "2026-04-02",
            "open": 142.30,
            "high": 143.50,
            "low": 141.90,
            "close": 143.00,
            "volume": 26730000,
        },
    ],
}

MOCK_LATEST_PRICES = {
    "AAPL": {
        "ticker": "AAPL",
        "price": 180.25,
        "change": 1.75,
        "change_percent": 0.98,
        "volume": 51200000,
        "timestamp": "2026-04-05T15:59:00Z",
    },
    "GOOGL": {
        "ticker": "GOOGL",
        "price": 143.00,
        "change": 0.70,
        "change_percent": 0.49,
        "volume": 26730000,
        "timestamp": "2026-04-05T15:59:00Z",
    },
    "MSFT": {
        "ticker": "MSFT",
        "price": 420.15,
        "change": 3.40,
        "change_percent": 0.82,
        "volume": 32100000,
        "timestamp": "2026-04-05T15:59:00Z",
    },
}

MOCK_FUNDAMENTALS = {
    "AAPL": {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 2800000000000,
        "pe_ratio": 28.5,
        "dividend_yield": 0.52,
        "eps": 6.32,
        "revenue": 394328000000,
        "profit_margin": 25.31,
    },
    "GOOGL": {
        "ticker": "GOOGL",
        "company_name": "Alphabet Inc.",
        "sector": "Technology",
        "industry": "Internet Content & Information",
        "market_cap": 1750000000000,
        "pe_ratio": 22.8,
        "dividend_yield": None,
        "eps": 6.26,
        "revenue": 307394000000,
        "profit_margin": 21.16,
    },
    "MSFT": {
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software",
        "market_cap": 3100000000000,
        "pe_ratio": 32.4,
        "dividend_yield": 0.82,
        "eps": 12.97,
        "revenue": 227582000000,
        "profit_margin": 36.88,
    },
}

MOCK_TICKERS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "asset_class": "Stock",
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "asset_class": "Stock",
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "asset_class": "Stock",
    },
    {
        "symbol": "JPM",
        "name": "JPMorgan Chase & Co.",
        "exchange": "NYSE",
        "sector": "Financial",
        "asset_class": "Stock",
    },
    {
        "symbol": "V",
        "name": "Visa Inc.",
        "exchange": "NYSE",
        "sector": "Financial",
        "asset_class": "Stock",
    },
]


@router.get("/prices/{ticker}", response_model=None)
async def get_historical_prices(
    ticker: str,
    from_date: date | None = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: date | None = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
) -> JSONResponse:
    """Get historical price data for a ticker within a date range."""
    ticker_upper = ticker.upper()

    if ticker_upper not in MOCK_PRICES:
        response = not_found_response("Ticker", ticker_upper)
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    prices = MOCK_PRICES[ticker_upper]

    # Filter by date range if provided
    if from_date or to_date:
        filtered_prices = []
        for price in prices:
            price_date = datetime.strptime(str(price["date"]), "%Y-%m-%d").date()
            if from_date and price_date < from_date:
                continue
            if to_date and price_date > to_date:
                continue
            filtered_prices.append(price)
        prices = filtered_prices

    metadata = {
        "ticker": ticker_upper,
        "from": from_date.isoformat() if from_date else None,
        "to": to_date.isoformat() if to_date else None,
        "count": len(prices),
    }

    response = success_response(
        data=prices,
        message=f"Historical prices for {ticker_upper} retrieved successfully",
        metadata=metadata,
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/prices/{ticker}/latest", response_model=None)
async def get_latest_price(ticker: str) -> JSONResponse:
    """Get the latest price data for a ticker."""
    ticker_upper = ticker.upper()

    if ticker_upper not in MOCK_LATEST_PRICES:
        response = not_found_response("Ticker", ticker_upper)
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    latest_price = MOCK_LATEST_PRICES[ticker_upper]

    response = success_response(
        data=latest_price,
        message=f"Latest price for {ticker_upper} retrieved successfully",
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/fundamentals/{ticker}", response_model=None)
async def get_fundamentals(ticker: str) -> JSONResponse:
    """Get fundamental data for a ticker."""
    ticker_upper = ticker.upper()

    if ticker_upper not in MOCK_FUNDAMENTALS:
        response = not_found_response("Ticker", ticker_upper)
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    fundamentals = MOCK_FUNDAMENTALS[ticker_upper]

    response = success_response(
        data=fundamentals,
        message=f"Fundamentals for {ticker_upper} retrieved successfully",
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/tickers", response_model=None)
async def get_tickers(
    sector: str | None = Query(None, description="Filter by sector"),
    exchange: str | None = Query(None, description="Filter by exchange"),
    asset_class: str | None = Query(None, description="Filter by asset class"),
) -> JSONResponse:
    """Get list of available tickers with optional filters."""
    tickers = MOCK_TICKERS

    # Apply filters
    if sector:
        tickers = [t for t in tickers if t["sector"].lower() == sector.lower()]
    if exchange:
        tickers = [t for t in tickers if t["exchange"].upper() == exchange.upper()]
    if asset_class:
        tickers = [t for t in tickers if t["asset_class"].lower() == asset_class.lower()]

    metadata = {
        "count": len(tickers),
        "filters": {
            "sector": sector,
            "exchange": exchange,
            "asset_class": asset_class,
        },
    }

    response = success_response(
        data=tickers,
        message="Tickers retrieved successfully",
        metadata=metadata,
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)
