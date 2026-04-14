"""
Unit tests for Redis CacheService.
"""

import json
from collections.abc import Generator
from unittest.mock import MagicMock, Mock, patch

import pytest
from redis.exceptions import ConnectionError, RedisError

from backend.gateway.cache import CacheKeyGenerator, CacheService
from tests.test_fixtures import mock_redis  # noqa: F401


class TestCacheKeyGenerator:
    """Test cache key generation utilities."""

    def test_generate_simple_key(self) -> None:
        """Test simple key generation with namespace and parts."""
        key = CacheKeyGenerator.generate("portfolio", 123)
        assert key == "portfolio:123"

    def test_generate_key_with_multiple_parts(self) -> None:
        """Test key generation with multiple parts."""
        key = CacheKeyGenerator.generate("portfolio", 123, "holdings")
        assert key == "portfolio:123:holdings"

    def test_generate_key_with_kwargs(self) -> None:
        """Test key generation with keyword arguments."""
        key = CacheKeyGenerator.generate("market", "AAPL", interval="1d", source="yahoo")
        assert "market:AAPL" in key
        assert "interval=1d" in key
        assert "source=yahoo" in key

    def test_generate_key_kwargs_sorted(self) -> None:
        """Test that kwargs are sorted for consistency."""
        key1 = CacheKeyGenerator.generate("test", z="last", a="first")
        key2 = CacheKeyGenerator.generate("test", a="first", z="last")
        assert key1 == key2

    def test_generate_key_ignores_none_kwargs(self) -> None:
        """Test that None kwargs are filtered out."""
        key = CacheKeyGenerator.generate("test", 123, value=None, active=True)
        assert "value=None" not in key
        assert "active=True" in key

    def test_generate_hash_with_dict(self) -> None:
        """Test hash generation with dictionary."""
        data = {"symbol": "AAPL", "days": 30}
        key = CacheKeyGenerator.generate_hash("query", data)
        assert key.startswith("query:")
        assert len(key.split(":")[-1]) == 32  # MD5 hash length

    def test_generate_hash_with_prefix(self) -> None:
        """Test hash generation with prefix."""
        data = {"test": "data"}
        key = CacheKeyGenerator.generate_hash("query", data, prefix="stocks")
        parts = key.split(":")
        assert parts[0] == "query"
        assert parts[1] == "stocks"
        assert len(parts[2]) == 32

    def test_generate_hash_consistency(self) -> None:
        """Test that same data generates same hash."""
        data = {"symbol": "AAPL", "days": 30}
        key1 = CacheKeyGenerator.generate_hash("query", data)
        key2 = CacheKeyGenerator.generate_hash("query", data)
        assert key1 == key2

    def test_generate_hash_order_independence(self) -> None:
        """Test that dict key order doesn't affect hash."""
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}
        key1 = CacheKeyGenerator.generate_hash("test", data1)
        key2 = CacheKeyGenerator.generate_hash("test", data2)
        assert key1 == key2


