"""Tests for custom exceptions module."""

from uuid import uuid4

import pytest

from backend.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CacheConnectionError,
    CacheError,
    CacheOperationError,
    ConfigurationError,
    ConflictError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseOperationError,
    DuplicateHoldingError,
    DuplicatePortfolioError,
    ExternalServiceError,
    HoldingNotFoundError,
    InfrastructureError,
    InsufficientHoldingQuantityError,
    InvalidHoldingDataError,
    InvalidPortfolioDataError,
    InvalidTickerError,
    KafkaConnectionError,
    MarketDataError,
    MarketDataUnavailableError,
    MessageConsumeError,
    MessagePublishError,
    MessagingError,
    NotFoundError,
    PortfolioNotFoundError,
    PriceDataNotFoundError,
    StockPortfolioError,
    TickerNotFoundError,
    ValidationError,
    WebSocketConnectionError,
    WebSocketError,
    WebSocketMessageError,
)

# ============================================================================
# Base Exception Tests
# ============================================================================


class TestStockPortfolioError:
    """Tests for the base StockPortfolioError exception."""

    def test_basic_error(self):
        """Test basic error creation with message only."""
        error = StockPortfolioError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    def test_error_with_details(self):
        """Test error with additional details."""
        details = {"key": "value", "count": 42}
        error = StockPortfolioError("Test error", details=details)
        assert error.message == "Test error"
        assert error.details == details

    def test_error_inheritance(self):
        """Test that StockPortfolioError inherits from Exception."""
        error = StockPortfolioError("Test")
        assert isinstance(error, Exception)


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error(self):
        """Test validation error creation."""
        error = ValidationError("Invalid data")
        assert str(error) == "Invalid data"
        assert isinstance(error, StockPortfolioError)


class TestNotFoundError:
    """Tests for NotFoundError exception."""

    def test_not_found_error(self):
        """Test not found error creation."""
        error = NotFoundError("Resource not found")
        assert str(error) == "Resource not found"
        assert isinstance(error, StockPortfolioError)


class TestConflictError:
    """Tests for ConflictError exception."""

    def test_conflict_error(self):
        """Test conflict error creation."""
        error = ConflictError("Resource conflict")
        assert str(error) == "Resource conflict"
        assert isinstance(error, StockPortfolioError)


# ============================================================================
# Portfolio Domain Exception Tests
# ============================================================================


class TestPortfolioNotFoundError:
    """Tests for PortfolioNotFoundError exception."""

    def test_with_uuid(self):
        """Test error with UUID portfolio ID."""
        portfolio_id = uuid4()
        error = PortfolioNotFoundError(portfolio_id)
        assert f"Portfolio {portfolio_id} not found" in str(error)
        assert error.details["portfolio_id"] == str(portfolio_id)
        assert isinstance(error, NotFoundError)

    def test_with_string(self):
        """Test error with string portfolio ID."""
        portfolio_id = "test-portfolio-123"
        error = PortfolioNotFoundError(portfolio_id)
        assert f"Portfolio {portfolio_id} not found" in str(error)
        assert error.details["portfolio_id"] == portfolio_id


class TestHoldingNotFoundError:
    """Tests for HoldingNotFoundError exception."""

    def test_with_uuid(self):
        """Test error with UUID holding ID."""
        holding_id = uuid4()
        error = HoldingNotFoundError(holding_id)
        assert f"Holding {holding_id} not found" in str(error)
        assert error.details["holding_id"] == str(holding_id)
        assert isinstance(error, NotFoundError)

    def test_with_string(self):
        """Test error with string holding ID."""
        holding_id = "test-holding-456"
        error = HoldingNotFoundError(holding_id)
        assert f"Holding {holding_id} not found" in str(error)
        assert error.details["holding_id"] == holding_id


class TestTickerNotFoundError:
    """Tests for TickerNotFoundError exception."""

    def test_ticker_not_found(self):
        """Test ticker not found error."""
        ticker = "INVALID"
        error = TickerNotFoundError(ticker)
        assert f"Ticker {ticker} not found" in str(error)
        assert error.details["ticker"] == ticker
        assert isinstance(error, NotFoundError)


