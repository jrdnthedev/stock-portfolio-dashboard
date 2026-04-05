"""Redis Cache Service with TTL logic and cache key generation."""

import hashlib
import json
import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Any

import redis
from redis.exceptions import ConnectionError, RedisError

logger = logging.getLogger(__name__)


class CacheKeyGenerator:
    """Utility for generating consistent cache keys."""

    @staticmethod
    def generate(
        namespace: str, *parts: str | int | float, **kwargs: str | int | float | bool | None
    ) -> str:
        """Generate cache key: namespace:part1:part2:key=value."""
        key_parts = [namespace, *(str(p) for p in parts)]
        if kwargs:
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
        return ":".join(key_parts)

    @staticmethod
    def generate_hash(namespace: str, data: str | dict | list, prefix: str = "") -> str:
        """Generate hash-based cache key for complex data."""
        data_str = json.dumps(data, sort_keys=True) if isinstance(data, dict | list) else str(data)
        hash_value = hashlib.md5(data_str.encode()).hexdigest()
        parts = [namespace, prefix, hash_value] if prefix else [namespace, hash_value]
        return ":".join(parts)


class CacheService:
    """Redis cache service with TTL management."""

    # TTL constants (seconds)
    TTL_SHORT = 300  # 5 minutes
    TTL_MEDIUM = 1800  # 30 minutes
    TTL_LONG = 3600  # 1 hour
    TTL_DAY = 86400  # 24 hours
    TTL_WEEK = 604800  # 7 days

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        decode_responses: bool = True,
        default_ttl: int = TTL_MEDIUM,
    ):
        """Initialize Redis cache service with lazy connection."""
        self.default_ttl = default_ttl
        self._client: redis.Redis | None = None
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._decode_responses = decode_responses
        self._socket_connect_timeout = 5.0
        self._socket_timeout = 5.0

    @property
    def client(self) -> redis.Redis:
        """Get or create Redis client (lazy initialization)."""
        if self._client is None:
            # Use type: ignore for Redis constructor overload complexity
            self._client = redis.Redis(  # type: ignore[call-overload]
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                socket_timeout=self._socket_timeout,
                socket_connect_timeout=self._socket_connect_timeout,
                decode_responses=self._decode_responses,
            )
            try:
                self._client.ping()
                logger.info("Connected to Redis")
            except ConnectionError as e:
                logger.error(f"Redis connection failed: {e}")
                raise
        return self._client

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache, return default if not found."""
        try:
            cached_data = self.client.get(key)
            if cached_data is not None:
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON for key '{key}', evicting")
                    self.delete(key)
            return default
        except RedisError as e:
            logger.error(f"Redis get error '{key}': {e}")
            return default

    def set(self, key: str, value: Any, ttl: int | None = None, nx: bool = False) -> bool:
        """Set value in cache with TTL (JSON serialized)."""
        try:
            result = self.client.set(key, json.dumps(value), ex=ttl or self.default_ttl, nx=nx)
            return bool(result)
        except (RedisError, TypeError, ValueError) as e:
            logger.error(f"Redis set error '{key}': {e}")
            return False

    def delete(self, *keys: str) -> int:
        """Delete keys from cache, return count deleted."""
        try:
            return self.client.delete(*keys) if keys else 0
        except RedisError as e:
            logger.error(f"Redis delete error: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            logger.error(f"Redis exists error '{key}': {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """Set or update TTL for key."""
        try:
            return bool(self.client.expire(key, ttl))
        except RedisError as e:
            logger.error(f"Redis expire error '{key}': {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get remaining TTL (-1 if no expiry, -2 if not found)."""
        try:
            return self.client.ttl(key)
        except RedisError as e:
            logger.error(f"Redis ttl error '{key}': {e}")
            return -2

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (e.g., 'user:*')."""
        try:
            keys = list(self.client.scan_iter(match=pattern, count=100))
            return self.client.delete(*keys) if keys else 0
        except RedisError as e:
            logger.error(f"Redis delete pattern error '{pattern}': {e}")
            return 0

    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in namespace."""
        return self.delete_pattern(f"{namespace}:*")

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: int | None = None) -> Any:
        """Get from cache or call factory function and cache result."""
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        fresh_value = factory()
        self.set(key, fresh_value, ttl=ttl)
        return fresh_value

    def mget(self, keys: list[str]) -> list[Any]:
        """Get multiple values (None for missing keys)."""
        try:
            if not keys:
                return []
            values = self.client.mget(keys)
            return [
                json.loads(v) if v is not None else None
                for v in values
                if v is None or isinstance(v, str)
            ]
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis mget error: {e}")
            return [None] * len(keys)

    def mset(self, mapping: dict[str, Any], ttl: int | None = None) -> bool:
        """Set multiple key-value pairs with optional TTL."""
        try:
            if not mapping:
                return True

            serialized = {k: json.dumps(v) for k, v in mapping.items()}
            pipe = self.client.pipeline()
            pipe.mset(serialized)  # type: ignore[arg-type]

            if ttl:
                for key in mapping:
                    pipe.expire(key, ttl)

            pipe.execute()
            return True
        except (RedisError, TypeError, ValueError) as e:
            logger.error(f"Redis mset error: {e}")
            return False

    def increment(self, key: str, amount: int = 1, ttl: int | None = None) -> int:
        """Increment counter, set TTL if creating new key."""
        try:
            new_value = self.client.incr(key, amount)
            if ttl and new_value == amount:
                self.client.expire(key, ttl)
            return new_value
        except RedisError as e:
            logger.error(f"Redis increment error '{key}': {e}")
            return 0

    def flush_all(self) -> bool:
        """Flush all keys from current database (WARNING: deletes everything)."""
        try:
            self.client.flushdb()
            logger.warning("Flushed all Redis keys")
            return True
        except RedisError as e:
            logger.error(f"Redis flush error: {e}")
            return False

    def ping(self) -> bool:
        """Check if Redis connection is alive."""
        try:
            return bool(self.client.ping())
        except RedisError:
            return False

    def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Closed Redis connection")


@lru_cache(maxsize=1)
def get_cache_service() -> CacheService:
    """Get singleton CacheService instance."""
    try:
        from backend.config import get_settings
    except ImportError:
        from config import get_settings

    settings = get_settings()
    return CacheService(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password if settings.redis_password else None,
        default_ttl=settings.redis_default_ttl,
    )


# Convenience instance for direct import
cache_service = get_cache_service()