class TestCacheService:
    """Test Redis cache service."""

    @pytest.fixture
    def cache_service(self, mock_redis: MagicMock) -> Generator[CacheService, None, None]:
        _ = mock_redis
        """Create a CacheService instance with mocked Redis."""
        service = CacheService(host="localhost", port=6379)
        # Force client initialization
        _ = service.client
        yield service

    def test_initialization(self, mock_redis: MagicMock) -> None:
        _ = mock_redis
        """Test CacheService initialization."""
        service = CacheService(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            default_ttl=3600,
        )
        assert service.default_ttl == 3600
        assert service._host == "redis.example.com"
        assert service._port == 6380
        assert service._db == 1
        assert service._password == "secret"

    def test_client_lazy_initialization(self, mock_redis: MagicMock) -> None:
        """Test that Redis client is lazily initialized."""
        service = CacheService()
        assert service._client is None
        _ = service.client
        assert service._client is not None
        mock_redis.ping.assert_called_once()

    def test_get_exists(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test getting an existing key."""
        test_data = {"id": 123, "value": "test"}
        mock_redis.get.return_value = json.dumps(test_data)

        result = cache_service.get("test:key")

        assert result == test_data
        mock_redis.get.assert_called_once_with("test:key")

    def test_get_not_exists(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test getting a non-existent key."""
        mock_redis.get.return_value = None

        result = cache_service.get("test:key")

        assert result is None
        mock_redis.get.assert_called_once_with("test:key")

    def test_get_with_default(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test getting with default value."""
        mock_redis.get.return_value = None
        default_value = {"default": True}

        result = cache_service.get("test:key", default=default_value)

        assert result == default_value

    def test_get_corrupted_data(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test handling corrupted cached data."""
        mock_redis.get.return_value = "invalid json {{"

        result = cache_service.get("test:key", default="default")

        assert result == "default"
        mock_redis.delete.assert_called_once_with("test:key")

    def test_set_success(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test setting a key."""
        test_data = {"id": 123, "value": "test"}
        mock_redis.set.return_value = True

        result = cache_service.set("test:key", test_data, ttl=3600)

        assert result is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "test:key"
        assert json.loads(call_args[0][1]) == test_data
        assert call_args[1]["ex"] == 3600

    def test_set_with_default_ttl(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test setting with default TTL."""
        mock_redis.set.return_value = True
        cache_service.default_ttl = 1800

        cache_service.set("test:key", {"data": "test"})

        call_args = mock_redis.set.call_args
        assert call_args[1]["ex"] == 1800

    def test_set_with_nx_flag(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test setting with NX flag (only if not exists)."""
        mock_redis.set.return_value = True

        cache_service.set("test:key", {"data": "test"}, nx=True)

        call_args = mock_redis.set.call_args
        assert call_args[1]["nx"] is True

    def test_delete_single_key(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test deleting a single key."""
        mock_redis.delete.return_value = 1

        result = cache_service.delete("test:key")

        assert result == 1
        mock_redis.delete.assert_called_once_with("test:key")

    def test_delete_multiple_keys(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test deleting multiple keys."""
        mock_redis.delete.return_value = 3

        result = cache_service.delete("key1", "key2", "key3")

        assert result == 3
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")

    def test_exists_true(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test checking if key exists (exists)."""
        mock_redis.exists.return_value = 1

        result = cache_service.exists("test:key")

        assert result is True
        mock_redis.exists.assert_called_once_with("test:key")

    def test_exists_false(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test checking if key exists (doesn't exist)."""
        mock_redis.exists.return_value = 0

        result = cache_service.exists("test:key")

        assert result is False

    def test_expire(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test setting expiration time."""
        mock_redis.expire.return_value = True

        result = cache_service.expire("test:key", 3600)

        assert result is True
        mock_redis.expire.assert_called_once_with("test:key", 3600)

    def test_ttl(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test getting TTL."""
        mock_redis.ttl.return_value = 1500

        result = cache_service.ttl("test:key")

        assert result == 1500
        mock_redis.ttl.assert_called_once_with("test:key")

    def test_delete_pattern(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test deleting keys by pattern."""
        mock_redis.scan_iter.return_value = ["portfolio:123:a", "portfolio:123:b"]
        mock_redis.delete.return_value = 2

        result = cache_service.delete_pattern("portfolio:123:*")

        assert result == 2
        mock_redis.scan_iter.assert_called_once_with(match="portfolio:123:*", count=100)
        mock_redis.delete.assert_called_once_with("portfolio:123:a", "portfolio:123:b")

    def test_clear_namespace(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test clearing a namespace."""
        mock_redis.scan_iter.return_value = ["portfolio:123", "portfolio:456"]
        mock_redis.delete.return_value = 2

        result = cache_service.clear_namespace("portfolio")

        assert result == 2
        mock_redis.scan_iter.assert_called_once_with(match="portfolio:*", count=100)

    def test_get_or_set_cache_hit(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test get_or_set with cache hit."""
        cached_data = {"id": 123}
        mock_redis.get.return_value = json.dumps(cached_data)
        factory = Mock(return_value={"id": 456})

        result = cache_service.get_or_set("test:key", factory)

        assert result == cached_data
        factory.assert_not_called()

    def test_get_or_set_cache_miss(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test get_or_set with cache miss."""
        fresh_data = {"id": 456}
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        factory = Mock(return_value=fresh_data)

        result = cache_service.get_or_set("test:key", factory, ttl=3600)

        assert result == fresh_data
        factory.assert_called_once()
        mock_redis.set.assert_called_once()

    def test_mget(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test getting multiple keys."""
        mock_redis.mget.return_value = [
            json.dumps({"id": 1}),
            json.dumps({"id": 2}),
            None,
        ]

        result = cache_service.mget(["key1", "key2", "key3"])

        assert result == [{"id": 1}, {"id": 2}, None]
        mock_redis.mget.assert_called_once_with(["key1", "key2", "key3"])

    def test_mget_empty_list(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test mget with empty list."""
        result = cache_service.mget([])

        assert result == []
        mock_redis.mget.assert_not_called()

    def test_mset(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test setting multiple keys."""
        mapping = {"key1": {"id": 1}, "key2": {"id": 2}}
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [True]

        result = cache_service.mset(mapping, ttl=3600)

        assert result is True
        mock_pipeline.mset.assert_called_once()
        # Check that expire was called for each key
        assert mock_pipeline.expire.call_count == 2

    def test_increment(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test incrementing a counter."""
        mock_redis.incr.return_value = 5

        result = cache_service.increment("counter:key", amount=2)

        assert result == 5
        mock_redis.incr.assert_called_once_with("counter:key", 2)

    def test_increment_with_ttl_on_new_key(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test increment sets TTL on newly created key."""
        mock_redis.incr.return_value = 1  # New key (value equals increment amount)

        cache_service.increment("counter:key", amount=1, ttl=3600)

        mock_redis.expire.assert_called_once_with("counter:key", 3600)

    def test_increment_without_ttl_on_existing_key(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test increment doesn't set TTL on existing key."""
        mock_redis.incr.return_value = 5  # Existing key (value > increment amount)

        cache_service.increment("counter:key", amount=1, ttl=3600)

        mock_redis.expire.assert_not_called()

    def test_flush_all(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test flushing all keys."""
        mock_redis.flushdb.return_value = True

        result = cache_service.flush_all()

        assert result is True
        mock_redis.flushdb.assert_called_once()

    def test_ping_success(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test successful ping."""
        mock_redis.ping.return_value = True

        result = cache_service.ping()

        assert result is True

    def test_ping_failure(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test failed ping."""
        mock_redis.ping.side_effect = RedisError("Connection failed")

        result = cache_service.ping()

        assert result is False

    def test_close(self, cache_service: CacheService, mock_redis: MagicMock) -> None:
        """Test closing connection."""
        cache_service.close()

        mock_redis.close.assert_called_once()
        assert cache_service._client is None

    def test_error_handling_on_get(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test error handling during get operation."""
        mock_redis.get.side_effect = RedisError("Connection error")

        result = cache_service.get("test:key", default="default")

        assert result == "default"

    def test_error_handling_on_set(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test error handling during set operation."""
        mock_redis.set.side_effect = RedisError("Connection error")

        result = cache_service.set("test:key", {"data": "test"})

        assert result is False

    def test_connection_error_on_initialization(self) -> None:
        """Test handling connection error on initialization."""
        with patch("backend.gateway.cache.redis.Redis") as mock_redis_class:
            mock_instance = MagicMock()
            mock_redis_class.return_value = mock_instance
            mock_instance.ping.side_effect = ConnectionError("Cannot connect")

            service = CacheService()

            with pytest.raises(ConnectionError):
                _ = service.client


@patch("backend.config.get_settings")
def test_get_cache_service_singleton(mock_get_settings: Mock) -> None:
    """Test that get_cache_service returns a singleton."""
    from backend.gateway.cache import get_cache_service

    mock_settings = Mock()
    mock_settings.redis_host = "localhost"
    mock_settings.redis_port = 6379
    mock_settings.redis_db = 0
    mock_settings.redis_password = ""
    mock_settings.redis_default_ttl = 1800
    mock_get_settings.return_value = mock_settings

    with patch("backend.gateway.cache.redis.Redis"):
        # Clear the cache to ensure fresh instances
        get_cache_service.cache_clear()

        service1 = get_cache_service()
        service2 = get_cache_service()

        # Should return same instance
        assert service1 is service2