class TestDuplicatePortfolioError:
    """Tests for DuplicatePortfolioError exception."""

    def test_duplicate_portfolio(self):
        """Test duplicate portfolio error."""
        error = DuplicatePortfolioError("My Portfolio", "user@example.com")
        assert "My Portfolio" in str(error)
        assert "user@example.com" in str(error)
        assert error.details["portfolio_name"] == "My Portfolio"
        assert error.details["owner"] == "user@example.com"
        assert isinstance(error, ConflictError)


class TestDuplicateHoldingError:
    """Tests for DuplicateHoldingError exception."""

    def test_duplicate_holding(self):
        """Test duplicate holding error."""
        portfolio_id = uuid4()
        ticker = "AAPL"
        error = DuplicateHoldingError(portfolio_id, ticker)
        assert ticker in str(error)
        assert str(portfolio_id) in str(error)
        assert error.details["portfolio_id"] == str(portfolio_id)
        assert error.details["ticker"] == ticker
        assert isinstance(error, ConflictError)


class TestInsufficientHoldingQuantityError:
    """Tests for InsufficientHoldingQuantityError exception."""

    def test_insufficient_quantity(self):
        """Test insufficient quantity error."""
        error = InsufficientHoldingQuantityError("AAPL", owned=10.0, requested=15.0)
        assert "AAPL" in str(error)
        assert "10" in str(error)
        assert "15" in str(error)
        assert error.details["ticker"] == "AAPL"
        assert error.details["owned"] == 10.0
        assert error.details["requested"] == 15.0
        assert isinstance(error, ValidationError)


class TestInvalidPortfolioDataError:
    """Tests for InvalidPortfolioDataError exception."""

    def test_invalid_portfolio_data(self):
        """Test invalid portfolio data error."""
        error = InvalidPortfolioDataError("Portfolio name is required")
        assert "Portfolio name is required" in str(error)
        assert isinstance(error, ValidationError)


class TestInvalidHoldingDataError:
    """Tests for InvalidHoldingDataError exception."""

    def test_invalid_holding_data(self):
        """Test invalid holding data error."""
        error = InvalidHoldingDataError("Quantity must be positive")
        assert "Quantity must be positive" in str(error)
        assert isinstance(error, ValidationError)


# ============================================================================
# Market Data Exception Tests
# ============================================================================


class TestMarketDataUnavailableError:
    """Tests for MarketDataUnavailableError exception."""

    def test_without_reason(self):
        """Test market data unavailable without reason."""
        error = MarketDataUnavailableError("AAPL")
        assert "AAPL" in str(error)
        assert "unavailable" in str(error)
        assert error.details["ticker"] == "AAPL"
        assert error.details["reason"] is None
        assert isinstance(error, MarketDataError)

    def test_with_reason(self):
        """Test market data unavailable with reason."""
        error = MarketDataUnavailableError("AAPL", reason="API rate limit exceeded")
        assert "AAPL" in str(error)
        assert "API rate limit exceeded" in str(error)
        assert error.details["ticker"] == "AAPL"
        assert error.details["reason"] == "API rate limit exceeded"


class TestInvalidTickerError:
    """Tests for InvalidTickerError exception."""

    def test_invalid_ticker(self):
        """Test invalid ticker error."""
        error = InvalidTickerError("INVALID")
        assert "INVALID" in str(error)
        assert error.details["ticker"] == "INVALID"
        assert isinstance(error, ValidationError)


class TestPriceDataNotFoundError:
    """Tests for PriceDataNotFoundError exception."""

    def test_without_date(self):
        """Test price data not found without date."""
        error = PriceDataNotFoundError("AAPL")
        assert "AAPL" in str(error)
        assert error.details["ticker"] == "AAPL"
        assert error.details["date"] is None
        assert isinstance(error, NotFoundError)

    def test_with_date(self):
        """Test price data not found with date."""
        error = PriceDataNotFoundError("AAPL", date="2024-01-15")
        assert "AAPL" in str(error)
        assert "2024-01-15" in str(error)
        assert error.details["ticker"] == "AAPL"
        assert error.details["date"] == "2024-01-15"


# ============================================================================
# Infrastructure Exception Tests
# ============================================================================


class TestDatabaseConnectionError:
    """Tests for DatabaseConnectionError exception."""

    def test_without_reason(self):
        """Test database connection error without reason."""
        error = DatabaseConnectionError()
        assert "Failed to connect to database" in str(error)
        assert error.details["reason"] is None
        assert isinstance(error, DatabaseError)

    def test_with_reason(self):
        """Test database connection error with reason."""
        error = DatabaseConnectionError(reason="Connection timeout")
        assert "Connection timeout" in str(error)
        assert error.details["reason"] == "Connection timeout"


