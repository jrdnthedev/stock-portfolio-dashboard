"""Dependency Injection Container for the application.

This module provides centralized dependency management without external dependencies.
A lightweight pure-Python DI container for better portability and simplicity.
"""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import Settings, get_settings
from backend.domains.portfolio.services.portfolio_service import PortfolioService
from backend.infrastructure.repositories.sqlalchemy_portfolio_repository import (
    SQLAlchemyHoldingRepository,
    SQLAlchemyPortfolioRepository,
)


def get_db_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Create a database session and ensure it's closed after use."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


class Container:
    """Lightweight dependency injection container.

    Provides centralized management of application dependencies using
    lazy initialization and proper lifecycle management.
    """

    def __init__(self) -> None:
        """Initialize the container."""
        self._config: Settings | None = None
        self._db_engine: Engine | None = None
        self._db_session_factory: sessionmaker[Session] | None = None

    @property
    def config(self) -> Settings:
        """Get application settings (singleton)."""
        if self._config is None:
            self._config = get_settings()
        return self._config

    @property
    def db_engine(self) -> Engine:
        """Get database engine (singleton)."""
        if self._db_engine is None:
            self._db_engine = create_engine(
                self.config.DATABASE_URL,
                echo=self.config.DEBUG,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
        return self._db_engine

    @property
    def db_session_factory(self) -> sessionmaker[Session]:
        """Get database session factory (singleton)."""
        if self._db_session_factory is None:
            self._db_session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.db_engine,
            )
        return self._db_session_factory

    def get_db_session(self) -> Generator[Session, None, None]:
        """Create a database session (factory - new session each call)."""
        session = self.db_session_factory()
        try:
            yield session
        finally:
            session.close()

    def get_portfolio_repository(self, session: Session) -> SQLAlchemyPortfolioRepository:
        """Create a portfolio repository (factory)."""
        return SQLAlchemyPortfolioRepository(session)

    def get_holding_repository(self, session: Session) -> SQLAlchemyHoldingRepository:
        """Create a holding repository (factory)."""
        return SQLAlchemyHoldingRepository(session)

    def get_portfolio_service(self, session: Session) -> PortfolioService:
        """Create a portfolio service with all dependencies (factory)."""
        portfolio_repo = self.get_portfolio_repository(session)
        holding_repo = self.get_holding_repository(session)

        return PortfolioService(
            portfolio_repo=portfolio_repo,
            holding_repo=holding_repo,
            kafka_bootstrap_servers=self.config.kafka_bootstrap_servers.split(","),
            topic="portfolio.holdings.changed",
        )

    def reset(self) -> None:
        """Reset container state (useful for testing)."""
        self._config = None
        if self._db_engine:
            self._db_engine.dispose()
        self._db_engine = None
        self._db_session_factory = None
