# Custom Exceptions - Usage Guide

This guide demonstrates how to use the custom exceptions in the Stock Portfolio Backend application. # noqa E999

## Overview

The application uses domain-specific exceptions that inherit from a base `StockPortfolioError` class. This provides:
- Clear error messages with context
- Structured error details for logging/debugging
- Type-safe exception handling
- Consistent error handling patterns across the codebase

## Exception Hierarchy

```
StockPortfolioError (base)
├── ValidationError
│   ├── InvalidPortfolioDataError
│   ├── InvalidHoldingDataError
│   ├── InvalidTickerError
│   └── InsufficientHoldingQuantityError
│
├── NotFoundError
│   ├── PortfolioNotFoundError
│   ├── HoldingNotFoundError
│   ├── TickerNotFoundError
│   └── PriceDataNotFoundError
│
├── ConflictError
│   ├── DuplicatePortfolioError
│   └── DuplicateHoldingError
│
├── ExternalServiceError
│   └── MarketDataError
│       └── MarketDataUnavailableError
│
├── InfrastructureError
│   ├── DatabaseError
│   │   ├── DatabaseConnectionError
│   │   └── DatabaseOperationError
│   ├── CacheError
│   │   ├── CacheConnectionError
│   │   └── CacheOperationError
│   └── MessagingError
│       ├── MessagePublishError
│       ├── MessageConsumeError
│       └── KafkaConnectionError
│
├── AuthenticationError
├── AuthorizationError
├── WebSocketError
│   ├── WebSocketConnectionError
│   └── WebSocketMessageError
└── ConfigurationError
```

## Basic Usage

### Raising Exceptions

```python
from backend.common.exceptions import (
    PortfolioNotFoundError,
    InvalidTickerError,
    InsufficientHoldingQuantityError,
)

# Simple not found error
def get_portfolio(portfolio_id: UUID):
    portfolio = db.query(Portfolio).filter_by(id=portfolio_id).first()
    if not portfolio:
        raise PortfolioNotFoundError(portfolio_id)
    return portfolio

# Validation error
def validate_ticker(ticker: str):
    if not ticker or len(ticker) > 10:
        raise InvalidTickerError(ticker)

# Business logic error with details
def sell_shares(ticker: str, owned: float, requested: float):
    if requested > owned:
        raise InsufficientHoldingQuantityError(
            ticker=ticker,
            owned=owned,
            requested=requested
        )
```

### Catching Exceptions

```python
from backend.common.exceptions import (
    PortfolioNotFoundError,
    NotFoundError,
    StockPortfolioError,
)

# Catch specific exception
try:
    portfolio = get_portfolio(portfolio_id)
except PortfolioNotFoundError as e:
    print(f"Portfolio not found: {e.message}")
    print(f"Details: {e.details}")
    # Details: {"portfolio_id": "123e4567-..."}

# Catch by category
try:
    portfolio = get_portfolio(portfolio_id)
    holding = get_holding(holding_id)
except NotFoundError as e:
    # Handles both PortfolioNotFoundError and HoldingNotFoundError
    return JSONResponse(
        content={"error": e.message, "details": e.details},
        status_code=404
    )

# Catch all application errors
try:
    # ... application code
except StockPortfolioError as e:
    logger.error(f"Application error: {e.message}", extra=e.details)
    # Re-raise or handle
```

## FastAPI Integration

### Route Handler Example

```python
from fastapi import APIRouter, HTTPException, status
from backend.common.exceptions import (
    PortfolioNotFoundError,
    DuplicatePortfolioError,
    ValidationError,
    NotFoundError,
    ConflictError,
)

router = APIRouter()

@router.get("/portfolio/{id}")
async def get_portfolio_endpoint(id: UUID):
    try:
        portfolio = portfolio_service.get_portfolio(id)
        return {"data": portfolio}
    except PortfolioNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message, "details": e.details}
        )

@router.post("/portfolio")
async def create_portfolio_endpoint(data: PortfolioCreate):
    try:
        portfolio = portfolio_service.create_portfolio(data)
        return {"data": portfolio}
    except DuplicatePortfolioError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": e.message, "details": e.details}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "details": e.details}
        )
```

### Global Exception Handler (Recommended)

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from backend.common.exceptions import (
    StockPortfolioError,
    NotFoundError,
    ConflictError,
    ValidationError,
    InfrastructureError,
)

app = FastAPI()

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": exc.message, "details": exc.details}
    )

@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": exc.message, "details": exc.details}
    )

@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.message, "details": exc.details}
    )

@app.exception_handler(InfrastructureError)
async def infrastructure_handler(request: Request, exc: InfrastructureError):
    logger.error(f"Infrastructure error: {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"error": "Service temporarily unavailable"}
    )

