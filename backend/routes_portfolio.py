"""Portfolio management API routes."""

from datetime import date, datetime
from typing import Any, cast

from fastapi import APIRouter, Body, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    from backend.gateway.cache import get_cache_service
    from backend.gateway.formatter import not_found_response, success_response
except ImportError:
    from gateway.cache import get_cache_service
    from gateway.formatter import not_found_response, success_response


class Portfolio(BaseModel):
    """Portfolio model."""

    id: int
    name: str
    description: str | None
    created_at: str
    updated_at: str
    total_value: float
    total_cost: float
    total_gain: float
    total_gain_percent: float


class Holding(BaseModel):
    """Holding model."""

    id: int
    portfolio_id: int
    ticker: str
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


router = APIRouter(prefix="/v1/portfolio", tags=["portfolio"])

# Mock data for demonstration
MOCK_PORTFOLIOS = {
    1: {
        "id": 1,
        "name": "Growth Portfolio",
        "description": "Technology and growth stocks",
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2026-04-05T15:00:00Z",
        "total_value": 125750.00,
        "total_cost": 100000.00,
        "total_gain": 25750.00,
        "total_gain_percent": 25.75,
    },
    2: {
        "id": 2,
        "name": "Dividend Portfolio",
        "description": "Income-focused dividend stocks",
        "created_at": "2025-06-20T14:00:00Z",
        "updated_at": "2026-04-05T15:00:00Z",
        "total_value": 82300.00,
        "total_cost": 75000.00,
        "total_gain": 7300.00,
        "total_gain_percent": 9.73,
    },
}

MOCK_HOLDINGS: dict[int, list[dict[str, Any]]] = {
    1: [
        {
            "id": 101,
            "portfolio_id": 1,
            "ticker": "AAPL",
            "quantity": 100.0,
            "average_cost": 150.00,
            "current_price": 180.25,
            "total_cost": 15000.00,
            "total_value": 18025.00,
            "gain": 3025.00,
            "gain_percent": 20.17,
            "purchased_at": "2025-01-15T10:30:00Z",
            "updated_at": "2026-04-05T15:00:00Z",
        },
        {
            "id": 102,
            "portfolio_id": 1,
            "ticker": "GOOGL",
            "quantity": 200.0,
            "average_cost": 130.00,
            "current_price": 143.00,
            "total_cost": 26000.00,
            "total_value": 28600.00,
            "gain": 2600.00,
            "gain_percent": 10.00,
            "purchased_at": "2025-02-10T11:00:00Z",
            "updated_at": "2026-04-05T15:00:00Z",
        },
        {
            "id": 103,
            "portfolio_id": 1,
            "ticker": "MSFT",
            "quantity": 140.0,
            "average_cost": 420.71,
            "current_price": 420.15,
            "total_cost": 58899.40,
            "total_value": 58821.00,
            "gain": -78.40,
            "gain_percent": -0.13,
            "purchased_at": "2025-03-05T09:45:00Z",
            "updated_at": "2026-04-05T15:00:00Z",
        },
    ],
    2: [
        {
            "id": 201,
            "portfolio_id": 2,
            "ticker": "JPM",
            "quantity": 150.0,
            "average_cost": 165.00,
            "current_price": 178.50,
            "total_cost": 24750.00,
            "total_value": 26775.00,
            "gain": 2025.00,
            "gain_percent": 8.18,
            "purchased_at": "2025-06-20T14:00:00Z",
            "updated_at": "2026-04-05T15:00:00Z",
        },
        {
            "id": 202,
            "portfolio_id": 2,
            "ticker": "V",
            "quantity": 180.0,
            "average_cost": 279.17,
            "current_price": 308.47,
            "total_cost": 50250.00,
            "total_value": 55525.00,
            "gain": 5275.00,
            "gain_percent": 10.50,
            "purchased_at": "2025-07-10T13:30:00Z",
            "updated_at": "2026-04-05T15:00:00Z",
        },
    ],
}

