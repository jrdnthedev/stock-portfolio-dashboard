# Health Check Module

**Location**: # noqa: E999 `backend/gateway/health.py`

## Overview

The health check module provides comprehensive monitoring of critical infrastructure dependencies. It performs active health checks on PostgreSQL, Redis, and Kafka to ensure the backend services are operational.

## Purpose

- **Service Monitoring**: Verify connectivity to external dependencies
- **Operational Visibility**: Provide health status for monitoring systems
- **Incident Detection**: Enable early detection of infrastructure failures
- **Load Balancer Integration**: Support health check endpoints for load balancers

## Architecture

### Health Check Functions

#### `check_postgres() -> dict[str, Any]`

Verifies PostgreSQL database connectivity by executing a simple query.

**Implementation**:
```python
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    _ = result.fetchone()
```

**Returns**:
- `status`: "healthy" or "unhealthy"
- `message`: Descriptive status message
- `response_time_ms`: Query execution time (currently 0, can be enhanced)

**Error Handling**: Catches all exceptions and returns unhealthy status with error details.

---

#### `check_redis() -> dict[str, Any]`

Verifies Redis connectivity using the `PING` command.

**Implementation**:
```python
cache = get_cache_service()
if cache.ping():
    return {"status": "healthy", ...}
```

**Returns**:
- `status`: "healthy" or "unhealthy"
- `message`: Descriptive status message
- `response_time_ms`: Ping latency

**Edge Cases**:
- Redis connection exists but ping fails → unhealthy
- Exception during ping → unhealthy with error message

---

#### `check_kafka() -> dict[str, Any]`

Verifies Kafka broker connectivity by listing topics.

**Implementation**:
```python
admin_client = KafkaAdminClient(
    bootstrap_servers=settings.kafka_bootstrap_servers,
    client_id="health-check",
)
topics = admin_client.list_topics()
```

**Returns**:
- `status`: "healthy" or "unhealthy"
- `message`: Status with topic count or error details
- `response_time_ms`: Operation latency

**Cleanup**: Always closes the admin client in a finally block.

---

#### `get_health_status() -> dict[str, Any]`

Aggregates all health checks into a single response.

**Response Structure**:
```json
{
  "status": "healthy" | "unhealthy",
  "message": "All systems operational" | "Some systems are unhealthy",
  "timestamp": "2026-04-05T15:30:00.000000Z",
  "checks": {
    "postgres": { "status": "healthy", ... },
    "redis": { "status": "healthy", ... },
    "kafka": { "status": "healthy", ... }
  }
}
```

**Status Logic**:
- Overall status is "healthy" only if **all** checks are healthy
- Single unhealthy check → overall status becomes "unhealthy"

---

## HTTP Integration

### Endpoint: `GET /api/health`

**Location**: `backend/main.py`

```python
@app.get("/api/health", response_model=None)
async def health_check() -> JSONResponse:
    health_status = get_health_status()
    status_code = (
        status.HTTP_200_OK
        if health_status["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    response = (
        success_response(data=health_status, message="Health check completed")
        if health_status["status"] == "healthy"
        else error_response(message="Service unhealthy", errors=[health_status])
    )
    return JSONResponse(content=response, status_code=status_code)
```

**Status Codes**:
- `200 OK`: All systems healthy
- `503 Service Unavailable`: One or more systems unhealthy

**Response Envelope**:
- Uses standard `success_response()` or `error_response()` format
- Includes full health check details in data/errors

---

## Testing

### Unit Tests

**Location**: `backend/tests/test_health.py`

**Coverage**: 94% (10 tests)

**Test Cases**:
1. `test_check_postgres_healthy` - Successful PostgreSQL connection
2. `test_check_postgres_unhealthy` - PostgreSQL connection failure
3. `test_check_redis_healthy` - Successful Redis ping
4. `test_check_redis_ping_failed` - Redis ping returns False
5. `test_check_redis_exception` - Redis raises exception
6. `test_check_kafka_healthy` - Successful Kafka topic listing
7. `test_check_kafka_failed` - Kafka connection failure
8. `test_get_health_status_all_healthy` - All checks pass
9. `test_get_health_status_one_unhealthy` - One check fails
10. `test_get_health_status_all_unhealthy` - All checks fail

**Mocking Strategy**:
- Mock `engine.connect()` for PostgreSQL
- Mock `get_cache_service()` for Redis
- Mock `KafkaAdminClient` for Kafka

---

## Configuration

### Environment Variables

```python
# config.py
kafka_bootstrap_servers: str = "localhost:9092"
```

**PostgreSQL**: Configured via `database/database.py` engine
**Redis**: Configured via `gateway/cache.py` service
**Kafka**: Configured via `config.py` settings

---

## Usage Examples

### Programmatic Usage

```python
from gateway.health import get_health_status

health = get_health_status()
if health["status"] == "healthy":
    print("All systems operational")
else:
    print(f"Issues detected: {health['checks']}")
```

### HTTP Request

```bash
curl http://localhost:8000/api/health
```

**Healthy Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "message": "All systems operational",
    "timestamp": "2026-04-05T15:30:00.000000Z",
    "checks": {
      "postgres": {"status": "healthy", "message": "PostgreSQL connection successful"},
      "redis": {"status": "healthy", "message": "Redis connection successful"},
      "kafka": {"status": "healthy", "message": "Kafka cluster is healthy (3 topics found)"}
    }
  },
  "message": "Health check completed",
  "errors": null,
  "metadata": null,
  "timestamp": "2026-04-05T15:30:00.123456Z"
}
```

**Unhealthy Response** (503 Service Unavailable):
```json
{
  "success": false,
  "data": null,
  "message": "Service unhealthy",
  "errors": [{
    "status": "unhealthy",
    "message": "Some systems are unhealthy",
    "checks": {
      "postgres": {"status": "healthy", ...},
      "redis": {"status": "unhealthy", "message": "Redis connection failed: ..."},
      "kafka": {"status": "healthy", ...}
    }
  }],
  "metadata": null,
  "timestamp": "2026-04-05T15:30:00.123456Z"
}
```

---

## Best Practices

1. **Monitoring Integration**: Configure your monitoring system (Prometheus, Datadog, New Relic) to poll `/api/health` regularly
2. **Load Balancer Configuration**: Use this endpoint for load balancer health checks
3. **Alert Thresholds**: Set alerts when health check returns 503 for more than 2-3 consecutive polls
4. **Timeout Configuration**: Set reasonable timeouts for health checks (e.g., 5-10 seconds)
5. **Logging**: All health check failures are logged at ERROR level for debugging

---

## Future Enhancements

- [ ] Add response time measurement for each check
- [ ] Implement circuit breaker pattern for degraded dependencies
- [ ] Add disk space and memory usage checks
- [ ] Support shallow vs deep health checks
- [ ] Add configurable timeouts per dependency
- [ ] Include version information in health response
- [ ] Add dependency graph visualization
