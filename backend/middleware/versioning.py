"""API versioning middleware for deprecation warnings and version validation.

This middleware adds versioning headers and deprecation warnings to API responses.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any, cast

from backend.api.versioning import (
    VERSION_COMPATIBILITY,
    is_version_deprecated,
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle API versioning headers and deprecation warnings.

    This middleware:
    - Adds API version headers to responses
    - Warns clients when using deprecated API versions
    - Logs API version usage for analytics
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and add versioning headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response: HTTP response with versioning headers
        """
        # Extract API version from path (e.g., /api/v1/...)
        version = self._extract_version_from_path(request.url.path)

        # Process request
        response: Response = await call_next(request)

        # Add version headers
        if version:
            response.headers["X-API-Version"] = version

            # Add deprecation warning if version is deprecated
            if is_version_deprecated(version):
                version_info = cast(dict[str, Any], VERSION_COMPATIBILITY.get(version, {}))
                sunset_date_raw = version_info.get("sunset_date")
                sunset_date = str(sunset_date_raw) if sunset_date_raw is not None else "TBD"

                warning_msg = f"API version {version} is deprecated"
                if sunset_date and sunset_date != "None" and sunset_date != "TBD":
                    warning_msg += f" and will be removed on {sunset_date}"

                response.headers["Deprecation"] = "true"
                response.headers["Sunset"] = sunset_date
                response.headers["Warning"] = f'299 - "{warning_msg}"'
                response.headers["Link"] = (
                    f'<{version_info.get("documentation_url", "/docs")}>; rel="documentation"'
                )

                logger.warning(
                    f"Deprecated API version {version} used",
                    extra={
                        "path": request.url.path,
                        "client": request.client.host if request.client else "unknown",
                        "version": version,
                    },
                )

        return response

    @staticmethod
    def _extract_version_from_path(path: str) -> str | None:
        """
        Extract API version from request path.

        Args:
            path: Request URL path

        Returns:
            str | None: Extracted version (e.g., "v1") or None if not found
        """
        parts = path.split("/")
        # Look for /api/v{number} pattern
        for i, part in enumerate(parts):
            if part == "api" and i + 1 < len(parts):
                potential_version = parts[i + 1]
                if potential_version.startswith("v") and potential_version[1:].isdigit():
                    return potential_version
        return None
