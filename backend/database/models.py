"""
SQLAlchemy database models for the stock portfolio dashboard.
Defines the database schema for tickers, prices, portfolios, and holdings.
"""

from datetime import date as date_type
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Ticker(Base):
    """Stock ticker information."""

    __tablename__ = "tickers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    symbol: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(50), nullable=False, default="Equity")

    # Relationships
    prices: Mapped[list["PricePoint"]] = relationship(
        back_populates="ticker", cascade="all, delete-orphan"
    )
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="ticker", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ticker(symbol='{self.symbol}', company='{self.company_name}')>"


class PricePoint(Base):
    """Historical price data for a ticker."""

    __tablename__ = "price_points"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ticker_id: Mapped[UUID] = mapped_column(ForeignKey("tickers.id"), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(nullable=False, index=True)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    ticker: Mapped["Ticker"] = relationship(back_populates="prices")

    def __repr__(self) -> str:
        return f"<PricePoint(ticker_id={self.ticker_id}, date={self.date}, close={self.close})>"


class Portfolio(Base):
    """User portfolio."""

    __tablename__ = "portfolios"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["PerformanceSnapshot"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Portfolio(name='{self.name}', owner='{self.owner}')>"


class Holding(Base):
    """Individual holding within a portfolio."""

    __tablename__ = "holdings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    portfolio_id: Mapped[UUID] = mapped_column(
        ForeignKey("portfolios.id"), nullable=False, index=True
    )
    ticker_id: Mapped[UUID] = mapped_column(ForeignKey("tickers.id"), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    avg_cost_basis: Mapped[float] = mapped_column(Float, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="holdings")
    ticker: Mapped["Ticker"] = relationship(back_populates="holdings")

    def __repr__(self) -> str:
        return f"<Holding(portfolio_id={self.portfolio_id}, ticker_id={self.ticker_id}, quantity={self.quantity})>"


class PerformanceSnapshot(Base):
    """Daily performance snapshot for a portfolio."""

    __tablename__ = "performance_snapshots"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    portfolio_id: Mapped[UUID] = mapped_column(
        ForeignKey("portfolios.id"), nullable=False, index=True
    )
    date: Mapped[date_type] = mapped_column(nullable=False, index=True)
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    daily_return: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cumulative_return: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="snapshots")

    def __repr__(self) -> str:
        return f"<PerformanceSnapshot(portfolio_id={self.portfolio_id}, date={self.date}, value={self.total_value})>"
