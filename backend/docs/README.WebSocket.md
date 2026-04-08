# WebSocket Real-Time Updates

This document describes the WebSocket implementation for real-time portfolio performance updates in the Stock Portfolio Dashboard. # noqa E999

## Architecture Overview

The WebSocket system enables real-time push notifications to connected clients when portfolio performance changes due to price updates:

```
PricePublisher → Kafka (market.prices.live) → PriceEventConsumer →
PortfolioPerformanceOrchestrator → PerformanceCalculator →
WebSocketManager → Connected Clients
```

## Components

### 1. WebSocketManager (`backend/gateway/websocket_manager.py`)

Manages WebSocket connections with Redis-backed registry for horizontal scaling.

**Key Features:**
- Connection lifecycle management (connect/disconnect)
- Topic-based subscriptions (portfolio IDs)
- Broadcasting to all clients or specific topics
- Redis-backed connection tracking with TTL (3600 seconds)
- Automatic cleanup on disconnect
- Singleton pattern for shared instance

**API Methods:**
```python
# Connection Management
await manager.connect(websocket, client_id)
manager.disconnect(client_id)

# Messaging
await manager.send_personal_message(client_id, message)
await manager.broadcast(message)
await manager.broadcast_to_topic(topic, message)

# Subscriptions
manager.subscribe(client_id, topic)
manager.unsubscribe(client_id, topic)

# Utilities
manager.get_connected_clients() -> list[str]
manager.get_client_subscriptions(client_id) -> set[str]
manager.is_connected(client_id) -> bool
```

### 2. WebSocket Routes (`backend/routes_websocket.py`)

Provides HTTP endpoints for WebSocket connections and status monitoring.

**Endpoints:**

#### WebSocket Connection: `ws://localhost:8000/ws/portfolio?client_id=<uuid>`

Client connects to this endpoint with a unique client_id in query parameters.

**Client → Server Messages:**

```json
// Subscribe to portfolio updates
{
    "type": "subscribe",
    "payload": {
        "portfolio_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}

// Unsubscribe from portfolio
{
    "type": "unsubscribe",
    "payload": {
        "portfolio_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}

// Heartbeat ping
{
    "type": "ping",
    "payload": null
}
```

**Server → Client Messages:**

```json
// Connection confirmation
{
    "event": "connected",
    "client_id": "abc123",
    "message": "WebSocket connected"
}

// Subscription confirmation
{
    "event": "subscribed",
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "success": true
}

// Portfolio performance update
{
    "event": "PortfolioPerformanceUpdated",
    "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
    "data": {
        "total_market_value": 123456.78,
        "total_unrealized_pnl": 5432.10,
        "total_unrealized_pnl_percent": 4.62,
        "holdings": [
            {
                "ticker_id": 1,
                "quantity": 100,
                "market_value": 15000.00,
                "unrealized_pnl": 500.00,
                "unrealized_pnl_percent": 3.45,
                "weight": 12.15
            }
        ]
    }
}

// Pong response
{
    "event": "pong",
    "timestamp": 1234567890
}

// Error message
{
    "event": "error",
    "message": "Invalid message format"
}
```

#### Status Endpoint: `GET /ws/status`

Returns connection statistics:

```json
{
    "status": "healthy",
    "active_connections": 5,
    "clients": ["client-1", "client-2", "client-3"]
}
```

### 3. Integration with PortfolioPerformanceOrchestrator

The WebSocketManager is integrated into the main application via the `create_portfolio_publisher()` factory function:

```python
# In backend/main.py
from backend.gateway.websocket_manager import create_portfolio_publisher

# Create WebSocket publisher
websocket_publisher = create_portfolio_publisher()

# Pass to orchestrator
portfolio_orchestrator = PortfolioPerformanceOrchestrator(
    portfolio_service=portfolio_service,
    performance_calculator=performance_calculator,
    price_consumer=price_consumer,
    websocket_publisher=websocket_publisher,  # Enables real-time updates
)
```

When a price update event is received:
1. `PriceEventConsumer` receives event from Kafka
2. `PortfolioPerformanceOrchestrator._on_price_updated()` processes event
3. `PerformanceCalculator` updates prices and recalculates P&L
4. `websocket_publisher` broadcasts to subscribed clients
5. Only clients subscribed to affected portfolios receive updates

## Client Implementation Example

### JavaScript/TypeScript WebSocket Client

