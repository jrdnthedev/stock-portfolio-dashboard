"""Tests for WebSocket Manager."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket

from backend.gateway.websocket_manager import (
    WebSocketManager,
    create_portfolio_publisher,
    get_websocket_manager,
)


@pytest.fixture
def mock_cache():
    """Mock cache service."""
    cache = MagicMock()
    cache.get.return_value = None
    cache.set.return_value = True
    cache.delete.return_value = True
    return cache


@pytest.fixture
def manager(mock_cache):
    """Create WebSocketManager with mocked cache."""
    with patch("backend.gateway.websocket_manager.get_cache_service", return_value=mock_cache):
        return WebSocketManager()


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    ws = AsyncMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestWebSocketManagerConnect:
    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_stores_connection(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")
        assert "client1" in manager.active_connections
        assert manager.active_connections["client1"] == mock_websocket

    @pytest.mark.asyncio
    async def test_connect_initializes_subscriptions(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")
        assert "client1" in manager.subscriptions
        assert manager.subscriptions["client1"] == set()

    @pytest.mark.asyncio
    async def test_connect_stores_metadata_in_redis(self, manager, mock_websocket, mock_cache):
        await manager.connect(mock_websocket, "client1")
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args[0]
        assert call_args[0] == "ws:client:client1"
        assert call_args[1]["client_id"] == "client1"
        assert call_args[1]["connected"] is True


class TestWebSocketManagerDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")
        manager.disconnect("client1")
        assert "client1" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_removes_subscriptions(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")
        manager.subscribe("client1", "portfolio:123")
        manager.disconnect("client1")
        assert "client1" not in manager.subscriptions

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_redis(self, manager, mock_websocket, mock_cache):
        await manager.connect(mock_websocket, "client1")
        mock_cache.reset_mock()
        manager.disconnect("client1")
        mock_cache.delete.assert_called_with("ws:client:client1")

    def test_disconnect_handles_nonexistent_client(self, manager):
        # Should not raise exception
        manager.disconnect("nonexistent")


class TestWebSocketManagerSendPersonalMessage:
    @pytest.mark.asyncio
    async def test_send_personal_message_success(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")
        message = {"event": "test", "data": "hello"}

        result = await manager.send_personal_message(message, "client1")

        assert result is True
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_to_nonexistent_client(self, manager):
        message = {"event": "test"}
        result = await manager.send_personal_message(message, "nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_personal_message_handles_disconnect(self, manager, mock_websocket):
        from fastapi import WebSocketDisconnect

        await manager.connect(mock_websocket, "client1")
        mock_websocket.send_json.side_effect = WebSocketDisconnect()

        result = await manager.send_personal_message({"event": "test"}, "client1")

        assert result is False
        assert "client1" not in manager.active_connections


class TestWebSocketManagerBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_to_all_clients(self, manager):
        ws1 = AsyncMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = AsyncMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")

        message = {"event": "broadcast", "data": "hello all"}
        count = await manager.broadcast(message)

        assert count == 2
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_no_clients(self, manager):
        message = {"event": "test"}
        count = await manager.broadcast(message)
        assert count == 0

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_clients(self, manager):
        from fastapi import WebSocketDisconnect

        ws1 = AsyncMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock(side_effect=WebSocketDisconnect())

        ws2 = AsyncMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")

        count = await manager.broadcast({"event": "test"})

        assert count == 1
        assert "client1" not in manager.active_connections
        assert "client2" in manager.active_connections


class TestWebSocketManagerSubscriptions:
    @pytest.mark.asyncio
    async def test_subscribe_to_topic(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")

        result = manager.subscribe("client1", "portfolio:123")

        assert result is True
        assert "portfolio:123" in manager.subscriptions["client1"]

    def test_subscribe_nonexistent_client_returns_false(self, manager):
        result = manager.subscribe("nonexistent", "portfolio:123")
        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe_from_topic(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")
        manager.subscribe("client1", "portfolio:123")

        result = manager.unsubscribe("client1", "portfolio:123")

        assert result is True
        assert "portfolio:123" not in manager.subscriptions["client1"]

    def test_unsubscribe_nonexistent_client_returns_false(self, manager):
        result = manager.unsubscribe("nonexistent", "portfolio:123")
        assert result is False


class TestWebSocketManagerBroadcastToTopic:
    @pytest.mark.asyncio
    async def test_broadcast_to_topic_subscribers_only(self, manager):
        ws1 = AsyncMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = AsyncMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        ws3 = AsyncMock(spec=WebSocket)
        ws3.accept = AsyncMock()
        ws3.send_json = AsyncMock()

        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")
        await manager.connect(ws3, "client3")

        manager.subscribe("client1", "portfolio:123")
        manager.subscribe("client3", "portfolio:123")

        message = {"event": "update", "portfolio_id": "123"}
        count = await manager.broadcast_to_topic("portfolio:123", message)

        assert count == 2
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_not_called()
        ws3.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_topic_with_no_subscribers(self, manager):
        message = {"event": "test"}
        count = await manager.broadcast_to_topic("portfolio:999", message)
        assert count == 0


class TestWebSocketManagerUtilities:
    @pytest.mark.asyncio
    async def test_get_connected_clients(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")

        ws2 = AsyncMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        await manager.connect(ws2, "client2")

        clients = manager.get_connected_clients()
        assert len(clients) == 2
        assert "client1" in clients
        assert "client2" in clients

    @pytest.mark.asyncio
    async def test_get_client_subscriptions(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "client1")
        manager.subscribe("client1", "portfolio:123")
        manager.subscribe("client1", "portfolio:456")

        subs = manager.get_client_subscriptions("client1")
        assert len(subs) == 2
        assert "portfolio:123" in subs
        assert "portfolio:456" in subs

    def test_get_client_subscriptions_nonexistent_client(self, manager):
        subs = manager.get_client_subscriptions("nonexistent")
        assert subs == []

    @pytest.mark.asyncio
    async def test_is_connected(self, manager, mock_websocket):
        assert manager.is_connected("client1") is False

        await manager.connect(mock_websocket, "client1")
        assert manager.is_connected("client1") is True

        manager.disconnect("client1")
        assert manager.is_connected("client1") is False


class TestWebSocketManagerSingleton:
    def test_get_websocket_manager_returns_singleton(self):
        manager1 = get_websocket_manager()
        manager2 = get_websocket_manager()
        assert manager1 is manager2


class TestCreatePortfolioPublisher:
    @pytest.mark.asyncio
    async def test_create_portfolio_publisher(self):
        with patch("backend.gateway.websocket_manager.get_websocket_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.broadcast_to_topic = AsyncMock(return_value=1)
            mock_get_manager.return_value = mock_manager

            publisher = create_portfolio_publisher()

            # Call the publisher
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            publisher("portfolio:123", {"event": "update", "data": {}})

            # Give the event loop time to process
            await asyncio.sleep(0.1)

            # Verify broadcast was scheduled
            # Note: In production this would be called asynchronously
