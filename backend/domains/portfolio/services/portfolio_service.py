import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from kafka import KafkaProducer

from ..models.models import Holding, Portfolio


class PortfolioService:
    """
    CRUD operations for portfolios and holdings.
    Publishes HoldingChanged events to portfolio.holdings.changed on every write.
    """

    def __init__(
        self, kafka_bootstrap_servers: list[str], topic: str = "portfolio.holdings.changed"
    ):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        self.topic = topic
        # In-memory storage (replace with database in production)
        self.portfolios: dict[UUID, Portfolio] = {}
        self.holdings: dict[UUID, Holding] = {}

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
        portfolio = Portfolio(
            id=uuid4(),
            name=name,
            owner=owner,
            currency=currency,
            created_at=datetime.now(UTC),
        )
        self.portfolios[portfolio.id] = portfolio
        return portfolio

    def get_portfolio(self, portfolio_id: UUID) -> Portfolio | None:
        return self.portfolios.get(portfolio_id)

    def list_portfolios(self, owner: str | None = None) -> list[Portfolio]:
        if owner:
            return [p for p in self.portfolios.values() if p.owner == owner]
        return list(self.portfolios.values())

    def update_portfolio(
        self, portfolio_id: UUID, name: str | None = None, currency: str | None = None
    ) -> Portfolio | None:
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            return None
        if name is not None:
            portfolio.name = name
        if currency is not None:
            portfolio.currency = currency
        return portfolio

    def delete_portfolio(self, portfolio_id: UUID) -> bool:
        if portfolio_id in self.portfolios:
            # Delete all holdings associated with this portfolio
            holding_ids = [h.id for h in self.holdings.values() if h.portfolio_id == portfolio_id]
            for holding_id in holding_ids:
                self.delete_holding(holding_id)
            del self.portfolios[portfolio_id]
            return True
        return False

    # Holding CRUD
    def create_holding(
        self,
        portfolio_id: UUID,
        ticker_id: UUID,
        quantity: float,
        avg_cost_basis: float,
    ) -> Holding | None:
        if portfolio_id not in self.portfolios:
            return None

        holding = Holding(
            id=uuid4(),
            portfolio_id=portfolio_id,
            ticker_id=ticker_id,
            quantity=quantity,
            avg_cost_basis=avg_cost_basis,
            opened_at=datetime.now(UTC),
        )
        self.holdings[holding.id] = holding
        self._publish_holding_changed("created", holding)
        return holding

    def get_holding(self, holding_id: UUID) -> Holding | None:
        return self.holdings.get(holding_id)

    def list_holdings(self, portfolio_id: UUID) -> list[Holding]:
        return [h for h in self.holdings.values() if h.portfolio_id == portfolio_id]

    def update_holding(
        self,
        holding_id: UUID,
        quantity: float | None = None,
        avg_cost_basis: float | None = None,
    ) -> Holding | None:
        holding = self.holdings.get(holding_id)
        if not holding:
            return None

        if quantity is not None:
            holding.quantity = quantity
        if avg_cost_basis is not None:
            holding.avg_cost_basis = avg_cost_basis

        self._publish_holding_changed("updated", holding)
        return holding

    def delete_holding(self, holding_id: UUID) -> bool:
        holding = self.holdings.get(holding_id)
        if holding:
            self._publish_holding_changed("deleted", holding)
            del self.holdings[holding_id]
            return True
        return False
