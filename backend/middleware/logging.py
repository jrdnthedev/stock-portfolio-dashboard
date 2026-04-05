"""Request logging middleware for FastAPI.

This middleware logs all incoming HTTP requests and their responses with detailed
information for monitoring and debugging.

Features:
- Generates unique request ID for tracing
- Logs request method, path, query parameters, and client information
- Measures and logs request processing time
- Adds X-Request-ID and X-Process-Time headers to responses
- Logs errors with full stack traces

Example log output:
    INFO: Request started
        {
            "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "method": "GET",
            "path": "/api/stocks/AAPL",
            "query_params": "include_history=true",
            "client_host": "127.0.0.1",
            "user_agent": "Mozilla/5.0..."
        }

    INFO: Request completed
        {
            "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "method": "GET",
            "path": "/api/stocks/AAPL",
            "status_code": 200,
            "duration_ms": 45.23
        }
"""

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract client information
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log incoming request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": client_host,
                "user_agent": user_agent,
            },
        )

        # Process request and measure time
        start_time = time.time()
        try:
            response: Response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time * 1000, 2),
                },
            )

            # Add request ID and processing time to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

            return response

        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(process_time * 1000, 2),
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise
