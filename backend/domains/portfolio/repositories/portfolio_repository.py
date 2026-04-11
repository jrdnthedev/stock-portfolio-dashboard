"""Repository interfaces for portfolio persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from ..models.models import Holding, Portfolio


class PortfolioRepository(ABC):
    """Repository interface for Portfolio persistence."""

    @abstractmethod
    def create(self, portfolio: Portfolio) -> Portfolio:
        """Create a new portfolio."""
        pass

    @abstractmethod
    def get_by_id(self, portfolio_id: UUID) -> Portfolio | None:
        """Get portfolio by ID."""
        pass

    @abstractmethod
    def list_by_owner(self, owner: str) -> list[Portfolio]:
        """List all portfolios for an owner."""
        pass

    @abstractmethod
    def list_all(self) -> list[Portfolio]:
        """List all portfolios."""
        pass

    @abstractmethod
    def update(self, portfolio: Portfolio) -> Portfolio:
        """Update an existing portfolio."""
        pass

    @abstractmethod
    def delete(self, portfolio_id: UUID) -> bool:
        """Delete a portfolio. Returns True if deleted, False if not found."""
        pass


class HoldingRepository(ABC):
    """Repository interface for Holding persistence."""

    @abstractmethod
    def create(self, holding: Holding) -> Holding:
        """Create a new holding."""
        pass

    @abstractmethod
    def get_by_id(self, holding_id: UUID) -> Holding | None:
        """Get holding by ID."""
        pass

    @abstractmethod
    def list_by_portfolio(self, portfolio_id: UUID) -> list[Holding]:
        """List all holdings for a portfolio."""
        pass

    @abstractmethod
    def list_by_ticker(self, ticker_id: UUID) -> list[Holding]:
        """List all holdings for a specific ticker across all portfolios."""
        pass

    @abstractmethod
    def update(self, holding: Holding) -> Holding:
        """Update an existing holding."""
        pass

    @abstractmethod
    def delete(self, holding_id: UUID) -> bool:
        """Delete a holding. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    def delete_by_portfolio(self, portfolio_id: UUID) -> int:
        """Delete all holdings for a portfolio. Returns count of deleted holdings."""
        pass