MOCK_PERFORMANCE = {
    1: [
        {"date": "2026-04-01", "value": 124500.00, "gain": 24500.00, "gain_percent": 24.50},
        {"date": "2026-04-02", "value": 125100.00, "gain": 25100.00, "gain_percent": 25.10},
        {"date": "2026-04-03", "value": 125300.00, "gain": 25300.00, "gain_percent": 25.30},
        {"date": "2026-04-04", "value": 125600.00, "gain": 25600.00, "gain_percent": 25.60},
        {"date": "2026-04-05", "value": 125750.00, "gain": 25750.00, "gain_percent": 25.75},
    ],
    2: [
        {"date": "2026-04-01", "value": 81800.00, "gain": 6800.00, "gain_percent": 9.07},
        {"date": "2026-04-02", "value": 82000.00, "gain": 7000.00, "gain_percent": 9.33},
        {"date": "2026-04-03", "value": 82150.00, "gain": 7150.00, "gain_percent": 9.53},
        {"date": "2026-04-04", "value": 82250.00, "gain": 7250.00, "gain_percent": 9.67},
        {"date": "2026-04-05", "value": 82300.00, "gain": 7300.00, "gain_percent": 9.73},
    ],
}

MOCK_ALLOCATIONS = {
    1: [
        {"ticker": "AAPL", "value": 18025.00, "percentage": 14.33, "sector": "Technology"},
        {"ticker": "GOOGL", "value": 28600.00, "percentage": 22.74, "sector": "Technology"},
        {"ticker": "MSFT", "value": 58821.00, "percentage": 46.77, "sector": "Technology"},
        {"ticker": "CASH", "value": 20304.00, "percentage": 16.16, "sector": "Cash"},
    ],
    2: [
        {"ticker": "JPM", "value": 26775.00, "percentage": 32.54, "sector": "Financial"},
        {"ticker": "V", "value": 55525.00, "percentage": 67.46, "sector": "Financial"},
    ],
}

# Counter for generating new IDs
_next_holding_id = 300


