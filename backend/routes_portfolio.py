"""Portfolio management API routes with database integration."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from backend.database.database import get_db
from backend.database.models import Holding, Portfolio, Ticker
from backend.gateway.cache import get_cache_service
from backend.gateway.formatter import not_found_response, success_response
from backend.middleware.auth import get_current_active_user


class PortfolioResponse(BaseModel):
    """Portfolio response model."""

    id: str
    name: str
    description: str | None
    created_at: str
    updated_at: str
    total_value: float
    total_cost: float
    total_gain: float
    total_gain_percent: float


class HoldingResponse(BaseModel):
    """Holding response model."""

    id: str
    portfolio_id: str
    ticker: dict[str, str]
    quantity: float
    average_cost: float
    current_price: float
    total_cost: float
    total_value: float
    gain: float
    gain_percent: float
    purchased_at: str
    updated_at: str


class HoldingCreate(BaseModel):
    """Create holding request."""

    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    quantity: float = Field(..., gt=0, description="Number of shares")
    average_cost: float = Field(..., gt=0, description="Average cost per share")
    purchased_at: str | None = Field(None, description="Purchase date (YYYY-MM-DD)")


class HoldingUpdate(BaseModel):
    """Update holding request."""

    quantity: float | None = Field(None, gt=0, description="Number of shares")
    average_cost: float | None = Field(None, gt=0, description="Average cost per share")


class PerformanceMetric(BaseModel):
    """Performance metric for a specific date."""

    date: str
    value: float
    gain: float
    gain_percent: float


class AllocationItem(BaseModel):
    """Portfolio allocation item."""

    ticker: str
    value: float
    percentage: float
    sector: str


router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/", response_model=None)
async def list_portfolios(
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """List all portfolios for the authenticated user."""
    # Filter portfolios by the authenticated user's email
    user_email = current_user["sub"]
    portfolios = db.query(Portfolio).filter(Portfolio.owner == user_email).all()

    portfolio_list = []
    for portfolio in portfolios:
        portfolio_list.append(
            {
                "id": str(portfolio.id),
                "name": portfolio.name,
                "description": None,
                "created_at": portfolio.created_at.isoformat(),
                # "updated_at": portfolio.updated_at.isoformat(),
            }
        )

    return JSONResponse(
        content=success_response(portfolio_list),
        status_code=status.HTTP_200_OK,
    )


@router.get("/{id}", response_model=None)
async def get_portfolio(
    id: UUID,
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get portfolio details by ID for the authenticated user."""
    user_email = current_user["sub"]
    portfolio = (
        db.query(Portfolio).filter(Portfolio.id == id, Portfolio.owner == user_email).first()
    )

    if not portfolio:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Calculate portfolio totals from holdings
    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == id)
        .options(joinedload(Holding.ticker))
        .all()
    )

    total_value = 0.0
    total_cost = 0.0

    for holding in holdings:
        # Mock current price (in real implementation, fetch from price service)
        current_price = 180.25  # Mock price
        total_cost += holding.quantity * holding.avg_cost_basis
        total_value += holding.quantity * current_price

    total_gain = total_value - total_cost
    total_gain_percent = (total_gain / total_cost * 100) if total_cost > 0 else 0.0

    portfolio_data = {
        "id": str(portfolio.id),
        "name": portfolio.name,
        "owner": portfolio.owner,
        "description": None,  # Add description field to model if needed
        "created_at": portfolio.created_at.isoformat() + "Z",
        "updated_at": portfolio.created_at.isoformat() + "Z",  # Add updated_at field if needed
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_gain": round(total_gain, 2),
        "total_gain_percent": round(total_gain_percent, 2),
    }

    response = success_response(
        data=portfolio_data,
        message=f"Portfolio {id} retrieved successfully",
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/{id}/holdings", response_model=None)
async def get_holdings(
    id: UUID,
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get all holdings for a portfolio owned by the authenticated user."""
    user_email = current_user["sub"]
    portfolio = (
        db.query(Portfolio).filter(Portfolio.id == id, Portfolio.owner == user_email).first()
    )

    if not portfolio:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == id)
        .options(joinedload(Holding.ticker))
        .all()
    )

    holdings_data = []
    total_value = 0.0
    total_cost = 0.0

    for holding in holdings:
        # Mock current price (in real implementation, fetch from price service)
        current_price = 180.25  # Mock price
        total_cost_holding = holding.quantity * holding.avg_cost_basis
        total_value_holding = holding.quantity * current_price
        gain = total_value_holding - total_cost_holding
        gain_percent = (gain / total_cost_holding * 100) if total_cost_holding > 0 else 0.0

        total_value += total_value_holding
        total_cost += total_cost_holding

        holdings_data.append(
            {
                "id": str(holding.id),
                "portfolio_id": str(holding.portfolio_id),
                "ticker": {
                    "symbol": holding.ticker.symbol,
                    "name": holding.ticker.company_name,
                },
                "quantity": holding.quantity,
                "avg_cost_basis": holding.avg_cost_basis,
                "current_price": current_price,
                "total_cost": round(total_cost_holding, 2),
                "total_value": round(total_value_holding, 2),
                "gain": round(gain, 2),
                "gain_percent": round(gain_percent, 2),
                "purchased_at": holding.opened_at.isoformat() + "Z",
                "updated_at": holding.opened_at.isoformat() + "Z",
            }
        )

    metadata = {
        "portfolio_id": str(id),
        "count": len(holdings_data),
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
    }

    response = success_response(
        data=holdings_data,
        message=f"Holdings for portfolio {id} retrieved successfully",
        metadata=metadata,
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/{id}/performance", response_model=None)
async def get_performance(
    id: UUID,
    from_date: date | None = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: date | None = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get portfolio performance metrics over a date range for the authenticated user."""
    user_email = current_user["sub"]
    portfolio = (
        db.query(Portfolio).filter(Portfolio.id == id, Portfolio.owner == user_email).first()
    )

    if not portfolio:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Mock performance data (in real implementation, query PerformanceSnapshot table)
    performance: list[dict] = []

    metadata = {
        "portfolio_id": str(id),
        "from": from_date.isoformat() if from_date else None,
        "to": to_date.isoformat() if to_date else None,
        "count": len(performance),
    }

    response = success_response(
        data=performance,
        message=f"Performance for portfolio {id} retrieved successfully",
        metadata=metadata,
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/{id}/allocation", response_model=None)
async def get_allocation(
    id: UUID,
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get portfolio allocation breakdown for the authenticated user."""
    user_email = current_user["sub"]
    portfolio = (
        db.query(Portfolio).filter(Portfolio.id == id, Portfolio.owner == user_email).first()
    )

    if not portfolio:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == id)
        .options(joinedload(Holding.ticker))
        .all()
    )

    allocation = []
    total_value = 0.0

    for holding in holdings:
        current_price = 180.25  # Mock price
        value = holding.quantity * current_price
        total_value += value

        allocation.append(
            {
                "ticker": holding.ticker.symbol,
                "value": value,
                "sector": holding.ticker.sector,
            }
        )

    # Calculate percentages
    for item in allocation:
        item["percentage"] = round(
            (item["value"] / total_value * 100) if total_value > 0 else 0.0, 2
        )
        item["value"] = round(item["value"], 2)

    metadata = {
        "portfolio_id": str(id),
        "total_value": round(total_value, 2),
        "item_count": len(allocation),
    }

    response = success_response(
        data=allocation,
        message=f"Allocation for portfolio {id} retrieved successfully",
        metadata=metadata,
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.post("/{id}/holdings", response_model=None)
async def create_holding(
    id: UUID,
    holding: HoldingCreate = Body(...),
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Add a new holding to the portfolio owned by the authenticated user."""
    user_email = current_user["sub"]
    portfolio = (
        db.query(Portfolio).filter(Portfolio.id == id, Portfolio.owner == user_email).first()
    )

    if not portfolio:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Find ticker
    ticker = db.query(Ticker).filter(Ticker.symbol == holding.ticker.upper()).first()

    if not ticker:
        response = not_found_response("Ticker", holding.ticker.upper())
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Create holding
    purchased_at = (
        datetime.fromisoformat(holding.purchased_at.replace("Z", ""))
        if holding.purchased_at
        else datetime.now()
    )

    new_holding = Holding(
        portfolio_id=id,
        ticker_id=ticker.id,
        quantity=holding.quantity,
        avg_cost_basis=holding.average_cost,
        opened_at=purchased_at,
    )

    db.add(new_holding)
    db.commit()
    db.refresh(new_holding)

    # Calculate values
    current_price = 180.25  # Mock price
    total_cost = new_holding.quantity * new_holding.avg_cost_basis
    total_value = new_holding.quantity * current_price
    gain = total_value - total_cost
    gain_percent = (gain / total_cost * 100) if total_cost > 0 else 0.0

    holding_data = {
        "id": str(new_holding.id),
        "portfolio_id": str(new_holding.portfolio_id),
        "ticker": {
            "symbol": ticker.symbol,
            "name": ticker.company_name,
        },
        "quantity": new_holding.quantity,
        "avg_cost_basis": new_holding.avg_cost_basis,
        "current_price": current_price,
        "total_cost": round(total_cost, 2),
        "total_value": round(total_value, 2),
        "gain": round(gain, 2),
        "gain_percent": round(gain_percent, 2),
        "purchased_at": new_holding.opened_at.isoformat() + "Z",
        "updated_at": new_holding.opened_at.isoformat() + "Z",
    }

    # Invalidate caches
    cache = get_cache_service()
    cache.delete(f"portfolio:{id}:holdings")
    cache.delete(f"portfolio:{id}:performance")
    cache.delete(f"portfolio:{id}:allocation")
    cache.delete(f"portfolio:{id}")

    response = success_response(
        data=holding_data,
        message=f"Holding created successfully in portfolio {id}",
    )
    return JSONResponse(content=response, status_code=status.HTTP_201_CREATED)


@router.put("/{id}/holdings/{hid}", response_model=None)
async def update_holding(
    id: UUID,
    hid: UUID,
    data: HoldingUpdate = Body(...),
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Update an existing holding for the authenticated user."""
    user_email = current_user["sub"]
    portfolio = (
        db.query(Portfolio).filter(Portfolio.id == id, Portfolio.owner == user_email).first()
    )

    if not portfolio:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    holding = (
        db.query(Holding)
        .filter(Holding.id == hid, Holding.portfolio_id == id)
        .options(joinedload(Holding.ticker))
        .first()
    )

    if not holding:
        response = not_found_response("Holding", str(hid))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Update fields
    if data.quantity is not None:
        holding.quantity = data.quantity
    if data.average_cost is not None:
        holding.avg_cost_basis = data.average_cost

    db.commit()
    db.refresh(holding)

    # Calculate values
    current_price = 180.25  # Mock price
    total_cost = holding.quantity * holding.avg_cost_basis
    total_value = holding.quantity * current_price
    gain = total_value - total_cost
    gain_percent = (gain / total_cost * 100) if total_cost > 0 else 0.0

    holding_data = {
        "id": str(holding.id),
        "portfolio_id": str(holding.portfolio_id),
        "ticker": {
            "symbol": holding.ticker.symbol,
            "name": holding.ticker.company_name,
        },
        "quantity": holding.quantity,
        "avg_cost_basis": holding.avg_cost_basis,
        "current_price": current_price,
        "total_cost": round(total_cost, 2),
        "total_value": round(total_value, 2),
        "gain": round(gain, 2),
        "gain_percent": round(gain_percent, 2),
        "purchased_at": holding.opened_at.isoformat() + "Z",
        "updated_at": holding.opened_at.isoformat() + "Z",
    }

    # Invalidate caches
    cache = get_cache_service()
    cache.delete(f"portfolio:{id}:holdings")
    cache.delete(f"portfolio:{id}:performance")
    cache.delete(f"portfolio:{id}:allocation")
    cache.delete(f"portfolio:{id}")

    response = success_response(
        data=holding_data,
        message=f"Holding {hid} updated successfully",
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.delete("/{id}/holdings/{hid}", response_model=None)
async def delete_holding(
    id: UUID,
    hid: UUID,
    current_user: dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Delete a holding from the portfolio for the authenticated user."""
    user_email = current_user["sub"]
    portfolio = (
        db.query(Portfolio).filter(Portfolio.id == id, Portfolio.owner == user_email).first()
    )

    if not portfolio:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    holding = db.query(Holding).filter(Holding.id == hid, Holding.portfolio_id == id).first()

    if not holding:
        response = not_found_response("Holding", str(hid))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    db.delete(holding)
    db.commit()

    # Invalidate caches
    cache = get_cache_service()
    cache.delete(f"portfolio:{id}:holdings")
    cache.delete(f"portfolio:{id}:performance")
    cache.delete(f"portfolio:{id}:allocation")
    cache.delete(f"portfolio:{id}")

    response = success_response(
        data={"id": str(hid), "deleted": True},
        message=f"Holding {hid} deleted successfully",
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)
