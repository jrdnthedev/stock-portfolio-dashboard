"""SQLAlchemy implementation of portfolio repositories."""

from uuid import UUID

from sqlalchemy.orm import Session

from backend.database.models import Holding as DBHolding
from backend.database.models import Portfolio as DBPortfolio
from backend.domains.portfolio.models.models import Holding as DomainHolding
from backend.domains.portfolio.models.models import Portfolio as DomainPortfolio
from backend.domains.portfolio.repositories.portfolio_repository import (
    HoldingRepository,
    PortfolioRepository,
)


class SQLAlchemyPortfolioRepository(PortfolioRepository):
    """SQLAlchemy implementation of PortfolioRepository."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, portfolio: DomainPortfolio) -> DomainPortfolio:
        """Create a new portfolio."""
        db_portfolio = DBPortfolio(
            id=portfolio.id,
            name=portfolio.name,
            owner=portfolio.owner,
            currency=portfolio.currency,
            created_at=portfolio.created_at,
        )
        self.session.add(db_portfolio)
        self.session.commit()
        self.session.refresh(db_portfolio)
        return self._to_domain(db_portfolio)

    def get_by_id(self, portfolio_id: UUID) -> DomainPortfolio | None:
        """Get portfolio by ID."""
        db_portfolio = (
            self.session.query(DBPortfolio).filter(DBPortfolio.id == portfolio_id).first()
        )
        return self._to_domain(db_portfolio) if db_portfolio else None

    def list_by_owner(self, owner: str) -> list[DomainPortfolio]:
        """List all portfolios for an owner."""
        db_portfolios = self.session.query(DBPortfolio).filter(DBPortfolio.owner == owner).all()
        return [self._to_domain(p) for p in db_portfolios]

    def list_all(self) -> list[DomainPortfolio]:
        """List all portfolios."""
        db_portfolios = self.session.query(DBPortfolio).all()
        return [self._to_domain(p) for p in db_portfolios]

    def update(self, portfolio: DomainPortfolio) -> DomainPortfolio:
        """Update an existing portfolio."""
        db_portfolio = (
            self.session.query(DBPortfolio).filter(DBPortfolio.id == portfolio.id).first()
        )
        if not db_portfolio:
            raise ValueError(f"Portfolio {portfolio.id} not found")

        db_portfolio.name = portfolio.name
        db_portfolio.currency = portfolio.currency
        self.session.commit()
        self.session.refresh(db_portfolio)
        return self._to_domain(db_portfolio)

    def delete(self, portfolio_id: UUID) -> bool:
        """Delete a portfolio."""
        result: int = (
            self.session.query(DBPortfolio).filter(DBPortfolio.id == portfolio_id).delete()
        )
        self.session.commit()
        return result > 0

    def _to_domain(self, db_model: DBPortfolio) -> DomainPortfolio:
        """Convert SQLAlchemy model to Pydantic domain model."""
        return DomainPortfolio(
            id=db_model.id,
            name=db_model.name,
            owner=db_model.owner,
            currency=db_model.currency,
            created_at=db_model.created_at,
        )


class SQLAlchemyHoldingRepository(HoldingRepository):
    """SQLAlchemy implementation of HoldingRepository."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, holding: DomainHolding) -> DomainHolding:
        """Create a new holding."""
        db_holding = DBHolding(
            id=holding.id,
            portfolio_id=holding.portfolio_id,
            ticker_id=holding.ticker_id,
            quantity=holding.quantity,
            avg_cost_basis=holding.avg_cost_basis,
            opened_at=holding.opened_at,
        )
        self.session.add(db_holding)
        self.session.commit()
        self.session.refresh(db_holding)
        return self._to_domain(db_holding)

    def get_by_id(self, holding_id: UUID) -> DomainHolding | None:
        """Get holding by ID."""
        db_holding = self.session.query(DBHolding).filter(DBHolding.id == holding_id).first()
        return self._to_domain(db_holding) if db_holding else None

    def list_by_portfolio(self, portfolio_id: UUID) -> list[DomainHolding]:
        """List all holdings for a portfolio."""
        db_holdings = (
            self.session.query(DBHolding).filter(DBHolding.portfolio_id == portfolio_id).all()
        )
        return [self._to_domain(h) for h in db_holdings]

    def list_by_ticker(self, ticker_id: UUID) -> list[DomainHolding]:
        """List all holdings for a specific ticker across all portfolios."""
        db_holdings = self.session.query(DBHolding).filter(DBHolding.ticker_id == ticker_id).all()
        return [self._to_domain(h) for h in db_holdings]

    def update(self, holding: DomainHolding) -> DomainHolding:
        """Update an existing holding."""
        db_holding = self.session.query(DBHolding).filter(DBHolding.id == holding.id).first()
        if not db_holding:
            raise ValueError(f"Holding {holding.id} not found")

        db_holding.quantity = holding.quantity
        db_holding.avg_cost_basis = holding.avg_cost_basis
        self.session.commit()
        self.session.refresh(db_holding)
        return self._to_domain(db_holding)

    def delete(self, holding_id: UUID) -> bool:
        """Delete a holding."""
        result: int = self.session.query(DBHolding).filter(DBHolding.id == holding_id).delete()
        self.session.commit()
        return result > 0

    def delete_by_portfolio(self, portfolio_id: UUID) -> int:
        """Delete all holdings for a portfolio."""
        result: int = (
            self.session.query(DBHolding).filter(DBHolding.portfolio_id == portfolio_id).delete()
        )
        self.session.commit()
        return result

    def _to_domain(self, db_model: DBHolding) -> DomainHolding:
        """Convert SQLAlchemy model to Pydantic domain model."""
        return DomainHolding(
            id=db_model.id,
            portfolio_id=db_model.portfolio_id,
            ticker_id=db_model.ticker_id,
            quantity=db_model.quantity,
            avg_cost_basis=db_model.avg_cost_basis,
            opened_at=db_model.opened_at,
        )
