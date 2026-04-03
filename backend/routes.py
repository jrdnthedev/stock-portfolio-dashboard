from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class Stock(BaseModel):
    symbol: str
    name: str
    current_price: float
    change: float
    change_percent: float


router = APIRouter(prefix="/api/stocks", tags=["stocks"])

# Mock data for demonstration
MOCK_STOCKS: list[dict[str, str | float]] = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "current_price": 178.50,
        "change": 2.25,
        "change_percent": 1.28,
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "current_price": 142.30,
        "change": -1.15,
        "change_percent": -0.80,
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "current_price": 420.15,
        "change": 3.40,
        "change_percent": 0.82,
    },
]


@router.get("/", response_model=list[Stock])
async def get_stocks() -> list[dict[str, str | float]]:
    """Get list of available stocks"""
    return MOCK_STOCKS


@router.get("/{symbol}", response_model=Stock)
async def get_stock(symbol: str) -> dict[str, str | float]:
    """Get stock details by symbol"""
    stock = next((s for s in MOCK_STOCKS if s["symbol"] == symbol.upper()), None)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock
