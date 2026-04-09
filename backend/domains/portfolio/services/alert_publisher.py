"""Alert Publisher service for monitoring price movements and publishing alerts."""

import json
from datetime import UTC, datetime
from uuid import UUID

from kafka import KafkaProducer

from ..models.models import AlertConfig, PriceAlert


class AlertPublisher:
    """
    Monitors price movements and publishes alerts when thresholds are exceeded.
    Publishes PriceAlert events to portfolio.alerts topic.
    """

    def __init__(
        self,
        kafka_bootstrap_servers: list[str],
        topic: str = "portfolio.alerts",
    ):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        self.topic = topic

        # In-memory storage for alert configurations
        self.alert_configs: dict[UUID, AlertConfig] = {}

        # Cache previous prices to calculate changes: ticker_id -> price
        self.previous_prices: dict[UUID, float] = {}

    def create_alert_config(
        self,
        portfolio_id: UUID,
        ticker_id: UUID,
        threshold_pct: float,
        alert_id: UUID | None = None,
    ) -> AlertConfig:
        """Create an alert configuration for a holding."""
        from uuid import uuid4

        config = AlertConfig(
            id=alert_id or uuid4(),
            portfolio_id=portfolio_id,
            ticker_id=ticker_id,
            threshold_pct=threshold_pct,
            enabled=True,
        )
        self.alert_configs[config.id] = config
        return config

    def get_alert_config(self, alert_id: UUID) -> AlertConfig | None:
        """Get an alert configuration by ID."""
        return self.alert_configs.get(alert_id)

    def list_alert_configs(self, portfolio_id: UUID | None = None) -> list[AlertConfig]:
        """List all alert configurations, optionally filtered by portfolio."""
        if portfolio_id:
            return [c for c in self.alert_configs.values() if c.portfolio_id == portfolio_id]
        return list(self.alert_configs.values())

    def update_alert_config(
        self,
        alert_id: UUID,
        threshold_pct: float | None = None,
        enabled: bool | None = None,
    ) -> AlertConfig | None:
        """Update an alert configuration."""
        config = self.alert_configs.get(alert_id)
        if not config:
            return None

        if threshold_pct is not None:
            config.threshold_pct = threshold_pct
        if enabled is not None:
            config.enabled = enabled

        return config

    def delete_alert_config(self, alert_id: UUID) -> bool:
        """Delete an alert configuration."""
        if alert_id in self.alert_configs:
            del self.alert_configs[alert_id]
            return True
        return False

    def check_and_publish_alerts(self, ticker_id: UUID, current_price: float) -> list[PriceAlert]:
        """
        Check if the price change exceeds any alert thresholds and publish alerts.

        Args:
            ticker_id: The ticker ID that had a price update
            current_price: The new current price

        Returns:
            List of alerts that were triggered and published
        """
        triggered_alerts: list[PriceAlert] = []

        # Get previous price
        previous_price = self.previous_prices.get(ticker_id)

        # If this is the first price we've seen, store it and return
        if previous_price is None:
            self.previous_prices[ticker_id] = current_price
            return triggered_alerts

        # Calculate price change percentage
        if previous_price == 0:
            change_pct = 0.0
        else:
            change_pct = ((current_price - previous_price) / previous_price) * 100

        # Check all alert configs for this ticker
        for config in self.alert_configs.values():
            if not config.enabled or config.ticker_id != ticker_id:
                continue

            # Check if threshold is exceeded (absolute value for both up/down movements)
            if abs(change_pct) >= config.threshold_pct:
                alert = PriceAlert(
                    ticker_id=ticker_id,
                    portfolio_id=config.portfolio_id,
                    previous_price=previous_price,
                    current_price=current_price,
                    change_pct=change_pct,
                    threshold_pct=config.threshold_pct,
                    timestamp=datetime.now(UTC),
                )

                # Publish the alert
                self._publish_alert(alert)
                triggered_alerts.append(alert)

        # Update the previous price for next comparison
        self.previous_prices[ticker_id] = current_price

        return triggered_alerts

    def _publish_alert(self, alert: PriceAlert) -> None:
        """Publish a PriceAlert event to Kafka."""
        event = {
            "event": "PriceAlert",
            "timestamp": alert.timestamp.isoformat(),
            "data": alert.model_dump(mode="json"),
        }
        self.producer.send(self.topic, event)
        self.producer.flush()