@app.exception_handler(StockPortfolioError)
async def generic_handler(request: Request, exc: StockPortfolioError):
    logger.error(f"Unhandled application error: {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )
```

## Domain-Specific Examples

### Portfolio Operations

```python
from backend.common.exceptions import (
    PortfolioNotFoundError,
    DuplicatePortfolioError,
    InvalidPortfolioDataError,
)

def create_portfolio(name: str, owner: str):
    # Validate input
    if not name or not owner:
        raise InvalidPortfolioDataError("Portfolio name and owner are required")

    # Check for duplicates
    existing = db.query(Portfolio).filter_by(name=name, owner=owner).first()
    if existing:
        raise DuplicatePortfolioError(name, owner)

    # Create portfolio
    portfolio = Portfolio(name=name, owner=owner)
    db.add(portfolio)
    db.commit()
    return portfolio

def update_portfolio(portfolio_id: UUID, name: str):
    portfolio = db.query(Portfolio).filter_by(id=portfolio_id).first()
    if not portfolio:
        raise PortfolioNotFoundError(portfolio_id)

    portfolio.name = name
    db.commit()
    return portfolio
```

### Market Data Operations

```python
from backend.common.exceptions import (
    MarketDataUnavailableError,
    PriceDataNotFoundError,
    InvalidTickerError,
)

def get_current_price(ticker: str):
    # Validate ticker format
    if not ticker or not ticker.isalpha():
        raise InvalidTickerError(ticker)

    try:
        price = external_api.get_price(ticker)
        if price is None:
            raise PriceDataNotFoundError(ticker)
        return price
    except APIError as e:
        raise MarketDataUnavailableError(
            ticker=ticker,
            reason=f"API error: {str(e)}"
        )
```

### Infrastructure Operations

```python
from backend.common.exceptions import (
    CacheConnectionError,
    CacheOperationError,
    DatabaseConnectionError,
    MessagePublishError,
)

def get_from_cache(key: str):
    try:
        return redis_client.get(key)
    except redis.ConnectionError as e:
        raise CacheConnectionError(reason=str(e))
    except redis.RedisError as e:
        raise CacheOperationError(
            operation="GET",
            key=key,
            reason=str(e)
        )

def publish_event(topic: str, event: dict):
    try:
        producer.send(topic, event)
    except KafkaError as e:
        raise MessagePublishError(topic=topic, reason=str(e))
```

## Testing Exception Handling

```python
import pytest
from backend.common.exceptions import (
    PortfolioNotFoundError,
    InsufficientHoldingQuantityError,
)

def test_portfolio_not_found_raises_error():
    """Test that accessing non-existent portfolio raises error."""
    portfolio_id = uuid4()

    with pytest.raises(PortfolioNotFoundError) as exc_info:
        portfolio_service.get_portfolio(portfolio_id)

    # Verify exception details
    assert str(portfolio_id) in str(exc_info.value)
    assert exc_info.value.details["portfolio_id"] == str(portfolio_id)

def test_insufficient_quantity_error_details():
    """Test that insufficient quantity error includes all details."""
    with pytest.raises(InsufficientHoldingQuantityError) as exc_info:
        portfolio_service.sell_shares("AAPL", owned=10.0, requested=15.0)

    exc = exc_info.value
    assert exc.details["ticker"] == "AAPL"
    assert exc.details["owned"] == 10.0
    assert exc.details["requested"] == 15.0
```

## Best Practices

1. **Use specific exceptions**: Prefer specific exceptions over generic ones
   ```python
   # Good
   raise PortfolioNotFoundError(portfolio_id)

   # Avoid
   raise NotFoundError(f"Portfolio {portfolio_id} not found")
   ```

2. **Include context in details**: Add relevant context to help with debugging
   ```python
   raise DatabaseOperationError(
       operation="INSERT",
       reason="Unique constraint violation"
   )
   ```

3. **Catch by category when appropriate**: Use base exception types for common handling
   ```python
   try:
       # ... code that might raise various NotFoundError subclasses
   except NotFoundError as e:
       # Handle all not found errors the same way
       return 404_response(e)
   ```

4. **Log with details**: Use the details dict for structured logging
   ```python
   except StockPortfolioError as e:
       logger.error(f"Error: {e.message}", extra={"error_details": e.details})
   ```

5. **Don't swallow exceptions**: Re-raise or convert to appropriate types
   ```python
   try:
       result = external_api.call()
   except ExternalAPIError as e:
       # Convert to our exception type
       raise MarketDataUnavailableError(ticker, reason=str(e))
   ```

## Migration Guide

To migrate existing code to use custom exceptions:

1. **Replace ValueError with specific exceptions**:
   ```python
   # Before
   if not portfolio:
       raise ValueError(f"Portfolio {id} not found")

   # After
   if not portfolio:
       raise PortfolioNotFoundError(id)
   ```

2. **Replace RuntimeError with infrastructure exceptions**:
   ```python
   # Before
   raise RuntimeError("Failed to connect to Kafka")

   # After
   raise KafkaConnectionError(reason="Connection failed")
   ```

3. **Update exception handlers**:
   ```python
   # Before
   except ValueError as e:
       if "not found" in str(e):
           return 404

   # After
   except NotFoundError as e:
       return 404
   ```

## Summary

The custom exceptions provide:
- ✅ Clear, descriptive error messages
- ✅ Structured error context via `details` dict
- ✅ Type-safe exception handling
- ✅ Consistent patterns across the codebase
- ✅ Better error tracking and debugging
- ✅ Domain-driven error handling

For the complete exception reference, see [backend/common/exceptions.py](../common/exceptions.py).
