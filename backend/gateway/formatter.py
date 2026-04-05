"""
Response envelope formatter for consistent API responses.

Provides standardized response structure with success/error handling, pagination, and validation.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""

    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=1000)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)
    has_next: bool
    has_previous: bool


class ErrorDetail(BaseModel):
    """Error detail with code, message, and optional field/context."""

    code: str
    message: str
    field: str | None = None
    details: dict[str, Any] | None = None


class ResponseEnvelope(BaseModel, Generic[T]):
    """Generic response envelope for all API responses."""

    success: bool
    data: T | None = None
    message: str | None = None
    errors: list[ErrorDetail] | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Core response functions


def success_response(
    data: Any, message: str | None = None, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create a success response with optional message and metadata."""
    envelope: ResponseEnvelope[Any] = ResponseEnvelope(
        success=True, data=data, message=message, metadata=metadata
    )
    return envelope.model_dump(mode="json")


def error_response(
    message: str,
    errors: list[ErrorDetail] | list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an error response with optional error details."""
    error_details: list[ErrorDetail] | None = None
    if errors:
        if isinstance(errors[0], dict):
            error_details = [ErrorDetail(**err) for err in errors]  # type: ignore[arg-type]
        else:
            error_details = errors  # type: ignore[assignment]

    envelope: ResponseEnvelope[None] = ResponseEnvelope(
        success=False, data=None, message=message, errors=error_details, metadata=metadata
    )
    return envelope.model_dump(mode="json")


def paginated_response(
    data: list[Any],
    page: int,
    page_size: int,
    total_items: int,
    message: str | None = None,
    additional_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a paginated response with pagination metadata."""
    import math

    total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
    pagination = PaginationMetadata(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )

    metadata = {"pagination": pagination.model_dump()}
    if additional_metadata:
        metadata.update(additional_metadata)

    return success_response(data, message, metadata)


def validation_error_response(
    validation_errors: list[dict[str, Any]], message: str = "Validation failed"
) -> dict[str, Any]:
    """Convert Pydantic validation errors to error response."""
    errors = []
    for err in validation_errors:
        field = err.get("loc", [])[-1] if err.get("loc") else None
        errors.append(
            ErrorDetail(
                code="VALIDATION_ERROR",
                message=err.get("msg", "Validation error"),
                field=str(field) if field is not None else None,
                details={"type": err.get("type"), "loc": err.get("loc")},
            )
        )
    return error_response(message, errors)


def not_found_response(resource: str, identifier: str | int | None = None) -> dict[str, Any]:
    """Create a 404 Not Found response for a resource."""
    message = f"{resource} not found"
    error_msg = f"The requested {resource}"
    if identifier is not None:
        error_msg += f" with id {identifier}"
    error_msg += " was not found"

    error = ErrorDetail(
        code="NOT_FOUND",
        message=error_msg,
        details=(
            {"resource": resource, "identifier": str(identifier)}
            if identifier
            else {"resource": resource}
        ),
    )
    return error_response(message, [error])
