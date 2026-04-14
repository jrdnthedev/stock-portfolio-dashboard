"""Tests for AlertPublisher service."""

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from domains.portfolio.services.alert_publisher import AlertPublisher
from tests.test_fixtures import mock_kafka_producer  # noqa: F401


@pytest.fixture
def alert_publisher(mock_kafka_producer: MagicMock) -> AlertPublisher:
    _ = mock_kafka_producer  # Fixture dependency
    return AlertPublisher(["localhost:9092"], "test.alerts.topic")


class TestAlertPublisherInit:
    def test_init_creates_kafka_producer(self, mock_kafka_producer: MagicMock) -> None:
        publisher = AlertPublisher(["localhost:9092"], "test.topic")
        assert publisher.topic == "test.topic"
        assert publisher.producer == mock_kafka_producer

    def test_init_initializes_empty_storage(self, alert_publisher: AlertPublisher) -> None:
        assert alert_publisher.alert_configs == {}
        assert alert_publisher.previous_prices == {}


class TestAlertConfigCRUD:
    def test_create_alert_config(self, alert_publisher: AlertPublisher) -> None:
        portfolio_id = uuid4()
        ticker_id = uuid4()
        config = alert_publisher.create_alert_config(portfolio_id, ticker_id, 5.0)

        assert config.portfolio_id == portfolio_id
        assert config.ticker_id == ticker_id
        assert config.threshold_pct == 5.0
        assert config.enabled is True
        assert isinstance(config.id, UUID)
        assert config.id in alert_publisher.alert_configs

    def test_create_alert_config_with_custom_id(self, alert_publisher: AlertPublisher) -> None:
        alert_id = uuid4()
        config = alert_publisher.create_alert_config(uuid4(), uuid4(), 10.0, alert_id=alert_id)
        assert config.id == alert_id

    def test_get_alert_config_returns_existing(self, alert_publisher: AlertPublisher) -> None:
        created = alert_publisher.create_alert_config(uuid4(), uuid4(), 5.0)
        retrieved = alert_publisher.get_alert_config(created.id)
        assert retrieved == created

    def test_get_alert_config_returns_none_if_not_found(
        self, alert_publisher: AlertPublisher
    ) -> None:
        result = alert_publisher.get_alert_config(uuid4())
        assert result is None

    def test_list_alert_configs_returns_all(self, alert_publisher: AlertPublisher) -> None:
        c1 = alert_publisher.create_alert_config(uuid4(), uuid4(), 5.0)
        c2 = alert_publisher.create_alert_config(uuid4(), uuid4(), 10.0)
        configs = alert_publisher.list_alert_configs()
        assert len(configs) == 2
        assert c1 in configs
        assert c2 in configs

    def test_list_alert_configs_filters_by_portfolio(self, alert_publisher: AlertPublisher) -> None:
        portfolio1 = uuid4()
        portfolio2 = uuid4()
        c1 = alert_publisher.create_alert_config(portfolio1, uuid4(), 5.0)
        c2 = alert_publisher.create_alert_config(portfolio2, uuid4(), 5.0)

        portfolio1_configs = alert_publisher.list_alert_configs(portfolio_id=portfolio1)
        assert len(portfolio1_configs) == 1
        assert c1 in portfolio1_configs
        assert c2 not in portfolio1_configs

    def test_update_alert_config_threshold(self, alert_publisher: AlertPublisher) -> None:
        config = alert_publisher.create_alert_config(uuid4(), uuid4(), 5.0)
        updated = alert_publisher.update_alert_config(config.id, threshold_pct=10.0)
        assert updated is not None
        assert updated.threshold_pct == 10.0
        assert updated.enabled is True

    def test_update_alert_config_enabled(self, alert_publisher: AlertPublisher) -> None:
        config = alert_publisher.create_alert_config(uuid4(), uuid4(), 5.0)
        updated = alert_publisher.update_alert_config(config.id, enabled=False)
        assert updated is not None
        assert updated.enabled is False
        assert updated.threshold_pct == 5.0

    def test_update_alert_config_returns_none_if_not_found(
        self, alert_publisher: AlertPublisher
    ) -> None:
        result = alert_publisher.update_alert_config(uuid4(), threshold_pct=10.0)
        assert result is None

    def test_delete_alert_config(self, alert_publisher: AlertPublisher) -> None:
        config = alert_publisher.create_alert_config(uuid4(), uuid4(), 5.0)
        result = alert_publisher.delete_alert_config(config.id)
        assert result is True
        assert config.id not in alert_publisher.alert_configs

    def test_delete_alert_config_returns_false_if_not_found(
        self, alert_publisher: AlertPublisher
    ) -> None:
        result = alert_publisher.delete_alert_config(uuid4())
        assert result is False


