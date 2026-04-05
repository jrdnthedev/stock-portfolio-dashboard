from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Stock Portfolio API"
    assert response.json()["status"] == "running"


@patch("main.get_health_status")
def test_health_check(mock_health_status: MagicMock) -> None:
    mock_health_status.return_value = {
        "status": "healthy",
        "timestamp": "2026-04-05T12:00:00",
        "services": {
            "postgres": {"status": "healthy", "message": "PostgreSQL connection successful"},
            "redis": {"status": "healthy", "message": "Redis connection successful"},
            "kafka": {"status": "healthy", "message": "Kafka broker connected, 3 topics available"},
        },
    }
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["postgres"]["status"] == "healthy"
    assert data["data"]["redis"]["status"] == "healthy"
    assert data["data"]["kafka"]["status"] == "healthy"


@patch("main.get_health_status")
def test_health_check_unhealthy(mock_health_status: MagicMock) -> None:
    mock_health_status.return_value = {
        "status": "unhealthy",
        "timestamp": "2026-04-05T12:00:00",
        "services": {
            "postgres": {"status": "healthy", "message": "PostgreSQL connection successful"},
            "redis": {"status": "unhealthy", "message": "Redis connection failed"},
            "kafka": {"status": "healthy", "message": "Kafka broker connected, 3 topics available"},
        },
    }
    response = client.get("/api/health")
    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert data["metadata"]["services"]["redis"]["status"] == "unhealthy"


def test_request_logging_headers() -> None:
    """Test that logging middleware adds tracking headers."""
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers
    # Verify request ID is a valid UUID format
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 36  # UUID format length
    # Verify process time is a number
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0
