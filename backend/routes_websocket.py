"""WebSocket routes for real-time updates."""

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

try:
    from backend.gateway.websocket_manager import get_websocket_manager
except ImportError:
    from gateway.websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class WebSocketMessage(BaseModel):
    """WebSocket message schema."""

    type: str  # 'subscribe', 'unsubscribe', 'ping'
    payload: dict[str, Any] | None = None


@router.websocket("/portfolio")
async def websocket_portfolio_endpoint(websocket: WebSocket, client_id: str) -> None:
    """
    WebSocket endpoint for real-time portfolio updates.

    Clients can:
    - Subscribe to specific portfolio IDs
    - Receive real-time P&L updates
    - Unsubscribe from portfolios

    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier (passed as query parameter)

    Message Format (Client -> Server):
        {
            "type": "subscribe",
            "payload": {"portfolio_id": "uuid-here"}
        }

        {
            "type": "unsubscribe",
            "payload": {"portfolio_id": "uuid-here"}
        }

        {
            "type": "ping",
            "payload": null
        }

    Message Format (Server -> Client):
        {
            "event": "PortfolioPerformanceUpdated",
            "portfolio_id": "uuid-here",
            "data": {
                "total_market_value": 123456.78,
                "total_unrealized_pnl": 5432.10,
                ...
            }
        }
    """
    manager = get_websocket_manager()

    try:
        # Connect the client
        await manager.connect(websocket, client_id)

        # Send connection confirmation
        await websocket.send_json(
            {"event": "connected", "client_id": client_id, "message": "WebSocket connected"}
        )

        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                # Parse and validate message
                try:
                    message = WebSocketMessage(**data)
                except ValidationError as e:
                    await websocket.send_json(
                        {"event": "error", "message": f"Invalid message format: {e}"}
                    )
                    continue

                # Handle different message types
                if message.type == "subscribe":
                    portfolio_id = message.payload.get("portfolio_id") if message.payload else None
                    if portfolio_id:
                        success = manager.subscribe(client_id, str(portfolio_id))
                        await websocket.send_json(
                            {
                                "event": "subscribed",
                                "portfolio_id": portfolio_id,
                                "success": success,
                            }
                        )
                        logger.info(f"Client {client_id} subscribed to portfolio {portfolio_id}")
                    else:
                        await websocket.send_json(
                            {
                                "event": "error",
                                "message": "portfolio_id required for subscribe",
                            }
                        )

                elif message.type == "unsubscribe":
                    portfolio_id = message.payload.get("portfolio_id") if message.payload else None
                    if portfolio_id:
                        success = manager.unsubscribe(client_id, str(portfolio_id))
                        await websocket.send_json(
                            {
                                "event": "unsubscribed",
                                "portfolio_id": portfolio_id,
                                "success": success,
                            }
                        )
                        logger.info(
                            f"Client {client_id} unsubscribed from portfolio {portfolio_id}"
                        )
                    else:
                        await websocket.send_json(
                            {
                                "event": "error",
                                "message": "portfolio_id required for unsubscribe",
                            }
                        )

                elif message.type == "ping":
                    await websocket.send_json({"event": "pong", "timestamp": data.get("timestamp")})

                else:
                    await websocket.send_json(
                        {
                            "event": "error",
                            "message": f"Unknown message type: {message.type}",
                        }
                    )

            except ValidationError as e:
                logger.error(f"Message validation error: {e}")
                await websocket.send_json({"event": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
        manager.disconnect(client_id)

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/status")
async def websocket_status() -> dict[str, Any]:
    """
    Get WebSocket manager status.

    Returns connection statistics and active clients.
    """
    manager = get_websocket_manager()

    return {
        "status": "healthy",
        "active_connections": len(manager.get_connected_clients()),
        "clients": manager.get_connected_clients(),
    }
