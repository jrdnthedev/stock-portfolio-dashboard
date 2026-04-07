"""Unit tests for cache invalidation in portfolio routes."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestCacheInvalidation:
    """Test cache invalidation on holdings write operations."""

    @patch("backend.routes_portfolio.get_cache_service")
    def test_create_holding_invalidates_cache(self, mock_get_cache: MagicMock) -> None:
        """Test that creating a holding invalidates relevant caches."""
        # Setup mock cache service
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        # Create a new holding
        new_holding = {
            "ticker": "NVDA",
            "quantity": 25.0,
            "average_cost": 450.00,
        }
        response = client.post("/v1/portfolio/1/holdings", json=new_holding)

        # Verify successful creation
        assert response.status_code == 201

        # Verify cache invalidation was called for all relevant keys
        assert mock_cache.delete.call_count == 4
        mock_cache.delete.assert_any_call("portfolio:1:holdings")
        mock_cache.delete.assert_any_call("portfolio:1:performance")
        mock_cache.delete.assert_any_call("portfolio:1:allocation")
        mock_cache.delete.assert_any_call("portfolio:1")

    @patch("backend.routes_portfolio.get_cache_service")
    def test_update_holding_invalidates_cache(self, mock_get_cache: MagicMock) -> None:
        """Test that updating a holding invalidates relevant caches."""
        # Setup mock cache service
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        # Update an existing holding in portfolio 2
        update_data = {"quantity": 200.0}
        response = client.put("/v1/portfolio/2/holdings/201", json=update_data)

        # Verify successful update
        assert response.status_code == 200

        # Verify cache invalidation was called for all relevant keys
        assert mock_cache.delete.call_count == 4
        mock_cache.delete.assert_any_call("portfolio:2:holdings")
        mock_cache.delete.assert_any_call("portfolio:2:performance")
        mock_cache.delete.assert_any_call("portfolio:2:allocation")
        mock_cache.delete.assert_any_call("portfolio:2")

    @patch("backend.routes_portfolio.get_cache_service")
    def test_delete_holding_invalidates_cache(self, mock_get_cache: MagicMock) -> None:
        """Test that deleting a holding invalidates relevant caches."""
        # Setup mock cache service
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        # Delete holding from portfolio 2
        response = client.delete("/v1/portfolio/2/holdings/202")

        # Verify successful deletion
        assert response.status_code == 200

        # Verify cache invalidation was called for all relevant keys
        assert mock_cache.delete.call_count == 4
        mock_cache.delete.assert_any_call("portfolio:2:holdings")
        mock_cache.delete.assert_any_call("portfolio:2:performance")
        mock_cache.delete.assert_any_call("portfolio:2:allocation")
        mock_cache.delete.assert_any_call("portfolio:2")

    @patch("backend.routes_portfolio.get_cache_service")
    def test_create_holding_wrong_portfolio_no_cache_invalidation(
        self, mock_get_cache: MagicMock
    ) -> None:
        """Test that failed operations don't invalidate cache."""
        # Setup mock cache service
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        # Try to create holding in non-existent portfolio
        new_holding = {
            "ticker": "NVDA",
            "quantity": 25.0,
            "average_cost": 450.00,
        }
        response = client.post("/v1/portfolio/999/holdings", json=new_holding)

        # Verify failed creation
        assert response.status_code == 404

        # Verify cache invalidation was NOT called
        mock_cache.delete.assert_not_called()

    @patch("backend.routes_portfolio.get_cache_service")
    def test_update_nonexistent_holding_no_cache_invalidation(
        self, mock_get_cache: MagicMock
    ) -> None:
        """Test that updating non-existent holding doesn't invalidate cache."""
        # Setup mock cache service
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        # Try to update non-existent holding
        update_data = {"quantity": 200.0}
        response = client.put("/v1/portfolio/1/holdings/9999", json=update_data)

        # Verify failed update
        assert response.status_code == 404

        # Verify cache invalidation was NOT called
        mock_cache.delete.assert_not_called()

    @patch("backend.routes_portfolio.get_cache_service")
    def test_multiple_holdings_operations_invalidate_correctly(
        self, mock_get_cache: MagicMock
    ) -> None:
        """Test that multiple operations invalidate cache correctly."""
        # Setup mock cache service
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        # Create a holding
        new_holding = {"ticker": "AMD", "quantity": 100.0, "average_cost": 120.00}
        client.post("/v1/portfolio/2/holdings", json=new_holding)

        # Update a holding
        client.put("/v1/portfolio/2/holdings/201", json={"quantity": 200.0})

        # Total calls should be 8 (4 per operation)
        assert mock_cache.delete.call_count == 8

        # Verify correct portfolio ID in cache keys
        calls = [str(call) for call in mock_cache.delete.call_args_list]
        assert any("portfolio:2:holdings" in str(call) for call in calls)
        assert any("portfolio:2:performance" in str(call) for call in calls)
        assert any("portfolio:2:allocation" in str(call) for call in calls)
        assert any("portfolio:2" in str(call) for call in calls)
