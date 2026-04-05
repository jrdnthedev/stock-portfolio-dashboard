"""Unit tests for health check endpoint."""

from unittest.mock import MagicMock, patch

from backend.gateway.health import check_kafka, check_postgres, check_redis, get_health_status


class TestPostgresHealthCheck:
    """Test PostgreSQL health check."""

    @patch("backend.gateway.health.engine")
    def test_postgres_healthy(self, mock_engine: MagicMock) -> None:
        """Test successful PostgreSQL health check."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (1,)

        result = check_postgres()

        assert result["status"] == "healthy"
        assert "PostgreSQL connection successful" in result["message"]

    @patch("backend.gateway.health.engine")
    def test_postgres_unhealthy(self, mock_engine: MagicMock) -> None:
        """Test failed PostgreSQL health check."""
        mock_engine.connect.side_effect = Exception("Connection failed")

        result = check_postgres()

        assert result["status"] == "unhealthy"
        assert "Connection failed" in result["message"]


class TestRedisHealthCheck:
    """Test Redis health check."""

    @patch("backend.gateway.health.get_cache_service")
    def test_redis_healthy(self, mock_get_cache: MagicMock) -> None:
        """Test successful Redis health check."""
        mock_cache = MagicMock()
        mock_cache.ping.return_value = True
        mock_get_cache.return_value = mock_cache

        result = check_redis()

        assert result["status"] == "healthy"
        assert "Redis connection successful" in result["message"]

    @patch("backend.gateway.health.get_cache_service")
    def test_redis_ping_failed(self, mock_get_cache: MagicMock) -> None:
        """Test Redis ping failure."""
        mock_cache = MagicMock()
        mock_cache.ping.return_value = False
        mock_get_cache.return_value = mock_cache

        result = check_redis()

        assert result["status"] == "unhealthy"
        assert "Redis ping failed" in result["message"]

    @patch("backend.gateway.health.get_cache_service")
    def test_redis_exception(self, mock_get_cache: MagicMock) -> None:
        """Test Redis connection exception."""
        mock_get_cache.side_effect = Exception("Connection error")

        result = check_redis()

        assert result["status"] == "unhealthy"
        assert "Connection error" in result["message"]


class TestKafkaHealthCheck:
    """Test Kafka health check."""

    @patch("backend.gateway.health.KafkaAdminClient")
    @patch("backend.gateway.health.get_settings")
    def test_kafka_healthy(self, mock_settings: MagicMock, mock_admin: MagicMock) -> None:
        """Test successful Kafka health check."""
        mock_settings.return_value.kafka_bootstrap_servers = "localhost:9092"
        mock_client = MagicMock()
        mock_client.list_topics.return_value = ["topic1", "topic2", "topic3"]
        mock_admin.return_value = mock_client

        result = check_kafka()

        assert result["status"] == "healthy"
        assert "Kafka broker connected" in result["message"]
        assert "3 topics" in result["message"]
        mock_client.close.assert_called_once()

    @patch("backend.gateway.health.KafkaAdminClient")
    @patch("backend.gateway.health.get_settings")
    def test_kafka_connection_failed(self, mock_settings: MagicMock, mock_admin: MagicMock) -> None:
        """Test Kafka connection failure."""
        from kafka.errors import KafkaError

        mock_settings.return_value.kafka_bootstrap_servers = "localhost:9092"
        mock_admin.side_effect = KafkaError("Broker not available")

        result = check_kafka()

        assert result["status"] == "unhealthy"
        assert "Kafka connection failed" in result["message"]


class TestAggregateHealthCheck:
    """Test aggregate health check."""

    @patch("backend.gateway.health.check_kafka")
    @patch("backend.gateway.health.check_redis")
    @patch("backend.gateway.health.check_postgres")
    def test_all_services_healthy(
        self,
        mock_postgres: MagicMock,
        mock_redis: MagicMock,
        mock_kafka: MagicMock,
    ) -> None:
        """Test when all services are healthy."""
        mock_postgres.return_value = {"status": "healthy", "message": "OK"}
        mock_redis.return_value = {"status": "healthy", "message": "OK"}
        mock_kafka.return_value = {"status": "healthy", "message": "OK"}

        result = get_health_status()

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "services" in result
        assert result["services"]["postgres"]["status"] == "healthy"
        assert result["services"]["redis"]["status"] == "healthy"
        assert result["services"]["kafka"]["status"] == "healthy"

    @patch("backend.gateway.health.check_kafka")
    @patch("backend.gateway.health.check_redis")
    @patch("backend.gateway.health.check_postgres")
    def test_one_service_unhealthy(
        self,
        mock_postgres: MagicMock,
        mock_redis: MagicMock,
        mock_kafka: MagicMock,
    ) -> None:
        """Test when one service is unhealthy."""
        mock_postgres.return_value = {"status": "healthy", "message": "OK"}
        mock_redis.return_value = {"status": "unhealthy", "message": "Connection failed"}
        mock_kafka.return_value = {"status": "healthy", "message": "OK"}

        result = get_health_status()

        assert result["status"] == "unhealthy"
        assert result["services"]["redis"]["status"] == "unhealthy"

    @patch("backend.gateway.health.check_kafka")
    @patch("backend.gateway.health.check_redis")
    @patch("backend.gateway.health.check_postgres")
    def test_all_services_unhealthy(
        self,
        mock_postgres: MagicMock,
        mock_redis: MagicMock,
        mock_kafka: MagicMock,
    ) -> None:
        """Test when all services are unhealthy."""
        mock_postgres.return_value = {"status": "unhealthy", "message": "Failed"}
        mock_redis.return_value = {"status": "unhealthy", "message": "Failed"}
        mock_kafka.return_value = {"status": "unhealthy", "message": "Failed"}

        result = get_health_status()

        assert result["status"] == "unhealthy"
        assert result["services"]["postgres"]["status"] == "unhealthy"
        assert result["services"]["redis"]["status"] == "unhealthy"
        assert result["services"]["kafka"]["status"] == "unhealthy"
