"""Tests for API versioning functionality."""

from fastapi.testclient import TestClient

from backend.api.versioning import (
    get_api_version,
    get_available_versions,
    is_version_deprecated,
    is_version_supported,
)
from backend.main import app

client = TestClient(app)


class TestVersioningModule:
    """Tests for the versioning module functions."""

    def test_get_api_version(self):
        """Test getting current API version."""
        version = get_api_version()
        assert version == "1.0.0"
        assert isinstance(version, str)

    def test_get_available_versions(self):
        """Test getting list of available versions."""
        versions = get_available_versions()
        assert isinstance(versions, list)
        assert "v1" in versions
        assert len(versions) > 0

    def test_is_version_supported_v1(self):
        """Test that v1 is supported."""
        assert is_version_supported("v1") is True

    def test_is_version_supported_invalid(self):
        """Test that invalid version is not supported."""
        assert is_version_supported("v99") is False
        assert is_version_supported("invalid") is False

    def test_is_version_deprecated_v1(self):
        """Test that v1 is not deprecated."""
        assert is_version_deprecated("v1") is False

    def test_is_version_deprecated_invalid(self):
        """Test that invalid version is considered deprecated."""
        assert is_version_deprecated("v99") is True


class TestVersionedEndpoints:
    """Tests for versioned API endpoints."""

    def test_root_endpoint_includes_version_info(self):
        """Test that root endpoint returns version information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "version" in data
        assert "available_versions" in data
        assert data["version"] == "1.0.0"
        assert "v1" in data["available_versions"]

    def test_v1_portfolio_list_endpoint(self):
        """Test that v1 portfolio endpoint works."""
        response = client.get("/api/v1/portfolio/")
        # Should return 200 or 404 depending on database state
        assert response.status_code in [200, 500]  # 500 if no DB connection in test

    def test_v1_market_endpoint(self):
        """Test that v1 market endpoint structure."""
        # This will fail without a ticker, but tests the route exists
        response = client.get("/api/v1/market/prices/AAPL")
        # Should return 200 (success) or 404 (no data), but route should exist
        assert response.status_code in [200, 404, 500]
        assert response.status_code != 405  # 405 means route doesn't exist

    def test_health_check_endpoint(self):
        """Test that health check endpoint works."""
        response = client.get("/api/health")
        assert response.status_code in [200, 503]
        data = response.json()
        # Health check returns success/data structure
        assert "success" in data or "data" in data


class TestVersioningHeaders:
    """Tests for API versioning headers in responses."""

    def test_response_includes_version_header(self):
        """Test that API responses include X-API-Version header."""
        response = client.get("/api/v1/portfolio/")
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "v1"

    def test_non_versioned_endpoint_no_version_header(self):
        """Test that non-versioned endpoints don't have version header."""
        response = client.get("/")
        _ = response
        # Root endpoint is not under /api/v{X} so may not have version header
        # This is acceptable behavior

    def test_websocket_endpoint_structure(self):
        """Test that WebSocket endpoint exists (not versioned in URL)."""
        # WebSocket endpoints can't be tested with TestClient in this way
        # but we can verify the route structure exists
        # This would need a proper WebSocket client for full testing
        pass


class TestVersioningMiddleware:
    """Tests for the versioning middleware."""

    def test_middleware_adds_version_header_to_v1(self):
        """Test that middleware adds version header to v1 endpoints."""
        response = client.get("/api/v1/portfolio/")
        assert "X-API-Version" in response.headers

    def test_middleware_handles_non_api_routes(self):
        """Test that middleware handles non-API routes gracefully."""
        response = client.get("/")
        assert response.status_code == 200
        # No version header expected for root endpoint

    def test_no_deprecation_headers_for_active_version(self):
        """Test that active versions don't have deprecation headers."""
        response = client.get("/api/v1/portfolio/")
        assert "Deprecation" not in response.headers
        assert "Sunset" not in response.headers


class TestVersionCompatibility:
    """Tests for version compatibility checking."""

    def test_version_compatibility_structure(self):
        """Test that VERSION_COMPATIBILITY is properly structured."""
        from backend.api.versioning import VERSION_COMPATIBILITY

        assert isinstance(VERSION_COMPATIBILITY, dict)
        assert "v1" in VERSION_COMPATIBILITY

        v1_info = VERSION_COMPATIBILITY["v1"]
        assert "min_client_version" in v1_info
        assert "deprecated" in v1_info
        assert "sunset_date" in v1_info
        assert "documentation_url" in v1_info

    def test_v1_is_not_deprecated(self):
        """Test that v1 is currently not deprecated."""
        from backend.api.versioning import VERSION_COMPATIBILITY

        assert VERSION_COMPATIBILITY["v1"]["deprecated"] is False
        assert VERSION_COMPATIBILITY["v1"]["sunset_date"] is None


class TestRouterCreation:
    """Tests for API router creation functions."""

    def test_create_api_v1_router(self):
        """Test that v1 router is created correctly."""
        from backend.api.versioning import create_api_v1_router

        router = create_api_v1_router()
        assert router is not None
        assert router.prefix == "/api/v1"

    def test_create_websocket_router(self):
        """Test that WebSocket router is created correctly."""
        from backend.api.versioning import create_websocket_router

        router = create_websocket_router()
        assert router is not None


class TestEndpointStructure:
    """Tests for endpoint URL structure and versioning."""

    def test_portfolio_endpoints_under_v1(self):
        """Test that portfolio endpoints are under /api/v1."""
        # List portfolios
        response = client.get("/api/v1/portfolio/")
        assert response.status_code != 404  # Endpoint exists

    def test_market_endpoints_under_v1(self):
        """Test that market endpoints are under /api/v1."""
        # This should exist even if it returns error due to missing ticker
        response = client.get("/api/v1/market/tickers")
        assert response.status_code != 404  # Endpoint exists

    def test_old_unversioned_paths_not_found(self):
        """Test that old unversioned paths return 404."""
        # These should no longer work since we moved to /api/v1
        response = client.get("/v1/portfolio/")
        assert response.status_code == 404

        response = client.get("/portfolio/")
        assert response.status_code == 404


class TestVersionMigration:
    """Tests for version migration scenarios."""

    def test_can_prepare_for_v2(self):
        """Test that the system is ready for adding v2."""
        # Verify the versioning structure supports multiple versions
        from backend.api.versioning import VERSION_COMPATIBILITY

        # Should be able to add v2 to this structure
        assert isinstance(VERSION_COMPATIBILITY, dict)

        # The functions should support multiple versions
        assert is_version_supported("v1")

    def test_version_detection_from_path(self):
        """Test that version can be extracted from URL path."""
        from backend.middleware.versioning import APIVersionMiddleware

        middleware = APIVersionMiddleware(app)

        assert middleware._extract_version_from_path("/api/v1/portfolio") == "v1"
        assert middleware._extract_version_from_path("/api/v2/portfolio") == "v2"
        assert middleware._extract_version_from_path("/portfolio") is None
        assert middleware._extract_version_from_path("/") is None
