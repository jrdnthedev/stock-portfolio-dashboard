from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Stock(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Company name")
    current_price: float = Field(..., description="Current stock price")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Percentage change")
    
class PortfolioItem(BaseModel):
    id: Optional[int] = None
    symbol: str
    shares: float
    purchase_price: float
    purchase_date: datetime
    
class PortfolioSummary(BaseModel):
    total_value: float
    total_gain_loss: float
    total_gain_loss_percent: float
    items: list[PortfolioItem]
