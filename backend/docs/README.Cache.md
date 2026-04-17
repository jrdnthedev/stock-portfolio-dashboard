# Redis Cache Service

> Production-ready Redis caching service with TTL management and intelligent cache key generation.

📚 **[Documentation Index](README.md)** | 🏠 **[Main README](../README.md)**

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [TTL Constants](#ttl-constants)
- [Common Patterns](#common-patterns)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

---

## Overview

A production-ready Redis caching service with TTL (Time To Live) management and intelligent cache key generation for the Stock Portfolio Dashboard backend.

## Features

- ✅ **TTL Management**: Predefined TTL constants and custom TTL support
- ✅ **Cache Key Generation**: Consistent, hierarchical key generation with hashing support
- ✅ **Batch Operations**: Multi-get and multi-set for efficient bulk operations
- ✅ **Pattern Matching**: Delete keys by pattern or clear entire namespaces
- ✅ **Error Handling**: Graceful degradation with comprehensive error handling
- ✅ **Get-or-Set Pattern**: Atomic cache-aside pattern implementation
- ✅ **Counter Support**: Increment/decrement operations with TTL
- ✅ **Type Safety**: Full type hints for better IDE support
- ✅ **Singleton Pattern**: Efficient resource usage via singleton service

## Installation

Redis is already included in `requirements.txt`:

```txt
redis==5.0.1
types-redis==4.6.0.20240106
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Add Redis configuration to your `.env` file:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_DEFAULT_TTL=1800  # 30 minutes in seconds
```

Configuration is managed through `backend/config.py`:

```python
class Settings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_default_ttl: int = 1800
```

## Quick Start

### Basic Usage

```python
from backend.gateway.cache import cache_service, CacheKeyGenerator

# Simple get/set
cache_service.set("user:123", {"name": "John", "email": "john@example.com"})
user = cache_service.get("user:123")

# With custom TTL
cache_service.set("session:abc", {"user_id": 123}, ttl=300)  # 5 minutes

# Check existence
if cache_service.exists("user:123"):
    print("User found in cache")
```

### Cache Key Generation

```python
from backend.gateway.cache import CacheKeyGenerator

# Simple hierarchical keys
portfolio_key = CacheKeyGenerator.generate("portfolio", 123)
# Result: "portfolio:123"

holdings_key = CacheKeyGenerator.generate("portfolio", 123, "holdings")
# Result: "portfolio:123:holdings"

# With parameters
market_key = CacheKeyGenerator.generate("market", "AAPL", interval="1d", source="yahoo")
# Result: "market:AAPL:interval=1d:source=yahoo"

# Hash-based keys for complex queries
query_data = {"symbols": ["AAPL", "GOOGL"], "days": 30}
query_key = CacheKeyGenerator.generate_hash("query", query_data, prefix="stocks")
# Result: "query:stocks:<md5_hash>"
```

## TTL Constants

The `CacheService` provides predefined TTL constants:

```python
from backend.gateway.cache import CacheService

CacheService.TTL_SHORT   # 300 seconds (5 minutes)
CacheService.TTL_MEDIUM  # 1800 seconds (30 minutes)
CacheService.TTL_LONG    # 3600 seconds (1 hour)
CacheService.TTL_DAY     # 86400 seconds (24 hours)
CacheService.TTL_WEEK    # 604800 seconds (7 days)
```

Usage:

```python
# Cache real-time stock prices (short TTL)
cache_service.set("price:AAPL", {"price": 175.50}, ttl=CacheService.TTL_SHORT)

# Cache daily market data (medium TTL)
cache_service.set("daily:AAPL", daily_data, ttl=CacheService.TTL_MEDIUM)

# Cache fundamentals (long TTL)
cache_service.set("fundamentals:AAPL", fundamentals, ttl=CacheService.TTL_DAY)
```

## Common Patterns

### 1. Get-or-Set Pattern

Automatically fetch and cache data if not in cache:

```python
def fetch_portfolio(user_id: int):
    # Expensive database operation
    return db.query(Portfolio).filter_by(user_id=user_id).first()

cache_key = CacheKeyGenerator.generate("portfolio", user_id)
portfolio = cache_service.get_or_set(
    cache_key,
    lambda: fetch_portfolio(user_id),
    ttl=CacheService.TTL_MEDIUM
)
```

### 2. Batch Operations

Efficiently handle multiple cache operations:

```python
# Multi-set
symbols_data = {
    CacheKeyGenerator.generate("quote", "AAPL"): {"price": 175.50},
    CacheKeyGenerator.generate("quote", "GOOGL"): {"price": 140.25},
    CacheKeyGenerator.generate("quote", "MSFT"): {"price": 420.80},
}
cache_service.mset(symbols_data, ttl=CacheService.TTL_SHORT)

# Multi-get
keys = [
    CacheKeyGenerator.generate("quote", symbol)
    for symbol in ["AAPL", "GOOGL", "MSFT"]
]
quotes = cache_service.mget(keys)
```

### 3. Namespace Invalidation

Clear all cache entries for a specific namespace:

```python
# When user updates profile, clear all user-related cache
user_id = 123
cache_service.clear_namespace(f"user:{user_id}")

# Or use pattern matching
cache_service.delete_pattern(f"portfolio:{user_id}:*")
```

### 4. Counters and Rate Limiting

```python
# Track API requests
api_key = f"api_requests:{user_id}"
request_count = cache_service.increment(api_key, ttl=3600)

if request_count > 100:
    raise RateLimitError("Too many requests")
```

### 5. Conditional Set (Only if Not Exists)

```python
# Set session only if it doesn't exist (e.g., distributed locks)
success = cache_service.set(
    "session:unique123",
    {"user_id": 123},
    ttl=3600,
    nx=True  # Only set if not exists
)

if success:
    print("Session created")
else:
    print("Session already exists")
```

## Application Examples

### Portfolio Service Caching

```python
from backend.gateway.cache import cache_service, CacheKeyGenerator, CacheService

class PortfolioService:
    def get_holdings(self, user_id: int):
        cache_key = CacheKeyGenerator.generate("portfolio", user_id, "holdings")

        def fetch_holdings():
            # Expensive database query
            return self.db.query(Holding).filter_by(user_id=user_id).all()

        return cache_service.get_or_set(
            cache_key,
            fetch_holdings,
            ttl=CacheService.TTL_MEDIUM
        )

    def invalidate_user_cache(self, user_id: int):
        """Clear all portfolio cache for a user."""
        cache_service.clear_namespace(f"portfolio:{user_id}")
```

### Market Data Service Caching

```python
class MarketDataService:
    def get_stock_price(self, symbol: str, interval: str = "1m"):
        cache_key = CacheKeyGenerator.generate(
            "market", symbol, "price", interval=interval
        )

        # Real-time data uses short TTL
        ttl = CacheService.TTL_SHORT if interval == "1m" else CacheService.TTL_MEDIUM

        return cache_service.get_or_set(
            cache_key,
            lambda: self._fetch_price_from_api(symbol, interval),
            ttl=ttl
        )

    def get_fundamentals(self, symbol: str):
        cache_key = CacheKeyGenerator.generate("market", symbol, "fundamentals")

        # Fundamentals change rarely, use long TTL
        return cache_service.get_or_set(
            cache_key,
            lambda: self._fetch_fundamentals_from_api(symbol),
            ttl=CacheService.TTL_DAY
        )
```

## Testing

The cache service includes comprehensive unit tests. Run tests with:

```bash
# Run cache tests
pytest backend/tests/test_cache.py -v

# Run with coverage
pytest backend/tests/test_cache.py --cov=backend.gateway.cache --cov-report=html
```

## API Reference

### CacheService

#### Core Methods

- `get(key, default=None)` - Get value from cache
- `set(key, value, ttl=None, nx=False)` - Set value in cache
- `delete(*keys)` - Delete one or more keys
- `exists(key)` - Check if key exists
- `expire(key, ttl)` - Set/update TTL for key
- `ttl(key)` - Get remaining TTL for key

#### Pattern Operations

- `delete_pattern(pattern)` - Delete keys matching pattern
- `clear_namespace(namespace)` - Clear all keys in namespace

#### Batch Operations

- `mget(keys)` - Get multiple values
- `mset(mapping, ttl=None)` - Set multiple key-value pairs

#### Advanced

- `get_or_set(key, factory, ttl=None)` - Get or set with factory function
- `increment(key, amount=1, ttl=None)` - Increment counter
- `ping()` - Check connection health
- `flush_all()` - Clear all keys (use with caution!)

### CacheKeyGenerator

- `generate(namespace, *parts, **kwargs)` - Generate hierarchical key
- `generate_hash(namespace, data, prefix="")` - Generate hash-based key

## Best Practices

1. **Use Consistent Namespaces**: Organize keys by domain (e.g., `portfolio:`, `market:`, `user:`)

2. **Choose Appropriate TTLs**: Match TTL to data volatility
   - Real-time data: `TTL_SHORT`
   - Session data: `TTL_MEDIUM`
   - Reference data: `TTL_LONG` or `TTL_DAY`

3. **Handle Cache Misses Gracefully**: Always provide fallback logic

4. **Invalidate Strategically**: Clear cache when data changes
   ```python
   # After updating user profile
   cache_service.clear_namespace(f"user:{user_id}")
   ```

5. **Use Get-or-Set Pattern**: Simplifies cache-aside pattern
   ```python
   data = cache_service.get_or_set(key, expensive_operation, ttl=3600)
   ```

6. **Batch When Possible**: Use `mget`/`mset` for multiple operations

7. **Monitor Cache Performance**: Track hit/miss ratios in production

## Troubleshooting

### Connection Issues

```python
# Check Redis connection
if cache_service.ping():
    print("✓ Connected")
else:
    print("✗ Connection failed")
```

### Cache Not Working

1. Verify Redis is running: `redis-cli ping`
2. Check configuration in `.env`
3. Review logs for Redis errors
4. Ensure data is JSON-serializable

### Performance Issues

1. Use batch operations for multiple keys
2. Avoid storing large objects (consider compression)
3. Use appropriate TTLs to prevent memory overflow
4. Monitor Redis memory usage: `redis-cli info memory`

## Related Files

- [`backend/gateway/cache.py`](../backend/gateway/cache.py) - Main implementation
- [`backend/gateway/cache_examples.py`](../backend/gateway/cache_examples.py) - Usage examples
- [`backend/tests/test_cache.py`](../backend/tests/test_cache.py) - Unit tests
- [`backend/config.py`](../backend/config.py) - Configuration settings

## Resources

- [Redis Documentation](https://redis.io/documentation)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Cache-Aside Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside)

---

## See Also

- **[Domain Architecture](README.Domains.md)** - Caching in domain services
- **[WebSocket Manager](README.WebSocket.md)** - Redis pub/sub integration
- **[Response Formatter](README.Formatter.md)** - Caching formatted responses

---

**Last Updated**: April 2026
**Component**: Caching Layer
**Module**: `backend/gateway/cache.py`