@router.get("/{id}", response_model=None)
async def get_portfolio(id: int) -> JSONResponse:
    """Get portfolio details by ID."""
    if id not in MOCK_PORTFOLIOS:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    portfolio = MOCK_PORTFOLIOS[id]
    response = success_response(
        data=portfolio,
        message=f"Portfolio {id} retrieved successfully",
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/{id}/holdings", response_model=None)
async def get_holdings(id: int) -> JSONResponse:
    """Get all holdings for a portfolio."""
    if id not in MOCK_PORTFOLIOS:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    holdings = MOCK_HOLDINGS.get(id, [])
    metadata = {
        "portfolio_id": id,
        "count": len(holdings),
        "total_value": sum(h["total_value"] for h in holdings),
        "total_cost": sum(h["total_cost"] for h in holdings),
    }

    response = success_response(
        data=holdings,
        message=f"Holdings for portfolio {id} retrieved successfully",
        metadata=metadata,
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.get("/{id}/performance", response_model=None)
async def get_performance(
    id: int,
    from_date: date | None = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: date | None = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
) -> JSONResponse:
    """Get portfolio performance metrics over a date range."""
    if id not in MOCK_PORTFOLIOS:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    performance = MOCK_PERFORMANCE.get(id, [])

    # Filter by date range if provided
    if from_date or to_date:
        filtered_performance = []
        for metric in performance:
            metric_date = datetime.strptime(str(metric["date"]), "%Y-%m-%d").date()
            if from_date and metric_date < from_date:
                continue
            if to_date and metric_date > to_date:
                continue
            filtered_performance.append(metric)
        performance = filtered_performance

    metadata = {
        "portfolio_id": id,
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
async def get_allocation(id: int) -> JSONResponse:
    """Get portfolio allocation breakdown."""
    if id not in MOCK_PORTFOLIOS:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    allocation = MOCK_ALLOCATIONS.get(id, [])
    total_value = sum(cast(float, item["value"]) for item in allocation)

    metadata = {
        "portfolio_id": id,
        "total_value": total_value,
        "item_count": len(allocation),
    }

    response = success_response(
        data=allocation,
        message=f"Allocation for portfolio {id} retrieved successfully",
        metadata=metadata,
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.post("/{id}/holdings", response_model=None)
async def create_holding(id: int, holding: HoldingCreate = Body(...)) -> JSONResponse:
    """Add a new holding to the portfolio."""
    global _next_holding_id

    if id not in MOCK_PORTFOLIOS:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Calculate derived values
    total_cost = holding.quantity * holding.average_cost
    current_price = 180.25  # Mock current price
    total_value = holding.quantity * current_price
    gain = total_value - total_cost
    gain_percent = (gain / total_cost) * 100 if total_cost > 0 else 0.0

    new_holding = {
        "id": _next_holding_id,
        "portfolio_id": id,
        "ticker": holding.ticker.upper(),
        "quantity": holding.quantity,
        "average_cost": holding.average_cost,
        "current_price": current_price,
        "total_cost": total_cost,
        "total_value": total_value,
        "gain": gain,
        "gain_percent": gain_percent,
        "purchased_at": holding.purchased_at or datetime.now().isoformat() + "Z",
        "updated_at": datetime.now().isoformat() + "Z",
    }

    # Add to mock data
    if id not in MOCK_HOLDINGS:
        MOCK_HOLDINGS[id] = []
    MOCK_HOLDINGS[id].append(new_holding)

    _next_holding_id += 1

    # Invalidate caches
    cache = get_cache_service()
    cache.delete(f"portfolio:{id}:holdings")
    cache.delete(f"portfolio:{id}:performance")
    cache.delete(f"portfolio:{id}:allocation")
    cache.delete(f"portfolio:{id}")

    response = success_response(
        data=new_holding,
        message=f"Holding created successfully in portfolio {id}",
    )
    return JSONResponse(content=response, status_code=status.HTTP_201_CREATED)


@router.put("/{id}/holdings/{hid}", response_model=None)
async def update_holding(
    id: int, hid: int, holding_update: HoldingUpdate = Body(...)
) -> JSONResponse:
    """Update an existing holding."""
    if id not in MOCK_PORTFOLIOS:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    holdings = MOCK_HOLDINGS.get(id, [])
    holding = next((h for h in holdings if h["id"] == hid), None)

    if not holding:
        response = not_found_response("Holding", str(hid))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Update fields
    if holding_update.quantity is not None:
        holding["quantity"] = holding_update.quantity
    if holding_update.average_cost is not None:
        holding["average_cost"] = holding_update.average_cost

    # Recalculate derived values
    holding["total_cost"] = holding["quantity"] * holding["average_cost"]
    holding["total_value"] = holding["quantity"] * holding["current_price"]
    holding["gain"] = holding["total_value"] - holding["total_cost"]
    holding["gain_percent"] = (
        (holding["gain"] / holding["total_cost"]) * 100 if holding["total_cost"] > 0 else 0.0
    )
    holding["updated_at"] = datetime.now().isoformat() + "Z"

    # Invalidate caches
    cache = get_cache_service()
    cache.delete(f"portfolio:{id}:holdings")
    cache.delete(f"portfolio:{id}:performance")
    cache.delete(f"portfolio:{id}:allocation")
    cache.delete(f"portfolio:{id}")

    response = success_response(
        data=holding,
        message=f"Holding {hid} updated successfully",
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@router.delete("/{id}/holdings/{hid}", response_model=None)
async def delete_holding(id: int, hid: int) -> JSONResponse:
    """Delete a holding from the portfolio."""
    if id not in MOCK_PORTFOLIOS:
        response = not_found_response("Portfolio", str(id))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    holdings = MOCK_HOLDINGS.get(id, [])
    holding = next((h for h in holdings if h["id"] == hid), None)

    if not holding:
        response = not_found_response("Holding", str(hid))
        return JSONResponse(content=response, status_code=status.HTTP_404_NOT_FOUND)

    # Remove holding
    MOCK_HOLDINGS[id] = [h for h in holdings if h["id"] != hid]

    # Invalidate caches
    cache = get_cache_service()
    cache.delete(f"portfolio:{id}:holdings")
    cache.delete(f"portfolio:{id}:performance")
    cache.delete(f"portfolio:{id}:allocation")
    cache.delete(f"portfolio:{id}")

    response = success_response(
        data={"id": hid, "deleted": True},
        message=f"Holding {hid} deleted successfully",
    )
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)
