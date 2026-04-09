import json
import threading
from collections.abc import Callable
from typing import Any

from kafka import KafkaConsumer
from pydantic import BaseModel

from .alert_publisher import AlertPublisher
from .performance_calculator import PerformanceCalculator
from .portfolio_service import PortfolioService


class PriceUpdatedEvent(BaseModel):
    """Schema for PriceUpdated events from market data."""

    ticker_id: int
    date: str
    close: float


class PriceEventConsumer:
    """
    Kafka consumer that listens to market.prices.live and triggers
    PerformanceCalculator to recompute affected portfolios.
    """

    def __init__(
        self,
        kafka_bootstrap_servers: list[str],
        topic: str = "market.prices.live",
        group_id: str = "portfolio-performance-group",
    ):
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=kafka_bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        self.topic = topic
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._on_price_update_callback: Callable[[Any], None] | None = None

    def set_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Set a callback to be invoked when a price update is received."""
        self._on_price_update_callback = callback

    def start(self) -> None:
        """Start consuming price events in a background thread."""

        def consume_loop() -> None:
            for message in self.consumer:
                if self._stop_event.is_set():
                    break

                try:
                    event = message.value
                    if event.get("event") == "PriceUpdated" and "data" in event:
                        self._handle_price_update(event["data"])
                except Exception as e:
                    print(f"Error processing price event: {e}")

        self._stop_event.clear()
        self._thread = threading.Thread(target=consume_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop consuming events and close the consumer."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        self.consumer.close()

    def _handle_price_update(self, data: dict[str, Any]) -> None:
        """Process a PriceUpdated event."""
        try:
            price_event = PriceUpdatedEvent(**data)

            # Invoke the callback if set
            if self._on_price_update_callback:
                self._on_price_update_callback(price_event.model_dump())

        except Exception as e:
            print(f"Failed to process PriceUpdated event: {e}")


class PortfolioPerformanceOrchestrator:
    """
    Orchestrates the recomputation of portfolio performance when prices update.
    Integrates PortfolioService, PerformanceCalculator, PriceEventConsumer, and AlertPublisher.
    """

    def __init__(
        self,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
        price_consumer: PriceEventConsumer,
        alert_publisher: AlertPublisher | None = None,
        websocket_publisher: Callable[[str, dict[str, Any]], None] | None = None,
    ):
        self.portfolio_service = portfolio_service
        self.performance_calculator = performance_calculator
        self.price_consumer = price_consumer
        self.alert_publisher = alert_publisher
        self.websocket_publisher = websocket_publisher

        # Register the callback for price updates
        self.price_consumer.set_callback(self._on_price_updated)

    def start(self) -> None:
        """Start listening for price updates."""
        self.price_consumer.start()

    def stop(self) -> None:
        """Stop listening for price updates."""
        self.price_consumer.stop()

    def _on_price_updated(self, price_data: dict[str, Any]) -> None:
        """
        Handle a price update by checking alerts, recomputing affected portfolios,
        and pushing results over WebSocket.
        """
        try:
            ticker_id = price_data.get("ticker_id")
            close_price = price_data.get("close")

            if ticker_id is None or close_price is None:
                return

            # Check and publish alerts if alert publisher is configured
            if self.alert_publisher:
                self.alert_publisher.check_and_publish_alerts(ticker_id, close_price)

            # Update the price in the performance calculator
            self.performance_calculator.update_price(ticker_id, close_price)

            # Find all portfolios that have holdings for this ticker
            affected_portfolios = set()
            for holding in self.portfolio_service.holdings.values():
                if holding.ticker_id == ticker_id:
                    affected_portfolios.add(holding.portfolio_id)

            # Recompute and publish performance for affected portfolios
            for portfolio_id in affected_portfolios:
                self._recompute_and_publish(portfolio_id)

        except Exception as e:
            print(f"Error handling price update: {e}")

    def _recompute_and_publish(self, portfolio_id: Any) -> None:
        """Recompute portfolio performance and publish via WebSocket."""
        try:
            holdings = self.portfolio_service.list_holdings(portfolio_id)
            if not holdings:
                return

            # Convert holdings to the format expected by performance calculator
            holdings_data = [(h.ticker_id, h.quantity, h.avg_cost_basis) for h in holdings]

            # Calculate performance
            performance = self.performance_calculator.calculate_portfolio_performance(
                portfolio_id, holdings_data
            )

            if performance and self.websocket_publisher:
                # Publish updated P&L over WebSocket
                self.websocket_publisher(
                    str(portfolio_id),
                    {
                        "event": "PortfolioPerformanceUpdated",
                        "portfolio_id": str(portfolio_id),
                        "data": performance.model_dump(mode="json"),
                    },
                )

        except Exception as e:
            print(f"Error recomputing portfolio {portfolio_id}: {e}")