class TestDatabaseOperationError:
    """Tests for DatabaseOperationError exception."""

    def test_without_reason(self):
        """Test database operation error without reason."""
        error = DatabaseOperationError("INSERT")
        assert "INSERT" in str(error)
        assert error.details["operation"] == "INSERT"
        assert error.details["reason"] is None
        assert isinstance(error, DatabaseError)

    def test_with_reason(self):
        """Test database operation error with reason."""
        error = DatabaseOperationError("UPDATE", reason="Constraint violation")
        assert "UPDATE" in str(error)
        assert "Constraint violation" in str(error)
        assert error.details["operation"] == "UPDATE"
        assert error.details["reason"] == "Constraint violation"


class TestCacheConnectionError:
    """Tests for CacheConnectionError exception."""

    def test_without_reason(self):
        """Test cache connection error without reason."""
        error = CacheConnectionError()
        assert "Failed to connect to cache" in str(error)
        assert error.details["reason"] is None
        assert isinstance(error, CacheError)

    def test_with_reason(self):
        """Test cache connection error with reason."""
        error = CacheConnectionError(reason="Redis unavailable")
        assert "Redis unavailable" in str(error)
        assert error.details["reason"] == "Redis unavailable"


class TestCacheOperationError:
    """Tests for CacheOperationError exception."""

    def test_operation_only(self):
        """Test cache operation error with operation only."""
        error = CacheOperationError("GET")
        assert "GET" in str(error)
        assert error.details["operation"] == "GET"
        assert error.details["key"] is None
        assert error.details["reason"] is None
        assert isinstance(error, CacheError)

    def test_with_key(self):
        """Test cache operation error with key."""
        error = CacheOperationError("SET", key="portfolio:123")
        assert "SET" in str(error)
        assert "portfolio:123" in str(error)
        assert error.details["operation"] == "SET"
        assert error.details["key"] == "portfolio:123"

    def test_with_all_details(self):
        """Test cache operation error with all details."""
        error = CacheOperationError("DELETE", key="portfolio:456", reason="Key not found")
        assert "DELETE" in str(error)
        assert "portfolio:456" in str(error)
        assert "Key not found" in str(error)
        assert error.details["operation"] == "DELETE"
        assert error.details["key"] == "portfolio:456"
        assert error.details["reason"] == "Key not found"


class TestMessagePublishError:
    """Tests for MessagePublishError exception."""

    def test_without_reason(self):
        """Test message publish error without reason."""
        error = MessagePublishError("price-updates")
        assert "price-updates" in str(error)
        assert error.details["topic"] == "price-updates"
        assert error.details["reason"] is None
        assert isinstance(error, MessagingError)

    def test_with_reason(self):
        """Test message publish error with reason."""
        error = MessagePublishError("price-updates", reason="Broker unavailable")
        assert "price-updates" in str(error)
        assert "Broker unavailable" in str(error)
        assert error.details["topic"] == "price-updates"
        assert error.details["reason"] == "Broker unavailable"


class TestMessageConsumeError:
    """Tests for MessageConsumeError exception."""

    def test_without_reason(self):
        """Test message consume error without reason."""
        error = MessageConsumeError("price-updates")
        assert "price-updates" in str(error)
        assert error.details["topic"] == "price-updates"
        assert error.details["reason"] is None
        assert isinstance(error, MessagingError)

    def test_with_reason(self):
        """Test message consume error with reason."""
        error = MessageConsumeError("price-updates", reason="Timeout")
        assert "price-updates" in str(error)
        assert "Timeout" in str(error)
        assert error.details["topic"] == "price-updates"
        assert error.details["reason"] == "Timeout"


class TestKafkaConnectionError:
    """Tests for KafkaConnectionError exception."""

    def test_without_reason(self):
        """Test Kafka connection error without reason."""
        error = KafkaConnectionError()
        assert "Failed to connect to Kafka" in str(error)
        assert error.details["reason"] is None
        assert isinstance(error, MessagingError)

    def test_with_reason(self):
        """Test Kafka connection error with reason."""
        error = KafkaConnectionError(reason="No brokers available")
        assert "No brokers available" in str(error)
        assert error.details["reason"] == "No brokers available"


