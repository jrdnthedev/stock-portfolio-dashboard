"""Unit tests for portfolio routes."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestGetPortfolio:
    """Test get portfolio endpoint."""

    def test_get_portfolio_success(self) -> None:
        """Test retrieving a portfolio."""
        response = client.get("/v1/portfolio/1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Portfolio 1 retrieved successfully" in data["message"]
        assert data["data"]["id"] == 1
        assert data["data"]["name"] == "Growth Portfolio"
        assert "total_value" in data["data"]
        assert "total_cost" in data["data"]
        assert "total_gain" in data["data"]

    def test_get_portfolio_not_found(self) -> None:
        """Test retrieving non-existent portfolio."""
        response = client.get("/v1/portfolio/999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Portfolio not found" in data["message"]


class TestGetHoldings:
    """Test get holdings endpoint."""

    def test_get_holdings_success(self) -> None:
        """Test retrieving portfolio holdings."""
        response = client.get("/v1/portfolio/1/holdings")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Holdings for portfolio 1" in data["message"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        assert data["metadata"]["portfolio_id"] == 1
        assert data["metadata"]["count"] == len(data["data"])
        assert "total_value" in data["metadata"]
        assert "total_cost" in data["metadata"]

    def test_get_holdings_portfolio_not_found(self) -> None:
        """Test retrieving holdings for non-existent portfolio."""
        response = client.get("/v1/portfolio/999/holdings")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestGetPerformance:
    """Test get performance endpoint."""

    def test_get_performance_success(self) -> None:
        """Test retrieving portfolio performance."""
        response = client.get("/v1/portfolio/1/performance")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Performance for portfolio 1" in data["message"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        assert data["metadata"]["portfolio_id"] == 1

    def test_get_performance_with_date_range(self) -> None:
        """Test retrieving performance with date range."""
        response = client.get("/v1/portfolio/1/performance?from=2026-04-01&to=2026-04-03")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["from"] == "2026-04-01"
        assert data["metadata"]["to"] == "2026-04-03"
        # Verify all dates are within range
        for metric in data["data"]:
            assert "2026-04-01" <= metric["date"] <= "2026-04-03"

    def test_get_performance_portfolio_not_found(self) -> None:
        """Test retrieving performance for non-existent portfolio."""
        response = client.get("/v1/portfolio/999/performance")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestGetAllocation:
    """Test get allocation endpoint."""

    def test_get_allocation_success(self) -> None:
        """Test retrieving portfolio allocation."""
        response = client.get("/v1/portfolio/1/allocation")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Allocation for portfolio 1" in data["message"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        assert data["metadata"]["portfolio_id"] == 1
        assert "total_value" in data["metadata"]
        # Verify allocation items have required fields
        for item in data["data"]:
            assert "ticker" in item
            assert "value" in item
            assert "percentage" in item
            assert "sector" in item

    def test_get_allocation_portfolio_not_found(self) -> None:
        """Test retrieving allocation for non-existent portfolio."""
        response = client.get("/v1/portfolio/999/allocation")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestCreateHolding:
    """Test create holding endpoint."""

    def test_create_holding_success(self) -> None:
        """Test creating a new holding."""
        new_holding = {
            "ticker": "TSLA",
            "quantity": 50.0,
            "average_cost": 250.00,
            "purchased_at": "2026-04-05T10:00:00Z",
        }
        response = client.post("/v1/portfolio/1/holdings", json=new_holding)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "Holding created successfully" in data["message"]
        assert data["data"]["ticker"] == "TSLA"
        assert data["data"]["quantity"] == 50.0
        assert data["data"]["average_cost"] == 250.00
        assert "id" in data["data"]
        assert "total_cost" in data["data"]
        assert "total_value" in data["data"]

    def test_create_holding_portfolio_not_found(self) -> None:
        """Test creating holding in non-existent portfolio."""
        new_holding = {"ticker": "TSLA", "quantity": 50.0, "average_cost": 250.00}
        response = client.post("/v1/portfolio/999/holdings", json=new_holding)
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_create_holding_validation_error(self) -> None:
        """Test creating holding with invalid data."""
        invalid_holding = {"ticker": "TSLA", "quantity": -10.0, "average_cost": 250.00}
        response = client.post("/v1/portfolio/1/holdings", json=invalid_holding)
        assert response.status_code == 422  # Validation error


class TestUpdateHolding:
    """Test update holding endpoint."""

    def test_update_holding_success(self) -> None:
        """Test updating an existing holding."""
        update_data = {"quantity": 150.0, "average_cost": 160.00}
        response = client.put("/v1/portfolio/1/holdings/101", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Holding 101 updated successfully" in data["message"]
        assert data["data"]["id"] == 101
        assert data["data"]["quantity"] == 150.0
        assert data["data"]["average_cost"] == 160.00

    def test_update_holding_partial(self) -> None:
        """Test updating holding with partial data."""
        update_data = {"quantity": 120.0}
        response = client.put("/v1/portfolio/1/holdings/102", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["quantity"] == 120.0

    def test_update_holding_not_found(self) -> None:
        """Test updating non-existent holding."""
        update_data = {"quantity": 150.0}
        response = client.put("/v1/portfolio/1/holdings/999", json=update_data)
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_update_holding_portfolio_not_found(self) -> None:
        """Test updating holding in non-existent portfolio."""
        update_data = {"quantity": 150.0}
        response = client.put("/v1/portfolio/999/holdings/101", json=update_data)
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestDeleteHolding:
    """Test delete holding endpoint."""

    def test_delete_holding_success(self) -> None:
        """Test deleting a holding."""
        # Use holding 103 for regular delete test
        response = client.delete("/v1/portfolio/1/holdings/103")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Holding 103 deleted successfully" in data["message"]
        assert data["data"]["id"] == 103
        assert data["data"]["deleted"] is True

    def test_delete_holding_not_found(self) -> None:
        """Test deleting non-existent holding."""
        response = client.delete("/v1/portfolio/1/holdings/999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_delete_holding_portfolio_not_found(self) -> None:
        """Test deleting holding from non-existent portfolio."""
        response = client.delete("/v1/portfolio/999/holdings/101")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
