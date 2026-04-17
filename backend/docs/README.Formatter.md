# Response Envelope Formatter

> Standardized response envelope formatter for consistent API responses across the Stock Portfolio Dashboard backend.

📚 **[Documentation Index](README.md)** | 🏠 **[Main README](../README.md)**

---

## Table of Contents
- [Overview](#overview)
- [Response Structure](#response-structure)
- [Features](#features)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

---

## Overview

A standardized response envelope formatter for consistent API responses across the Stock Portfolio Dashboard backend.

## Features

- ✅ **Consistent Structure**: All API responses follow the same envelope format
- ✅ **Type Safety**: Full Pydantic models with type hints
- ✅ **Pagination Support**: Built-in pagination metadata handling
- ✅ **Error Handling**: Structured error details with codes and messages
- ✅ **Metadata Support**: Flexible metadata field for additional context
- ✅ **Timestamp Tracking**: Automatic UTC timestamps on all responses
- ✅ **Helper Functions**: Convenient functions for common response patterns

## Response Structure

All API responses follow this structure:

```json
{
  "success": true,
  "data": { "id": 123, "name": "Example" },
  "message": "Operation completed successfully",
  "errors": null,
  "metadata": { "request_id": "abc-123" },
  "timestamp": "2026-04-05T10:30:00.000Z"
}
```

### Fields

- **success** (boolean): Indicates if the request was successful
- **data** (any|null): The response payload (null on error)
- **message** (string|null): Optional human-readable message
- **errors** (array|null): Array of error details (null on success)
- **metadata** (object|null): Additional metadata (pagination, timing, etc.)
- **timestamp** (string): UTC timestamp of the response

## Installation

The formatter is built with Pydantic and is already available in the backend:

```python
from backend.gateway.formatter import (
    success_response,
    error_response,
    paginated_response,
    not_found_response,
    # ... other helpers
)
```

## Usage Examples

### 1. Success Response

```python
from backend.gateway.formatter import success_response

@app.get("/api/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: int):
    portfolio = {"id": portfolio_id, "name": "Tech Stocks"}
    return success_response(portfolio, "Portfolio retrieved successfully")
```

Response:
```json
{
  "success": true,
  "data": { "id": 123, "name": "Tech Stocks" },
  "message": "Portfolio retrieved successfully",
  "errors": null,
  "metadata": null,
  "timestamp": "2026-04-05T10:30:00.000Z"
}
```

### 2. Resource Not Found

```python
from backend.gateway.formatter import not_found_response

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    user = db.get_user(user_id)

    if user is None:
        return not_found_response("User", user_id)

    return success_response(user)
```

Response (404):
```json
{
  "success": false,
  "data": null,
  "message": "User not found",
  "errors": [
    {
      "code": "NOT_FOUND",
      "message": "The requested User with id 123 was not found",
      "field": null,
      "details": { "resource": "User", "identifier": "123" }
    }
  ],
  "metadata": null,
  "timestamp": "2026-04-05T10:30:00.000Z"
}
```

### 3. Paginated List Response

```python
from backend.gateway.formatter import paginated_response

@app.get("/api/portfolios")
async def list_portfolios(page: int = 1, page_size: int = 10):
    portfolios = db.get_portfolios(page, page_size)
    total_count = db.count_portfolios()

    return paginated_response(
        data=portfolios,
        page=page,
        page_size=page_size,
        total_items=total_count
    )
```

Response:
```json
{
  "success": true,
  "data": [
    { "id": 1, "name": "Tech Stocks" },
    { "id": 2, "name": "Blue Chips" }
  ],
  "message": null,
  "errors": null,
  "metadata": {
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_items": 47,
      "total_pages": 5,
      "has_next": true,
      "has_previous": false
    }
  },
  "timestamp": "2026-04-05T10:30:00.000Z"
}
```

### 4. Validation Errors

```python
from backend.gateway.formatter import validation_error_response

@app.post("/api/users")
async def create_user(user_data: dict):
    # Pydantic validation errors
    errors = [
        {"loc": ["body", "email"], "msg": "field required", "type": "value_error.missing"},
        {"loc": ["body", "age"], "msg": "value is not a valid integer", "type": "type_error.integer"}
    ]

    return validation_error_response(errors)
```

Response (400):
```json
{
  "success": false,
  "data": null,
  "message": "Validation failed",
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "field required",
      "field": "email",
      "details": { "type": "value_error.missing", "loc": ["body", "email"] }
    },
    {
      "code": "VALIDATION_ERROR",
      "message": "value is not a valid integer",
      "field": "age",
      "details": { "type": "type_error.integer", "loc": ["body", "age"] }
    }
  ],
  "metadata": null,
  "timestamp": "2026-04-05T10:30:00.000Z"
}
```

### 5. Created Resource (201)

```python
from backend.gateway.formatter import created_response

@app.post("/api/portfolios")
async def create_portfolio(portfolio_data: dict):
    new_portfolio = db.create_portfolio(portfolio_data)
    return created_response(new_portfolio, "Portfolio created successfully")
```

### 6. Unauthorized Access (401)

```python
from backend.gateway.formatter import unauthorized_response

@app.get("/api/admin/settings")
async def get_settings(token: str | None = None):
    if not token:
        return unauthorized_response("Authentication token required")

    # Validate token...
```

### 7. Forbidden Access (403)

```python
from backend.gateway.formatter import forbidden_response

@app.delete("/api/portfolios/{id}")
async def delete_portfolio(id: int, user_role: str):
    if user_role != "admin":
        return forbidden_response(
            "Cannot delete portfolio",
            "Only administrators can delete portfolios"
        )
```

### 8. Server Error (500)

```python
from backend.gateway.formatter import server_error_response

@app.get("/api/data/{id}")
async def get_data(id: int):
    try:
        data = external_api.fetch(id)
        return success_response(data)
    except Exception as e:
        return server_error_response(
            "Failed to fetch data",
            details={"trace_id": "abc-123"}
        )
```

## Available Helper Functions

### Success Responses

- **`success_response(data, message=None, metadata=None)`** - Generic success response
- **`created_response(data, message="Resource created successfully")`** - 201 Created
- **`no_content_response(message="Operation completed successfully")`** - 204 No Content

### Error Responses

- **`error_response(message, errors=None, metadata=None)`** - Generic error response
- **`not_found_response(resource, identifier=None)`** - 404 Not Found
- **`unauthorized_response(message="Unauthorized access")`** - 401 Unauthorized
- **`forbidden_response(message="Access forbidden", reason=None)`** - 403 Forbidden
- **`bad_request_response(message="Bad request", errors=None)`** - 400 Bad Request
- **`conflict_response(resource, message=None)`** - 409 Conflict
- **`server_error_response(message="Internal server error", details=None)`** - 500 Internal Server Error
- **`validation_error_response(validation_errors, message="Validation failed")`** - 400 Validation Error

### Paginated Responses

- **`paginated_response(data, page, page_size, total_items, message=None, additional_metadata=None)`** - Paginated list response

## Error Detail Structure

Each error in the `errors` array follows this structure:

```python
{
    "code": "ERROR_CODE",           # Machine-readable error code
    "message": "Human readable message",
    "field": "field_name",          # Optional: field that caused the error
    "details": {                    # Optional: additional context
        "key": "value"
    }
}
```

### Common Error Codes

- `VALIDATION_ERROR` - Input validation failed
- `NOT_FOUND` - Resource not found
- `UNAUTHORIZED` - Authentication required
- `FORBIDDEN` - Insufficient permissions
- `BAD_REQUEST` - Invalid request
- `CONFLICT` - Resource conflict (duplicate)
- `INTERNAL_ERROR` - Server error

## Best Practices

### 1. Always Use Helper Functions

```python
# ✅ Good
return success_response(data, "User retrieved")

# ❌ Avoid
return {"success": True, "data": data}
```

### 2. Provide Meaningful Messages

```python
# ✅ Good
return not_found_response("User", user_id)

# ❌ Less helpful
return error_response("Not found")
```

### 3. Include Metadata for Context

```python
# ✅ Good
metadata = {
    "query_time_ms": 142,
    "cache_hit": True,
    "source": "database"
}
return success_response(data, metadata=metadata)
```

### 4. Use Appropriate Error Responses

```python
# For validation errors
return validation_error_response(errors)

# For missing resources
return not_found_response("Portfolio", portfolio_id)

# For permission issues
return forbidden_response("Access denied", "Admin role required")
```

### 5. Pagination for Lists

```python
# Always use paginated_response for lists
return paginated_response(
    data=items,
    page=page,
    page_size=page_size,
    total_items=total_count
)
```

## Testing

Comprehensive tests are available in `tests/test_formatter.py`:

```bash
# Run formatter tests
pytest backend/tests/test_formatter.py -v

# Run with coverage
pytest backend/tests/test_formatter.py --cov=backend.gateway.formatter --cov-report=html
```

## Integration with FastAPI

### Exception Handler Example

```python
from fastapi import FastAPI, HTTPException
from backend.gateway.formatter import not_found_response, server_error_response

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 404:
        return not_found_response("Resource")
    return error_response(exc.detail)

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return server_error_response("An unexpected error occurred")
```

### Dependency Injection Pattern

```python
from fastapi import Depends, HTTPException
from backend.gateway.formatter import unauthorized_response

async def verify_token(token: str = Header(...)):
    if not is_valid_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

@app.get("/api/protected")
async def protected_route(token: str = Depends(verify_token)):
    return success_response({"message": "Access granted"})
```

## Related Files

- [`backend/gateway/formatter.py`](../formatter.py) - Main implementation
- [`backend/gateway/formatter_examples.py`](../formatter_examples.py) - Usage examples
- [`backend/tests/test_formatter.py`](../../tests/test_formatter.py) - Unit tests

## Additional Resources

- [FastAPI Response Models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [REST API Best Practices](https://restfulapi.net/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

---

## See Also

- **[Domain Architecture](README.Domains.md)** - Using formatters in domain services
- **[API Versioning](README.Versioning.md)** - Version headers in responses
- **[Authentication](README.Auth.md)** - Error formatting for auth failures

---

**Last Updated**: April 2026
**Component**: Response Formatting
**Module**: `backend/gateway/formatter.py`
