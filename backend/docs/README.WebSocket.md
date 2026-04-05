# WebSocket Manager

**Location**: # noqa: E999 `backend/gateway/websocket_manager.py`

## Overview

The WebSocket Manager provides real-time, bidirectional communication between the backend and connected clients. It manages WebSocket connections, broadcasts updates, and handles connection lifecycle events.

## Purpose

- **Real-Time Updates**: Push live market data and portfolio changes to clients
- **Connection Management**: Track active WebSocket connections
- **Broadcasting**: Efficiently send updates to multiple clients
- **Event Distribution**: Route messages to specific clients or groups

## Architecture

### Current Status

> ⚠️ **Note**: The `websocket_manager.py` file is currently empty. This document describes the planned implementation.

### Planned Implementation

```python
from fastapi import WebSocket
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        # Store active connections by client ID
        self.active_connections: Dict[str, WebSocket] = {}

        # Store subscriptions (client_id -> set of topics)
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
        logger.info(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            del self.subscriptions[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal_message(
        self, message: dict, client_id: str
    ) -> None:
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    async def broadcast_to_topic(
        self, topic: str, message: dict
    ) -> None:
        """Broadcast a message to all clients subscribed to a topic."""
        for client_id, topics in self.subscriptions.items():
            if topic in topics:
                await self.send_personal_message(message, client_id)

    def subscribe(self, client_id: str, topic: str) -> None:
        """Subscribe a client to a topic."""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].add(topic)
            logger.info(f"Client {client_id} subscribed to {topic}")

    def unsubscribe(self, client_id: str, topic: str) -> None:
        """Unsubscribe a client from a topic."""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(topic)
            logger.info(f"Client {client_id} unsubscribed from {topic}")

# Global singleton instance
manager = WebSocketManager()
```

---

## WebSocket Endpoints

### Endpoint: `WS /ws/{client_id}`

**Handler Location**: `backend/main.py` or dedicated WebSocket routes

```python
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str
):
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            # Handle subscription requests
            if data.get("action") == "subscribe":
                topic = data.get("topic")
                manager.subscribe(client_id, topic)
                await manager.send_personal_message(
                    {"type": "subscribed", "topic": topic},
                    client_id
                )

            elif data.get("action") == "unsubscribe":
                topic = data.get("topic")
                manager.unsubscribe(client_id, topic)
                await manager.send_personal_message(
                    {"type": "unsubscribed", "topic": topic},
                    client_id
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)
```

---

## Message Formats

### Client → Server Messages

**Subscribe to Topic**:
```json
{
  "action": "subscribe",
  "topic": "market.prices.AAPL"
}
```

**Unsubscribe from Topic**:
```json
{
  "action": "unsubscribe",
  "topic": "market.prices.AAPL"
}
```

**Request Data**:
```json
{
  "action": "request",
  "type": "portfolio.holdings",
  "portfolio_id": 1
}
```

---

### Server → Client Messages

**Price Update**:
```json
{
  "type": "price.update",
  "topic": "market.prices.AAPL",
  "data": {
    "ticker": "AAPL",
    "price": 180.25,
    "change": 2.15,
    "change_percent": 1.21,
    "volume": 52340000,
    "timestamp": "2026-04-05T15:30:00Z"
  }
}
```

**Portfolio Update**:
```json
{
  "type": "portfolio.update",
  "topic": "portfolio.1",
  "data": {
    "portfolio_id": 1,
    "total_value": 125750.00,
    "total_gain": 25750.00,
    "total_gain_percent": 25.75,
    "updated_at": "2026-04-05T15:30:00Z"
  }
}
```

**Subscription Confirmation**:
```json
{
  "type": "subscribed",
  "topic": "market.prices.AAPL",
  "message": "Successfully subscribed to topic"
}
```

**Error Message**:
```json
{
  "type": "error",
  "message": "Invalid action",
  "details": "Action 'invalid' is not supported"
}
```

---

## Integration with Kafka

The WebSocket manager integrates with Kafka consumers to broadcast real-time updates:

```python
# In price_event_consumer.py
from gateway.websocket_manager import manager

async def consume_price_events():
    """Consume price events from Kafka and broadcast to WebSocket clients."""
    consumer = KafkaConsumer(
        'price-updates',
        bootstrap_servers=settings.kafka_bootstrap_servers,
    )

    for message in consumer:
        price_data = json.loads(message.value)

        # Broadcast to all clients subscribed to this ticker
        topic = f"market.prices.{price_data['ticker']}"
        await manager.broadcast_to_topic(topic, {
            "type": "price.update",
            "topic": topic,
            "data": price_data
        })
```

---

## Connection Store Integration

**Related Module**: `backend/websocket_handler/connection_store.py`

