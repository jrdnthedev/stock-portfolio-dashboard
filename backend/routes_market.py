"""Market data API routes with database integration."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import PricePoint, Ticker
from backend.gateway.formatter import not_found_response, success_response


class PricePointResponse(BaseModel):
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


class TickerResponse(BaseModel):
    """Ticker information."""

    symbol: str
    name: str
    exchange: str
    sector: str
    asset_class: str


router = APIRouter(prefix="/v1/market", tags=["market"])


@router.get("/prices/{ticker}", response_model=None)
async def get_historical_prices(
    ticker: str,
    from_date: date | None = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: date | None = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get historical price data for a ticker within a date range."""
    ticker_upper = ticker.upper()

    # Find ticker
    ticker_obj = db.query(Ticker).filter(Ticker.symbol == ticker_upper).first()

    if not ticker_obj:
        response = not_found_response("Ticker", ticker_upper)
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Query price data
    query = db.query(PricePoint).filter(PricePoint.ticker_id == ticker_obj.id)

    if from_date:
        query = query.filter(PricePoint.date >= from_date)
    if to_date:
        query = query.filter(PricePoint.date <= to_date)

    prices = query.order_by(PricePoint.date).all()

    prices_data = [
        {
            "date": price.date.isoformat(),
            "open": price.open_price,
            "high": price.high,
            "low": price.low,
            "close": price.close,
            "volume": price.volume,
        }
        for price in prices
    ]

    metadata = {
        "ticker": ticker_upper,
        "from": from_date.isoformat() if from_date else None,
        "to": to_date.isoformat() if to_date else None,
        "count": len(prices_data),
    }

    response = success_response(
        data=prices_data,
        message=f"Historical prices for {ticker_upper} retrieved successfully",
        metadata=metadata,
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/prices/{ticker}/latest", response_model=None)
async def get_latest_price(ticker: str, db: Session = Depends(get_db)) -> JSONResponse:
    """Get the latest price data for a ticker."""
    ticker_upper = ticker.upper()

    # Find ticker
    ticker_obj = db.query(Ticker).filter(Ticker.symbol == ticker_upper).first()

    if not ticker_obj:
        response = not_found_response("Ticker", ticker_upper)
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Get latest price
    latest_price = (
        db.query(PricePoint)
        .filter(PricePoint.ticker_id == ticker_obj.id)
        .order_by(desc(PricePoint.date))
        .first()
    )

    if not latest_price:
        response = not_found_response("Price data", ticker_upper)
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Get previous price for change calculation
    previous_price = (
        db.query(PricePoint)
        .filter(and_(PricePoint.ticker_id == ticker_obj.id, PricePoint.date < latest_price.date))
        .order_by(desc(PricePoint.date))
        .first()
    )

    if previous_price:
        change = latest_price.close - previous_price.close
        change_percent = (change / previous_price.close * 100) if previous_price.close > 0 else 0.0
    else:
        change = 0.0
        change_percent = 0.0

    latest_price_data = {
        "ticker": ticker_upper,
        "price": latest_price.close,
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "volume": latest_price.volume,
        "timestamp": datetime.combine(latest_price.date, datetime.min.time()).isoformat() + "Z",
    }

    response = success_response(
        data=latest_price_data,
        message=f"Latest price for {ticker_upper} retrieved successfully",
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/fundamentals/{ticker}", response_model=None)
async def get_fundamentals(ticker: str, db: Session = Depends(get_db)) -> JSONResponse:
    """Get fundamental data for a ticker."""
    ticker_upper = ticker.upper()

    # Find ticker
    ticker_obj = db.query(Ticker).filter(Ticker.symbol == ticker_upper).first()

    if not ticker_obj:
        response = not_found_response("Ticker", ticker_upper)
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Mock fundamentals data (in real implementation, would come from separate table or service)
    fundamentals = {
        "ticker": ticker_upper,
        "company_name": ticker_obj.company_name,
        "sector": ticker_obj.sector,
        "industry": "Technology",  # Mock value
        "market_cap": 2800000000000.0,  # Mock value
        "pe_ratio": 28.5,  # Mock value
        "dividend_yield": 0.52,  # Mock value
        "eps": 6.32,  # Mock value
        "revenue": 394328000000.0,  # Mock value
        "profit_margin": 25.31,  # Mock value
    }

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
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get list of available tickers with optional filters."""
    query = db.query(Ticker)

    # Apply filters
    if sector:
        query = query.filter(Ticker.sector.ilike(sector))
    if exchange:
        query = query.filter(Ticker.exchange.ilike(exchange))
    if asset_class:
        query = query.filter(Ticker.asset_class.ilike(asset_class))

    tickers = query.all()

    tickers_data = [
        {
            "symbol": t.symbol,
            "name": t.company_name,
            "exchange": t.exchange,
            "sector": t.sector,
            "asset_class": t.asset_class,
        }
        for t in tickers
    ]

    metadata = {
        "count": len(tickers_data),
        "filters": {
            "sector": sector,
            "exchange": exchange,
            "asset_class": asset_class,
        },
    }

    response = success_response(
        data=tickers_data,
        message="Tickers retrieved successfully",
        metadata=metadata,
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)
