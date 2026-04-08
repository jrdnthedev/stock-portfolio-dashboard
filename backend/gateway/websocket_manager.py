"""
WebSocket Manager with Redis-backed connection registry.

Maintains client connections and routes real-time updates to subscribed clients.
Uses Redis for distributed connection tracking across multiple server instances.
"""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

try:
    from backend.gateway.cache import get_cache_service
except ImportError:
    from gateway.cache import get_cache_service

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections with Redis-backed registry.

    Features:
    - Redis-backed connection tracking for horizontal scaling
    - Topic-based subscriptions (e.g., subscribe to specific portfolio IDs)
    - Automatic cleanup on disconnect
    - Broadcast to all clients or specific topics
    """

    def __init__(self) -> None:
        self.cache = get_cache_service()
        # Local in-memory connections (per server instance)
        self.active_connections: dict[str, WebSocket] = {}
        # Local subscriptions: client_id -> set of topics
        self.subscriptions: dict[str, set[str]] = {}

    def _get_redis_key(self, client_id: str) -> str:
        """Generate Redis key for client connection metadata."""
        return f"ws:client:{client_id}"

    def _get_topic_key(self, topic: str) -> str:
        """Generate Redis key for topic subscribers."""
        return f"ws:topic:{topic}"

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket connection
            client_id: Unique identifier for the client
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()

        # Store connection metadata in Redis
        connection_data = {
            "client_id": client_id,
            "connected": True,
            "subscriptions": [],
        }
        self.cache.set(self._get_redis_key(client_id), connection_data, ttl=3600)

        logger.info(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str) -> None:
        """
        Remove a WebSocket connection and clean up subscriptions.

        Args:
            client_id: Unique identifier for the client
        """
        if client_id in self.active_connections:
            # Clean up local state
            del self.active_connections[client_id]

            # Clean up topic subscriptions
            if client_id in self.subscriptions:
                topics = self.subscriptions[client_id].copy()
                for topic in topics:
                    self._remove_from_topic(client_id, topic)
                del self.subscriptions[client_id]

            # Remove from Redis
            self.cache.delete(self._get_redis_key(client_id))

            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal_message(self, message: dict[str, Any], client_id: str) -> bool:
        """
        Send a message to a specific client.

        Args:
            message: JSON-serializable message data
            client_id: Target client identifier

        Returns:
            True if message was sent successfully, False otherwise
        """
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
                return True
            except WebSocketDisconnect:
                logger.warning(f"Client {client_id} disconnected during send")
                self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")

        return False

    async def broadcast(self, message: dict[str, Any]) -> int:
        """
        Broadcast a message to all connected clients.

        Args:
            message: JSON-serializable message data

        Returns:
            Number of clients that received the message
        """
        disconnected = []
        sent_count = 0

        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
                sent_count += 1
            except WebSocketDisconnect:
                disconnected.append(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

        return sent_count

    async def broadcast_to_topic(self, topic: str, message: dict[str, Any]) -> int:
        """
        Broadcast a message to all clients subscribed to a topic.

        Args:
            topic: Topic identifier (e.g., portfolio ID)
            message: JSON-serializable message data

        Returns:
            Number of clients that received the message
        """
        sent_count = 0
        disconnected = []

        # Get all clients subscribed to this topic (local subscriptions)
        for client_id, topics in self.subscriptions.items():
            if topic in topics:
                try:
                    if await self.send_personal_message(message, client_id):
                        sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending to {client_id} on topic {topic}: {e}")
                    disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

        if sent_count > 0:
            logger.debug(f"Broadcast to topic '{topic}': {sent_count} clients")

        return sent_count

    def subscribe(self, client_id: str, topic: str) -> bool:
        """
        Subscribe a client to a topic.

        Args:
            client_id: Client identifier
            topic: Topic to subscribe to

        Returns:
            True if subscription was successful, False otherwise
        """
        if client_id not in self.subscriptions:
            logger.warning(f"Cannot subscribe: client {client_id} not connected")
            return False

        self.subscriptions[client_id].add(topic)
        self._add_to_topic(client_id, topic)

        logger.info(f"Client {client_id} subscribed to topic '{topic}'")
        return True

    def unsubscribe(self, client_id: str, topic: str) -> bool:
        """
        Unsubscribe a client from a topic.

        Args:
            client_id: Client identifier
            topic: Topic to unsubscribe from

        Returns:
            True if unsubscription was successful, False otherwise
        """
        if client_id not in self.subscriptions:
            return False

        self.subscriptions[client_id].discard(topic)
        self._remove_from_topic(client_id, topic)

        logger.info(f"Client {client_id} unsubscribed from topic '{topic}'")
        return True

    def _add_to_topic(self, client_id: str, topic: str) -> None:
        """Add client to topic subscribers in Redis."""
        topic_key = self._get_topic_key(topic)
        # Get current subscribers
        subscribers = self.cache.get(topic_key, default=[])
        if not isinstance(subscribers, list):
            subscribers = []

        if client_id not in subscribers:
            subscribers.append(client_id)
            self.cache.set(topic_key, subscribers, ttl=3600)

    def _remove_from_topic(self, client_id: str, topic: str) -> None:
        """Remove client from topic subscribers in Redis."""
        topic_key = self._get_topic_key(topic)
        subscribers = self.cache.get(topic_key, default=[])
        if isinstance(subscribers, list) and client_id in subscribers:
            subscribers.remove(client_id)
            if subscribers:
                self.cache.set(topic_key, subscribers, ttl=3600)
            else:
                self.cache.delete(topic_key)

    def get_connected_clients(self) -> list[str]:
        """
        Get list of currently connected client IDs on this server instance.

        Returns:
            List of client IDs
        """
        return list(self.active_connections.keys())

    def get_client_subscriptions(self, client_id: str) -> list[str]:
        """
        Get all topics a client is subscribed to.

        Args:
            client_id: Client identifier

        Returns:
            List of topic names
        """
        return list(self.subscriptions.get(client_id, set()))

    def is_connected(self, client_id: str) -> bool:
        """
        Check if a client is connected to this server instance.

        Args:
            client_id: Client identifier

        Returns:
            True if connected, False otherwise
        """
        return client_id in self.active_connections


# Global singleton instance
_manager: WebSocketManager | None = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get or create the global WebSocketManager instance.

    Returns:
        WebSocketManager singleton
    """
    global _manager
    if _manager is None:
        _manager = WebSocketManager()
    return _manager


def create_portfolio_publisher() -> Callable[[str, dict[str, Any]], None]:
    """
    Create a publisher function for portfolio performance updates.

    This function is designed to be passed to PortfolioPerformanceOrchestrator
    as the websocket_publisher parameter.

    Returns:
        Callable that takes (portfolio_id: str, message: dict) and broadcasts
        the message to all clients subscribed to that portfolio.
    """
    manager = get_websocket_manager()

    def publish(portfolio_id: str, message: dict[str, Any]) -> None:
        """
        Publish portfolio performance update to subscribed clients.

        Args:
            portfolio_id: Portfolio identifier (topic)
            message: Performance update message
        """
        import asyncio

        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Schedule the broadcast as a task
        if loop.is_running():
            asyncio.create_task(manager.broadcast_to_topic(portfolio_id, message))
        else:
            loop.run_until_complete(manager.broadcast_to_topic(portfolio_id, message))

    return publish
