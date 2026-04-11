import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from kafka import KafkaProducer

from ..models.models import Holding, Portfolio
from ..repositories.portfolio_repository import HoldingRepository, PortfolioRepository


class PortfolioService:
    """
    CRUD operations for portfolios and holdings.
    Publishes HoldingChanged events to portfolio.holdings.changed on every write.
    Uses repositories for database persistence.
    """

    def __init__(
        self,
        portfolio_repo: PortfolioRepository,
        holding_repo: HoldingRepository,
        kafka_bootstrap_servers: list[str],
        topic: str = "portfolio.holdings.changed",
    ):
        self.portfolio_repo = portfolio_repo
        self.holding_repo = holding_repo
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        self.topic = topic

    def _publish_holding_changed(self, event_type: str, holding: Holding) -> None:
        """Publish a HoldingChanged event to Kafka."""
        event = {
            "event": "HoldingChanged",
            "event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": holding.model_dump(mode="json"),
        }
        self.producer.send(self.topic, event)
        self.producer.flush()

    # Portfolio CRUD
    def create_portfolio(self, name: str, owner: str, currency: str = "USD") -> Portfolio:
        """Create a new portfolio and persist it to the database."""
        portfolio = Portfolio(
            id=uuid4(),
            name=name,
            owner=owner,
            currency=currency,
            created_at=datetime.now(UTC),
        )
        return self.portfolio_repo.create(portfolio)

    def get_portfolio(self, portfolio_id: UUID) -> Portfolio | None:
        """Get a portfolio by ID from the database."""
        return self.portfolio_repo.get_by_id(portfolio_id)

    def list_portfolios(self, owner: str | None = None) -> list[Portfolio]:
        """List portfolios, optionally filtered by owner."""
        if owner:
            return self.portfolio_repo.list_by_owner(owner)
        return self.portfolio_repo.list_all()

    def update_portfolio(
        self, portfolio_id: UUID, name: str | None = None, currency: str | None = None
    ) -> Portfolio | None:
        """Update a portfolio's name or currency."""
        portfolio = self.portfolio_repo.get_by_id(portfolio_id)
        if not portfolio:
            return None
        if name is not None:
            portfolio.name = name
        if currency is not None:
            portfolio.currency = currency
        return self.portfolio_repo.update(portfolio)

    def delete_portfolio(self, portfolio_id: UUID) -> bool:
        """Delete a portfolio and all its holdings."""
        # Delete all holdings associated with this portfolio first
        self.holding_repo.delete_by_portfolio(portfolio_id)
        # Delete the portfolio
        return self.portfolio_repo.delete(portfolio_id)

    # Holding CRUD
    def create_holding(
        self,
        portfolio_id: UUID,
        ticker_id: UUID,
        quantity: float,
        avg_cost_basis: float,
    ) -> Holding | None:
        """Create a new holding in a portfolio."""
        # Verify portfolio exists
        if not self.portfolio_repo.get_by_id(portfolio_id):
            return None

        holding = Holding(
            id=uuid4(),
            portfolio_id=portfolio_id,
            ticker_id=ticker_id,
            quantity=quantity,
            avg_cost_basis=avg_cost_basis,
            opened_at=datetime.now(UTC),
        )
        created_holding = self.holding_repo.create(holding)
        self._publish_holding_changed("created", created_holding)
        return created_holding

    def get_holding(self, holding_id: UUID) -> Holding | None:
        """Get a holding by ID from the database."""
        return self.holding_repo.get_by_id(holding_id)

    def list_holdings(self, portfolio_id: UUID) -> list[Holding]:
        """List all holdings for a portfolio."""
        return self.holding_repo.list_by_portfolio(portfolio_id)

    def list_holdings_by_ticker(self, ticker_id: UUID) -> list[Holding]:
        """List all holdings for a specific ticker across all portfolios."""
        return self.holding_repo.list_by_ticker(ticker_id)

    def update_holding(
        self,
        holding_id: UUID,
        quantity: float | None = None,
        avg_cost_basis: float | None = None,
    ) -> Holding | None:
        """Update a holding's quantity or average cost basis."""
        holding = self.holding_repo.get_by_id(holding_id)
        if not holding:
            return None

        if quantity is not None:
            holding.quantity = quantity
        if avg_cost_basis is not None:
            holding.avg_cost_basis = avg_cost_basis

        updated_holding = self.holding_repo.update(holding)
        self._publish_holding_changed("updated", updated_holding)
        return updated_holding

    def delete_holding(self, holding_id: UUID) -> bool:
        """Delete a holding."""
        holding = self.holding_repo.get_by_id(holding_id)
        if holding:
            self._publish_holding_changed("deleted", holding)
            return self.holding_repo.delete(holding_id)
        return False