# ============================================================================
# Authentication & Authorization Exception Tests
# ============================================================================


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_without_reason(self):
        """Test authentication error without reason."""
        error = AuthenticationError()
        assert "Authentication failed" in str(error)
        assert error.details["reason"] is None
        assert isinstance(error, StockPortfolioError)

    def test_with_reason(self):
        """Test authentication error with reason."""
        error = AuthenticationError(reason="Invalid credentials")
        assert "Invalid credentials" in str(error)
        assert error.details["reason"] == "Invalid credentials"


class TestAuthorizationError:
    """Tests for AuthorizationError exception."""

    def test_without_details(self):
        """Test authorization error without resource or action."""
        error = AuthorizationError()
        assert "Access denied" in str(error)
        assert error.details["resource"] is None
        assert error.details["action"] is None
        assert isinstance(error, StockPortfolioError)

    def test_with_resource_only(self):
        """Test authorization error with resource only."""
        error = AuthorizationError(resource="portfolio")
        assert "portfolio" in str(error)
        assert error.details["resource"] == "portfolio"

    def test_with_resource_and_action(self):
        """Test authorization error with resource and action."""
        error = AuthorizationError(resource="portfolio", action="delete")
        assert "delete" in str(error)
        assert "portfolio" in str(error)
        assert error.details["resource"] == "portfolio"
        assert error.details["action"] == "delete"


# ============================================================================
# WebSocket Exception Tests
# ============================================================================


class TestWebSocketConnectionError:
    """Tests for WebSocketConnectionError exception."""

    def test_without_details(self):
        """Test WebSocket connection error without details."""
        error = WebSocketConnectionError()
        assert "WebSocket connection failed" in str(error)
        assert error.details["client_id"] is None
        assert error.details["reason"] is None
        assert isinstance(error, WebSocketError)

    def test_with_client_id(self):
        """Test WebSocket connection error with client ID."""
        error = WebSocketConnectionError(client_id="client-123")
        assert "client-123" in str(error)
        assert error.details["client_id"] == "client-123"

    def test_with_all_details(self):
        """Test WebSocket connection error with all details."""
        error = WebSocketConnectionError(client_id="client-123", reason="Timeout")
        assert "client-123" in str(error)
        assert "Timeout" in str(error)
        assert error.details["client_id"] == "client-123"
        assert error.details["reason"] == "Timeout"


class TestWebSocketMessageError:
    """Tests for WebSocketMessageError exception."""

    def test_without_details(self):
        """Test WebSocket message error without details."""
        error = WebSocketMessageError()
        assert "WebSocket message error" in str(error)
        assert error.details["client_id"] is None
        assert error.details["reason"] is None
        assert isinstance(error, WebSocketError)

    def test_with_client_id(self):
        """Test WebSocket message error with client ID."""
        error = WebSocketMessageError(client_id="client-123")
        assert "client-123" in str(error)
        assert error.details["client_id"] == "client-123"

    def test_with_all_details(self):
        """Test WebSocket message error with all details."""
        error = WebSocketMessageError(client_id="client-123", reason="Invalid message format")
        assert "client-123" in str(error)
        assert "Invalid message format" in str(error)
        assert error.details["client_id"] == "client-123"
        assert error.details["reason"] == "Invalid message format"


# ============================================================================
# Configuration Exception Tests
# ============================================================================


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_without_reason(self):
        """Test configuration error without reason."""
        error = ConfigurationError("DATABASE_URL")
        assert "DATABASE_URL" in str(error)
        assert error.details["config_key"] == "DATABASE_URL"
        assert error.details["reason"] is None
        assert isinstance(error, StockPortfolioError)

    def test_with_reason(self):
        """Test configuration error with reason."""
        error = ConfigurationError("API_KEY", reason="Missing required value")
        assert "API_KEY" in str(error)
        assert "Missing required value" in str(error)
        assert error.details["config_key"] == "API_KEY"
        assert error.details["reason"] == "Missing required value"


