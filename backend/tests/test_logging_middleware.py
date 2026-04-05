"""Unit tests for request logging middleware."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware.logging import RequestLoggingMiddleware


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI app with logging middleware."""
    test_app = FastAPI()
    test_app.add_middleware(RequestLoggingMiddleware)

    @test_app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"message": "test"}

    @test_app.get("/error")
    async def error_endpoint() -> None:
        raise ValueError("Test error")

    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""

    @patch("middleware.logging.logger")
    def test_logs_successful_request(self, mock_logger: MagicMock, client: TestClient) -> None:
        """Test that successful requests are logged."""
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers

        # Verify logging calls
        assert mock_logger.info.call_count == 2  # Start and completion
        start_call = mock_logger.info.call_args_list[0]
        completion_call = mock_logger.info.call_args_list[1]

        # Check start log
        assert "Request started" in start_call[0][0]
        assert start_call[1]["extra"]["method"] == "GET"
        assert start_call[1]["extra"]["path"] == "/test"
        assert "request_id" in start_call[1]["extra"]

        # Check completion log
        assert "Request completed" in completion_call[0][0]
        assert completion_call[1]["extra"]["status_code"] == 200
        assert "duration_ms" in completion_call[1]["extra"]

    @patch("middleware.logging.logger")
    def test_logs_request_with_query_params(
        self, mock_logger: MagicMock, client: TestClient
    ) -> None:
        """Test that query parameters are logged."""
        response = client.get("/test?param1=value1&param2=value2")

        assert response.status_code == 200

        start_call = mock_logger.info.call_args_list[0]
        assert "param1=value1" in start_call[1]["extra"]["query_params"]
        assert "param2=value2" in start_call[1]["extra"]["query_params"]

    @patch("middleware.logging.logger")
    def test_logs_failed_request(self, mock_logger: MagicMock, client: TestClient) -> None:
        """Test that failed requests are logged with error details."""
        with pytest.raises(ValueError):
            client.get("/error")

        # Should have start log and error log
        assert mock_logger.info.call_count == 1  # Only start
        assert mock_logger.error.call_count == 1  # Error

        error_call = mock_logger.error.call_args_list[0]
        assert "Request failed" in error_call[0][0]
        assert "error" in error_call[1]["extra"]
        assert "Test error" in error_call[1]["extra"]["error"]

    @patch("middleware.logging.logger")
    def test_request_id_consistency(self, mock_logger: MagicMock, client: TestClient) -> None:
        """Test that request ID is consistent across logs."""
        response = client.get("/test")

        start_call = mock_logger.info.call_args_list[0]
        completion_call = mock_logger.info.call_args_list[1]

        start_id = start_call[1]["extra"]["request_id"]
        completion_id = completion_call[1]["extra"]["request_id"]
        header_id = response.headers["X-Request-ID"]

        assert start_id == completion_id == header_id

    @patch("middleware.logging.logger")
    def test_logs_client_information(self, mock_logger: MagicMock, client: TestClient) -> None:
        """Test that client information is logged."""
        response = client.get("/test")

        assert response.status_code == 200

        start_call = mock_logger.info.call_args_list[0]
        assert "client_host" in start_call[1]["extra"]
        assert "user_agent" in start_call[1]["extra"]

    def test_process_time_header(self, client: TestClient) -> None:
        """Test that process time is added to response headers."""
        response = client.get("/test")

        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
