"""API versioning configuration and router management.

This module provides a centralized way to manage API versions across the application.
It supports multiple API versions running simultaneously and provides clear upgrade paths.
"""

from fastapi import APIRouter

from backend.routes_market import router as market_router_v1
from backend.routes_portfolio import router as portfolio_router_v1
from backend.routes_websocket import router as websocket_router


def create_api_v1_router() -> APIRouter:
    """
    Create and configure the API v1 router.

    This function aggregates all v1 endpoints into a single versioned router
    with the /api/v1 prefix.

    Returns:
        APIRouter: Configured v1 API router with all v1 endpoints
    """
    api_v1_router = APIRouter(prefix="/api/v1")

    # Include all v1 route modules
    # Remove the /v1 prefix from individual routers since it's handled here
    api_v1_router.include_router(
        market_router_v1,
        tags=["v1-market"],
    )
    api_v1_router.include_router(
        portfolio_router_v1,
        tags=["v1-portfolio"],
    )

    return api_v1_router


def create_websocket_router() -> APIRouter:
    """
    Create and configure the WebSocket router.

    WebSockets are typically not versioned in the same way as REST APIs
    since they maintain long-lived connections. However, we can version
    the protocol/message format if needed.

    Returns:
        APIRouter: Configured WebSocket router
    """
    ws_router = APIRouter()
    ws_router.include_router(websocket_router, tags=["websocket"])
    return ws_router


# Future version routers can be added here
# Example:
# def create_api_v2_router() -> APIRouter:
#     """Create and configure the API v2 router."""
#     api_v2_router = APIRouter(prefix="/api/v2")
#     # Include v2 route modules
#     return api_v2_router


def get_api_version() -> str:
    """
    Get the current API version.

    Returns:
        str: Current API version (e.g., "1.0.0")
    """
    return "1.0.0"


def get_available_versions() -> list[str]:
    """
    Get list of available API versions.

    Returns:
        list[str]: List of available API version prefixes
    """
    return ["v1"]


# Version compatibility matrix
# Defines which client versions are compatible with which API versions
VERSION_COMPATIBILITY = {
    "v1": {
        "min_client_version": "1.0.0",
        "deprecated": False,
        "sunset_date": None,  # ISO date string when this version will be removed
        "documentation_url": "/docs",
    },
    # Future versions:
    # "v2": {
    #     "min_client_version": "2.0.0",
    #     "deprecated": False,
    #     "sunset_date": None,
    #     "documentation_url": "/docs/v2",
    # },
}


def is_version_supported(version: str) -> bool:
    """
    Check if an API version is supported.

    Args:
        version: API version to check (e.g., "v1", "v2")

    Returns:
        bool: True if version is supported, False otherwise
    """
    return version in VERSION_COMPATIBILITY


def is_version_deprecated(version: str) -> bool:
    """
    Check if an API version is deprecated.

    Args:
        version: API version to check

    Returns:
        bool: True if version is deprecated, False otherwise
    """
    if version not in VERSION_COMPATIBILITY:
        return True
    deprecated = VERSION_COMPATIBILITY[version].get("deprecated", False)
    return bool(deprecated)