# ============================================================================
# Exception Hierarchy Tests
# ============================================================================


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_base_exceptions(self):
        """Test that all base exceptions inherit from StockPortfolioError."""
        assert issubclass(ValidationError, StockPortfolioError)
        assert issubclass(NotFoundError, StockPortfolioError)
        assert issubclass(ConflictError, StockPortfolioError)
        assert issubclass(ExternalServiceError, StockPortfolioError)
        assert issubclass(InfrastructureError, StockPortfolioError)

    def test_portfolio_exceptions(self):
        """Test portfolio exception hierarchy."""
        assert issubclass(PortfolioNotFoundError, NotFoundError)
        assert issubclass(HoldingNotFoundError, NotFoundError)
        assert issubclass(TickerNotFoundError, NotFoundError)
        assert issubclass(DuplicatePortfolioError, ConflictError)
        assert issubclass(DuplicateHoldingError, ConflictError)
        assert issubclass(InsufficientHoldingQuantityError, ValidationError)
        assert issubclass(InvalidPortfolioDataError, ValidationError)
        assert issubclass(InvalidHoldingDataError, ValidationError)

    def test_market_data_exceptions(self):
        """Test market data exception hierarchy."""
        assert issubclass(MarketDataError, ExternalServiceError)
        assert issubclass(MarketDataUnavailableError, MarketDataError)
        assert issubclass(PriceDataNotFoundError, NotFoundError)
        assert issubclass(InvalidTickerError, ValidationError)

    def test_infrastructure_exceptions(self):
        """Test infrastructure exception hierarchy."""
        assert issubclass(DatabaseError, InfrastructureError)
        assert issubclass(DatabaseConnectionError, DatabaseError)
        assert issubclass(DatabaseOperationError, DatabaseError)
        assert issubclass(CacheError, InfrastructureError)
        assert issubclass(CacheConnectionError, CacheError)
        assert issubclass(CacheOperationError, CacheError)
        assert issubclass(MessagingError, InfrastructureError)
        assert issubclass(MessagePublishError, MessagingError)
        assert issubclass(MessageConsumeError, MessagingError)
        assert issubclass(KafkaConnectionError, MessagingError)

    def test_websocket_exceptions(self):
        """Test WebSocket exception hierarchy."""
        assert issubclass(WebSocketError, StockPortfolioError)
        assert issubclass(WebSocketConnectionError, WebSocketError)
        assert issubclass(WebSocketMessageError, WebSocketError)

    def test_auth_exceptions(self):
        """Test authentication/authorization exception hierarchy."""
        assert issubclass(AuthenticationError, StockPortfolioError)
        assert issubclass(AuthorizationError, StockPortfolioError)

    def test_config_exceptions(self):
        """Test configuration exception hierarchy."""
        assert issubclass(ConfigurationError, StockPortfolioError)


# ============================================================================
# Integration Tests
# ============================================================================


class TestExceptionIntegration:
    """Integration tests for exception usage patterns."""

    def test_catch_by_base_type(self):
        """Test catching exceptions by base type."""
        with pytest.raises(NotFoundError):
            raise PortfolioNotFoundError(uuid4())

        with pytest.raises(StockPortfolioError):
            raise HoldingNotFoundError(uuid4())

    def test_catch_specific_exception(self):
        """Test catching specific exception types."""
        portfolio_id = uuid4()
        with pytest.raises(PortfolioNotFoundError) as exc_info:
            raise PortfolioNotFoundError(portfolio_id)

        assert str(portfolio_id) in str(exc_info.value)
        assert exc_info.value.details["portfolio_id"] == str(portfolio_id)

    def test_exception_details_accessible(self):
        """Test that exception details are accessible after catching."""
        try:
            raise InsufficientHoldingQuantityError("AAPL", owned=10.0, requested=15.0)
        except InsufficientHoldingQuantityError as e:
            assert e.details["ticker"] == "AAPL"
            assert e.details["owned"] == 10.0
            assert e.details["requested"] == 15.0

    def test_multiple_exception_types(self):
        """Test handling multiple exception types."""

        def risky_operation(error_type: str):
            if error_type == "not_found":
                raise PortfolioNotFoundError(uuid4())
            elif error_type == "conflict":
                raise DuplicatePortfolioError("Test", "user@example.com")
            elif error_type == "validation":
                raise InvalidPortfolioDataError("Invalid data")

        with pytest.raises(NotFoundError):
            risky_operation("not_found")

        with pytest.raises(ConflictError):
            risky_operation("conflict")

        with pytest.raises(ValidationError):
            risky_operation("validation")