```typescript
class PortfolioWebSocketClient {
    private ws: WebSocket;
    private clientId: string;

    constructor(clientId: string) {
        this.clientId = clientId;
        this.connect();
    }

    connect() {
        this.ws = new WebSocket(`ws://localhost:8000/ws/portfolio?client_id=${this.clientId}`);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
            // Implement reconnection logic here
        };
    }

    subscribe(portfolioId: string) {
        this.send({
            type: 'subscribe',
            payload: { portfolio_id: portfolioId }
        });
    }

    unsubscribe(portfolioId: string) {
        this.send({
            type: 'unsubscribe',
            payload: { portfolio_id: portfolioId }
        });
    }

    ping() {
        this.send({
            type: 'ping',
            payload: { timestamp: Date.now() }
        });
    }

    private send(message: any) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    private handleMessage(message: any) {
        switch (message.event) {
            case 'connected':
                console.log('Connection confirmed:', message.client_id);
                break;

            case 'subscribed':
                console.log('Subscribed to portfolio:', message.portfolio_id);
                break;

            case 'PortfolioPerformanceUpdated':
                console.log('Portfolio update:', message.data);
                // Update UI with new performance data
                this.updatePortfolioUI(message.portfolio_id, message.data);
                break;

            case 'pong':
                console.log('Pong received');
                break;

            case 'error':
                console.error('Server error:', message.message);
                break;
        }
    }

    private updatePortfolioUI(portfolioId: string, data: any) {
        // Implement UI update logic
        // This is where you'd update Angular components, React state, etc.
    }

    disconnect() {
        this.ws.close();
    }
}

// Usage
const client = new PortfolioWebSocketClient('unique-client-id-123');
client.subscribe('550e8400-e29b-41d4-a716-446655440000');
```

## Testing

The WebSocket implementation includes comprehensive test coverage (26 tests):

```bash
# Run WebSocket tests
pytest backend/tests/test_websocket_manager.py -v

# All 26 tests pass, covering:
# - Connection management (connect/disconnect)
# - Personal messaging
# - Broadcasting (all clients and topic-specific)
# - Subscription management
# - Error handling (WebSocketDisconnect)
# - Singleton pattern
# - Redis integration
# - create_portfolio_publisher() factory function
```

## Redis Data Structure

WebSocket connection data is stored in Redis:

### Connection Metadata
```
Key: ws:client:{client_id}
Type: Hash
TTL: 3600 seconds
Fields:
  - connected_at: ISO timestamp
  - client_id: string
```

### Topic Subscriptions
```
Key: ws:topic:{topic}
Type: Set
TTL: 3600 seconds
Members: List of client_ids subscribed to the topic
```

## Scaling Considerations

### Horizontal Scaling
The Redis-backed connection registry enables horizontal scaling:
- Multiple FastAPI instances can run behind a load balancer
- Each instance maintains local WebSocket connections
- Redis tracks all connections across instances
- Broadcasting queries Redis to find all subscribers

### Connection Limits
- Default connection TTL: 3600 seconds
- Redis handles connection tracking overhead
- Consider connection pooling for high-traffic scenarios

### Performance
- Local connection dict for fast lookups
- Redis for distributed state
- Async/await for non-blocking operations
- Automatic cleanup prevents memory leaks

## Troubleshooting

### Connection Issues
```python
# Check active connections
GET /ws/status

# Verify client is connected
manager.is_connected(client_id)

# Check subscriptions
manager.get_client_subscriptions(client_id)
```

### Redis Issues
```python
# Verify Redis connection
from backend.gateway.cache import get_cache_service
cache = get_cache_service()
cache.set("test", "value")
assert cache.get("test") == "value"
```

### Missing Updates
1. Verify client subscription: `manager.get_client_subscriptions(client_id)`
2. Check portfolio has holdings with the ticker
3. Verify PricePublisher is running
4. Check PriceEventConsumer logs
5. Verify PerformanceCalculator received price update

## Security Considerations

### Authentication
Currently, the WebSocket endpoint does not enforce authentication. Consider adding:
- JWT token validation in query parameters or headers
- Client ID validation against authenticated user
- Rate limiting per client

### Authorization
Implement portfolio access control:
- Verify client has permission to subscribe to portfolio
- Reject subscriptions for inaccessible portfolios
- Log unauthorized access attempts

Example middleware:
```python
async def verify_portfolio_access(client_id: str, portfolio_id: str) -> bool:
    # Implement your authorization logic
    # Check if client_id has access to portfolio_id
    return True  # placeholder
```

## Monitoring

### Metrics to Track
- Active connection count
- Messages sent per second
- Subscription counts per portfolio
- Disconnection rate
- Error rate

### Logging
All key events are logged:
- Connection/disconnection events
- Subscription changes
- Broadcast operations
- Error conditions

Check logs:
```bash
grep "WebSocket" backend.log
grep "Client.*connected" backend.log
grep "Portfolio update broadcast" backend.log
```

## Implementation Status

✅ **COMPLETED:**
- WebSocketManager with full connection lifecycle
- Redis-backed connection registry for horizontal scaling
- Topic-based subscription system
- Broadcasting to all clients or specific topics
- create_portfolio_publisher() factory function
- Integration with PortfolioPerformanceOrchestrator
- WebSocket route endpoint (`/ws/portfolio`)
- Status monitoring endpoint (`/ws/status`)
- Comprehensive test suite (26 tests passing)
- Error handling and automatic cleanup

🔄 **NEXT STEPS:**
1. Frontend integration - build Angular WebSocket service
2. Add JWT authentication to WebSocket endpoint
3. Implement portfolio authorization checks
4. Add monitoring/metrics collection (Prometheus)
5. Load testing with multiple concurrent connections
6. Implement automatic reconnection with exponential backoff
7. Add message queuing for offline clients
