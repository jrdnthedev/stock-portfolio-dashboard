"""Dependency injection helpers for FastAPI routes.

This module provides dependency injection using our custom lightweight container.
"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from backend.config import settings
from backend.container import Container
from backend.database.database import get_db
from backend.domains.portfolio.services.portfolio_service import PortfolioService
from backend.infrastructure.repositories.sqlalchemy_portfolio_repository import (
    SQLAlchemyHoldingRepository,
    SQLAlchemyPortfolioRepository,
)


def get_container(request: Request) -> Container:
    """
    Get the dependency injection container from app state.

    Usage:
        container: Container = Depends(get_container)
    """
    return request.app.state.services.container


def get_portfolio_service(db: Session = Depends(get_db)) -> PortfolioService:
    """
    Dependency injection factory for PortfolioService (Traditional approach).

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
        kafka_bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        topic="portfolio.holdings.changed",
    )


def get_portfolio_service_from_container(
    db: Session = Depends(get_db),
    container: Container = Depends(get_container),
) -> PortfolioService:
    """
    Dependency injection for PortfolioService using the DI container.

    This is the recommended approach as it centralizes all dependency wiring.

    Usage:
        @router.post("/portfolios")
        def create_portfolio(
            request: CreatePortfolioRequest,
            service: PortfolioService = Depends(get_portfolio_service_from_container)
        ):
            return service.create_portfolio(request.name, request.owner)
    """
    return container.get_portfolio_service(db)