The connection store provides persistent connection tracking:

```python
from websocket_handler.connection_store import ConnectionStore

store = ConnectionStore()

# Register connection
store.add_connection(client_id, websocket, metadata={
    "user_id": user_id,
    "connected_at": datetime.now(),
    "ip_address": request.client.host
})

# Get connections for user
user_connections = store.get_connections_by_user(user_id)

# Remove stale connections
store.cleanup_stale_connections(max_age_seconds=3600)
```

---

## Topic Naming Conventions

### Market Data Topics
- `market.prices.{TICKER}` - Real-time price updates for a specific ticker
- `market.fundamentals.{TICKER}` - Fundamental data updates
- `market.tickers` - New ticker listings

### Portfolio Topics
- `portfolio.{PORTFOLIO_ID}` - Portfolio-level updates
- `portfolio.{PORTFOLIO_ID}.holdings` - Holdings changes
- `portfolio.{PORTFOLIO_ID}.performance` - Performance recalculations

### System Topics
- `system.health` - Health status updates
- `system.notifications` - System-wide notifications

---

## Client Usage Example

### JavaScript/TypeScript Client

```typescript
class PortfolioWebSocket {
  private ws: WebSocket;

  constructor(clientId: string) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');

      // Subscribe to portfolio updates
      this.subscribe('portfolio.1');
      this.subscribe('market.prices.AAPL');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
  }

  subscribe(topic: string) {
    this.ws.send(JSON.stringify({
      action: 'subscribe',
      topic: topic
    }));
  }

  unsubscribe(topic: string) {
    this.ws.send(JSON.stringify({
      action: 'unsubscribe',
      topic: topic
    }));
  }

  handleMessage(message: any) {
    switch (message.type) {
      case 'price.update':
        this.updatePrice(message.data);
        break;
      case 'portfolio.update':
        this.updatePortfolio(message.data);
        break;
      case 'subscribed':
        console.log(`Subscribed to ${message.topic}`);
        break;
      case 'error':
        console.error('Server error:', message.message);
        break;
    }
  }

  private updatePrice(data: any) {
    // Update UI with new price data
  }

  private updatePortfolio(data: any) {
    // Update UI with portfolio changes
  }
}

// Usage
const ws = new PortfolioWebSocket('client-123');
```

---

## Testing

### Unit Tests

**Planned Location**: `backend/tests/test_websocket_manager.py`

```python
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from gateway.websocket_manager import manager

@pytest.fixture
def app():
    app = FastAPI()

    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        await manager.connect(websocket, client_id)
        # ... handler logic

    return app

def test_websocket_connection(app):
    client = TestClient(app)
    with client.websocket_connect("/ws/test-client") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connected"

def test_subscription():
    manager.subscribe("client-1", "market.prices.AAPL")
    assert "market.prices.AAPL" in manager.subscriptions["client-1"]

def test_broadcast_to_topic():
    # Test that messages are only sent to subscribed clients
    pass
```

---

## Best Practices

1. **Connection Limits**: Implement max connections per user to prevent resource exhaustion
2. **Heartbeat/Ping**: Send periodic pings to detect stale connections
3. **Rate Limiting**: Limit message frequency per client to prevent abuse
4. **Authentication**: Validate client identity before accepting connections
5. **Reconnection**: Implement exponential backoff on client side for reconnections
6. **Message Queuing**: Queue messages if broadcast fails temporarily
7. **Graceful Shutdown**: Close all connections cleanly on server shutdown

---

## Configuration

```python
# config.py
WEBSOCKET_MAX_CONNECTIONS_PER_USER = 3
WEBSOCKET_PING_INTERVAL_SECONDS = 30
WEBSOCKET_MESSAGE_RATE_LIMIT = 100  # per minute
WEBSOCKET_MAX_MESSAGE_SIZE = 64 * 1024  # 64KB
```

---

## Monitoring

### Metrics to Track

- Active WebSocket connections count
- Messages sent/received per second
- Subscription count by topic
- Connection duration (average, p95, p99)
- Broadcast failure rate
- Reconnection rate

### Logging

```python
logger.info(f"WebSocket stats: {len(manager.active_connections)} active, "
            f"{sum(len(subs) for subs in manager.subscriptions.values())} total subscriptions")
```

---

## Future Enhancements

- [ ] Implement WebSocket authentication with JWT
- [ ] Add connection pooling and load balancing
- [ ] Support WebSocket compression
- [ ] Implement message acknowledgment
- [ ] Add binary message support for efficiency
- [ ] Create Redis pub/sub integration for multi-instance deployments
- [ ] Add WebSocket metrics endpoint
- [ ] Implement connection rate limiting
