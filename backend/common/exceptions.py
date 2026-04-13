"""Custom exceptions for the Stock Portfolio Backend application.

This module defines domain-specific exceptions that provide clear error handling
and improve code readability throughout the application.
"""

from typing import Any
from uuid import UUID

# ============================================================================
# Base Exceptions
# ============================================================================


class StockPortfolioError(Exception):
    """Base exception for all application-specific errors.

    All custom exceptions should inherit from this class to enable
    centralized error handling and logging.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the exception with a message and optional details.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(StockPortfolioError):
    """Exception raised when data validation fails.

    Used for input validation, business rule violations, and data integrity checks.
    """

    pass


class NotFoundError(StockPortfolioError):
    """Base exception for resource not found errors."""

    pass


class ConflictError(StockPortfolioError):
    """Exception raised when an operation conflicts with existing state.

    Examples: duplicate resources, concurrent modifications, state violations.
    """

    pass


class ExternalServiceError(StockPortfolioError):
    """Exception raised when an external service fails.

    Used for third-party API errors, network failures, and service unavailability.
    """

    pass


class InfrastructureError(StockPortfolioError):
    """Exception raised for infrastructure-level failures.

    Examples: database errors, cache failures, messaging system errors.
    """

    pass


# ============================================================================
# Portfolio Domain Exceptions
# ============================================================================


class PortfolioNotFoundError(NotFoundError):
    """Exception raised when a portfolio cannot be found."""

    def __init__(self, portfolio_id: UUID | str) -> None:
        """Initialize with portfolio identifier.

        Args:
            portfolio_id: The ID of the portfolio that was not found
        """
        super().__init__(
            message=f"Portfolio {portfolio_id} not found",
            details={"portfolio_id": str(portfolio_id)},
        )


class HoldingNotFoundError(NotFoundError):
    """Exception raised when a holding cannot be found."""

    def __init__(self, holding_id: UUID | str) -> None:
        """Initialize with holding identifier.

        Args:
            holding_id: The ID of the holding that was not found
        """
        super().__init__(
            message=f"Holding {holding_id} not found",
            details={"holding_id": str(holding_id)},
        )


class TickerNotFoundError(NotFoundError):
    """Exception raised when a ticker cannot be found."""

    def __init__(self, ticker: str) -> None:
        """Initialize with ticker symbol.

        Args:
            ticker: The ticker symbol that was not found
        """
        super().__init__(
            message=f"Ticker {ticker} not found",
            details={"ticker": ticker},
        )


class DuplicatePortfolioError(ConflictError):
    """Exception raised when attempting to create a duplicate portfolio."""

    def __init__(self, portfolio_name: str, owner: str) -> None:
        """Initialize with portfolio details.

        Args:
            portfolio_name: Name of the duplicate portfolio
            owner: Owner of the portfolio
        """
        super().__init__(
            message=f"Portfolio '{portfolio_name}' already exists for owner '{owner}'",
            details={"portfolio_name": portfolio_name, "owner": owner},
        )


class DuplicateHoldingError(ConflictError):
    """Exception raised when attempting to create a duplicate holding."""

    def __init__(self, portfolio_id: UUID | str, ticker: str) -> None:
        """Initialize with holding details.

        Args:
            portfolio_id: ID of the portfolio
            ticker: Ticker symbol
        """
        super().__init__(
            message=f"Holding for ticker '{ticker}' already exists in portfolio {portfolio_id}",
            details={"portfolio_id": str(portfolio_id), "ticker": ticker},
        )


class InsufficientHoldingQuantityError(ValidationError):
    """Exception raised when attempting to sell more shares than owned."""

    def __init__(self, ticker: str, owned: float, requested: float) -> None:
        """Initialize with quantity details.

        Args:
            ticker: Ticker symbol
            owned: Number of shares owned
            requested: Number of shares requested to sell
        """
        super().__init__(
            message=f"Insufficient shares for {ticker}: owned {owned}, requested {requested}",
            details={"ticker": ticker, "owned": owned, "requested": requested},
        )


class InvalidPortfolioDataError(ValidationError):
    """Exception raised when portfolio data is invalid."""

    pass


class InvalidHoldingDataError(ValidationError):
    """Exception raised when holding data is invalid."""

    pass


# ============================================================================
# Market Data Exceptions
# ============================================================================


class MarketDataError(ExternalServiceError):
    """Base exception for market data-related errors."""

    pass


class MarketDataUnavailableError(MarketDataError):
    """Exception raised when market data cannot be retrieved."""

    def __init__(self, ticker: str, reason: str | None = None) -> None:
        """Initialize with ticker and optional reason.

        Args:
            ticker: Ticker symbol for which data is unavailable
            reason: Optional reason why data is unavailable
        """
        message = f"Market data unavailable for {ticker}"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"ticker": ticker, "reason": reason})


class InvalidTickerError(ValidationError):
    """Exception raised when a ticker symbol is invalid."""

    def __init__(self, ticker: str) -> None:
        """Initialize with invalid ticker.

        Args:
            ticker: The invalid ticker symbol
        """
        super().__init__(
            message=f"Invalid ticker symbol: {ticker}",
            details={"ticker": ticker},
        )


class PriceDataNotFoundError(NotFoundError):
    """Exception raised when price data is not available."""

    def __init__(self, ticker: str, date: str | None = None) -> None:
        """Initialize with ticker and optional date.

        Args:
            ticker: Ticker symbol
            date: Optional date for which price is not found
        """
        message = f"Price data not found for {ticker}"
        if date:
            message += f" on {date}"
        super().__init__(message=message, details={"ticker": ticker, "date": date})


# ============================================================================
# Infrastructure Exceptions
# ============================================================================


class DatabaseError(InfrastructureError):
    """Exception raised for database-related errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Exception raised when database connection fails."""

    def __init__(self, reason: str | None = None) -> None:
        """Initialize with optional reason.

        Args:
            reason: Optional reason for connection failure
        """
        message = "Failed to connect to database"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"reason": reason})


class DatabaseOperationError(DatabaseError):
    """Exception raised when a database operation fails."""

    def __init__(self, operation: str, reason: str | None = None) -> None:
        """Initialize with operation and optional reason.

        Args:
            operation: The database operation that failed
            reason: Optional reason for failure
        """
        message = f"Database operation '{operation}' failed"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"operation": operation, "reason": reason})


class CacheError(InfrastructureError):
    """Base exception for cache-related errors."""

    pass


class CacheConnectionError(CacheError):
    """Exception raised when cache connection fails."""

    def __init__(self, reason: str | None = None) -> None:
        """Initialize with optional reason.

        Args:
            reason: Optional reason for connection failure
        """
        message = "Failed to connect to cache"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"reason": reason})


class CacheOperationError(CacheError):
    """Exception raised when a cache operation fails."""

    def __init__(self, operation: str, key: str | None = None, reason: str | None = None) -> None:
        """Initialize with operation details.

        Args:
            operation: The cache operation that failed
            key: Optional cache key
            reason: Optional reason for failure
        """
        message = f"Cache operation '{operation}' failed"
        if key:
            message += f" for key '{key}'"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message, details={"operation": operation, "key": key, "reason": reason}
        )


class MessagingError(InfrastructureError):
    """Base exception for messaging system errors."""

    pass


class MessagePublishError(MessagingError):
    """Exception raised when publishing a message fails."""

    def __init__(self, topic: str, reason: str | None = None) -> None:
        """Initialize with topic and optional reason.

        Args:
            topic: The topic to which message publication failed
            reason: Optional reason for failure
        """
        message = f"Failed to publish message to topic '{topic}'"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"topic": topic, "reason": reason})


class MessageConsumeError(MessagingError):
    """Exception raised when consuming a message fails."""

    def __init__(self, topic: str, reason: str | None = None) -> None:
        """Initialize with topic and optional reason.

        Args:
            topic: The topic from which message consumption failed
            reason: Optional reason for failure
        """
        message = f"Failed to consume message from topic '{topic}'"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"topic": topic, "reason": reason})


class KafkaConnectionError(MessagingError):
    """Exception raised when Kafka connection fails."""

    def __init__(self, reason: str | None = None) -> None:
        """Initialize with optional reason.

        Args:
            reason: Optional reason for connection failure
        """
        message = "Failed to connect to Kafka"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"reason": reason})


# ============================================================================
# Authentication & Authorization Exceptions
# ============================================================================


class AuthenticationError(StockPortfolioError):
    """Exception raised for authentication failures."""

    def __init__(self, reason: str | None = None) -> None:
        """Initialize with optional reason.

        Args:
            reason: Optional reason for authentication failure
        """
        message = "Authentication failed"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"reason": reason})


class AuthorizationError(StockPortfolioError):
    """Exception raised for authorization failures."""

    def __init__(self, resource: str | None = None, action: str | None = None) -> None:
        """Initialize with optional resource and action.

        Args:
            resource: The resource access was denied to
            action: The action that was denied
        """
        message = "Access denied"
        if action and resource:
            message = f"Not authorized to {action} {resource}"
        elif resource:
            message = f"Not authorized to access {resource}"
        super().__init__(message=message, details={"resource": resource, "action": action})


# ============================================================================
# WebSocket Exceptions
# ============================================================================


class WebSocketError(StockPortfolioError):
    """Base exception for WebSocket-related errors."""

    pass


class WebSocketConnectionError(WebSocketError):
    """Exception raised when WebSocket connection fails."""

    def __init__(self, client_id: str | None = None, reason: str | None = None) -> None:
        """Initialize with optional client ID and reason.

        Args:
            client_id: Optional client identifier
            reason: Optional reason for connection failure
        """
        message = "WebSocket connection failed"
        if client_id:
            message += f" for client {client_id}"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"client_id": client_id, "reason": reason})


class WebSocketMessageError(WebSocketError):
    """Exception raised when sending/receiving WebSocket message fails."""

    def __init__(self, client_id: str | None = None, reason: str | None = None) -> None:
        """Initialize with optional client ID and reason.

        Args:
            client_id: Optional client identifier
            reason: Optional reason for message failure
        """
        message = "WebSocket message error"
        if client_id:
            message += f" for client {client_id}"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"client_id": client_id, "reason": reason})


# ============================================================================
# Configuration Exceptions
# ============================================================================


class ConfigurationError(StockPortfolioError):
    """Exception raised for configuration-related errors."""

    def __init__(self, config_key: str, reason: str | None = None) -> None:
        """Initialize with configuration key and optional reason.

        Args:
            config_key: The configuration key that caused the error
            reason: Optional reason for the error
        """
        message = f"Configuration error for '{config_key}'"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"config_key": config_key, "reason": reason})
