"""Dependency injection helpers for FastAPI routes."""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.database import get_db
from backend.domains.portfolio.services.portfolio_service import PortfolioService
from backend.infrastructure.repositories.sqlalchemy_portfolio_repository import (
    SQLAlchemyHoldingRepository,
    SQLAlchemyPortfolioRepository,
)


def get_portfolio_service(db: Session = Depends(get_db)) -> PortfolioService:
    """
    Dependency injection factory for PortfolioService.

    Creates a PortfolioService with SQLAlchemy repositories and Kafka producer.

    Usage:
        @router.post("/portfolios")
        def create_portfolio(
            request: CreatePortfolioRequest,
            service: PortfolioService = Depends(get_portfolio_service)
        ):
            return service.create_portfolio(request.name, request.owner)
    """
    portfolio_repo = SQLAlchemyPortfolioRepository(db)
    holding_repo = SQLAlchemyHoldingRepository(db)

    return PortfolioService(
        portfolio_repo=portfolio_repo,
        holding_repo=holding_repo,
        kafka_bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        topic="portfolio.holdings.changed",
    )