class TestAlertPublishing:
    def test_first_price_does_not_trigger_alert(
        self, alert_publisher: AlertPublisher, mock_kafka_producer: MagicMock
    ) -> None:
        ticker_id = uuid4()
        alert_publisher.create_alert_config(uuid4(), ticker_id, 5.0)

        alerts = alert_publisher.check_and_publish_alerts(ticker_id, 100.0)

        assert len(alerts) == 0
        assert alert_publisher.previous_prices[ticker_id] == 100.0
        mock_kafka_producer.send.assert_not_called()

    def test_small_price_change_does_not_trigger_alert(
        self, alert_publisher: AlertPublisher, mock_kafka_producer: MagicMock
    ) -> None:
        ticker_id = uuid4()
        alert_publisher.create_alert_config(uuid4(), ticker_id, 5.0)

        # Set initial price
        alert_publisher.check_and_publish_alerts(ticker_id, 100.0)
        mock_kafka_producer.reset_mock()

        # Price change of 3% (below 5% threshold)
        alerts = alert_publisher.check_and_publish_alerts(ticker_id, 103.0)

        assert len(alerts) == 0
        mock_kafka_producer.send.assert_not_called()

    def test_large_price_increase_triggers_alert(
        self, alert_publisher: AlertPublisher, mock_kafka_producer: MagicMock
    ) -> None:
        ticker_id = uuid4()
        portfolio_id = uuid4()
        alert_publisher.create_alert_config(portfolio_id, ticker_id, 5.0)

        # Set initial price
        alert_publisher.check_and_publish_alerts(ticker_id, 100.0)
        mock_kafka_producer.reset_mock()

        # Price change of 10% (above 5% threshold)
        alerts = alert_publisher.check_and_publish_alerts(ticker_id, 110.0)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.ticker_id == ticker_id
        assert alert.portfolio_id == portfolio_id
        assert alert.previous_price == 100.0
        assert alert.current_price == 110.0
        assert alert.change_pct == 10.0
        assert alert.threshold_pct == 5.0

        # Verify Kafka publish
        mock_kafka_producer.send.assert_called_once()
        args, _ = mock_kafka_producer.send.call_args
        assert args[0] == "test.alerts.topic"
        event = args[1]
        assert event["event"] == "PriceAlert"
        assert event["data"]["ticker_id"] == str(ticker_id)

    def test_large_price_decrease_triggers_alert(
        self, alert_publisher: AlertPublisher, mock_kafka_producer: MagicMock
    ) -> None:
        ticker_id = uuid4()
        portfolio_id = uuid4()
        alert_publisher.create_alert_config(portfolio_id, ticker_id, 5.0)

        # Set initial price
        alert_publisher.check_and_publish_alerts(ticker_id, 100.0)
        mock_kafka_producer.reset_mock()

        # Price change of -8% (above 5% threshold in absolute terms)
        alerts = alert_publisher.check_and_publish_alerts(ticker_id, 92.0)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.change_pct == -8.0
        assert alert.threshold_pct == 5.0

        mock_kafka_producer.send.assert_called_once()

    def test_disabled_alert_does_not_trigger(
        self, alert_publisher: AlertPublisher, mock_kafka_producer: MagicMock
    ) -> None:
        ticker_id = uuid4()
        config = alert_publisher.create_alert_config(uuid4(), ticker_id, 5.0)
        alert_publisher.update_alert_config(config.id, enabled=False)

        # Set initial price
        alert_publisher.check_and_publish_alerts(ticker_id, 100.0)
        mock_kafka_producer.reset_mock()

        # Large price change
        alerts = alert_publisher.check_and_publish_alerts(ticker_id, 120.0)

        assert len(alerts) == 0
        mock_kafka_producer.send.assert_not_called()

    def test_multiple_alerts_for_different_portfolios(
        self, alert_publisher: AlertPublisher, mock_kafka_producer: MagicMock
    ) -> None:
        ticker_id = uuid4()
        portfolio1 = uuid4()
        portfolio2 = uuid4()

        alert_publisher.create_alert_config(portfolio1, ticker_id, 5.0)
        alert_publisher.create_alert_config(portfolio2, ticker_id, 8.0)

        # Set initial price
        alert_publisher.check_and_publish_alerts(ticker_id, 100.0)
        mock_kafka_producer.reset_mock()

        # Price change of 7% triggers first alert but not second
        alerts = alert_publisher.check_and_publish_alerts(ticker_id, 107.0)

        assert len(alerts) == 1
        assert alerts[0].portfolio_id == portfolio1
        mock_kafka_producer.send.assert_called_once()

        # Reset and test larger change
        mock_kafka_producer.reset_mock()
        alert_publisher.previous_prices[ticker_id] = 100.0

        # Price change of 10% triggers both alerts
        alerts = alert_publisher.check_and_publish_alerts(ticker_id, 110.0)

        assert len(alerts) == 2
        portfolio_ids = {alert.portfolio_id for alert in alerts}
        assert portfolio1 in portfolio_ids
        assert portfolio2 in portfolio_ids
        assert mock_kafka_producer.send.call_count == 2

    def test_previous_price_updates_after_check(self, alert_publisher: AlertPublisher) -> None:
        ticker_id = uuid4()
        alert_publisher.create_alert_config(uuid4(), ticker_id, 5.0)

        alert_publisher.check_and_publish_alerts(ticker_id, 100.0)
        assert alert_publisher.previous_prices[ticker_id] == 100.0

        alert_publisher.check_and_publish_alerts(ticker_id, 110.0)
        assert alert_publisher.previous_prices[ticker_id] == 110.0

    def test_zero_previous_price_does_not_crash(
        self, alert_publisher: AlertPublisher, mock_kafka_producer: MagicMock
    ) -> None:
        ticker_id = uuid4()
        alert_publisher.create_alert_config(uuid4(), ticker_id, 5.0)

        # Manually set previous price to 0
        alert_publisher.previous_prices[ticker_id] = 0.0

        # Should handle gracefully without division by zero
        alerts = alert_publisher.check_and_publish_alerts(ticker_id, 100.0)

        # With 0 previous price, change_pct is 0, so no alert
        assert len(alerts) == 0
        mock_kafka_producer.send.assert_not_called()

    def test_alert_only_checks_matching_ticker(
        self, alert_publisher: AlertPublisher, mock_kafka_producer: MagicMock
    ) -> None:
        ticker1 = uuid4()
        ticker2 = uuid4()
        alert_publisher.create_alert_config(uuid4(), ticker1, 5.0)

        # Set price for ticker1
        alert_publisher.check_and_publish_alerts(ticker1, 100.0)
        mock_kafka_producer.reset_mock()

        # Update ticker2 (different ticker) - should not trigger alert for ticker1's config
        alerts = alert_publisher.check_and_publish_alerts(ticker2, 200.0)

        assert len(alerts) == 0
        mock_kafka_producer.send.assert_not_called()
