"""
Unit tests for Response envelope formatter.
"""

from datetime import datetime

from backend.gateway.formatter import (
    ErrorDetail,
    PaginationMetadata,
    ResponseEnvelope,
    error_response,
    not_found_response,
    paginated_response,
    success_response,
    validation_error_response,
)


class TestResponseEnvelopeModels:
    """Test Pydantic models for response envelopes."""

    def test_pagination_metadata_creation(self) -> None:
        """Test creating pagination metadata."""
        pagination = PaginationMetadata(
            page=1,
            page_size=10,
            total_items=25,
            total_pages=3,
            has_next=True,
            has_previous=False,
        )

        assert pagination.page == 1
        assert pagination.page_size == 10
        assert pagination.total_items == 25
        assert pagination.total_pages == 3
        assert pagination.has_next is True
        assert pagination.has_previous is False

    def test_error_detail_creation(self) -> None:
        """Test creating error detail."""
        error = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Email is required",
            field="email",
            details={"type": "value_error.missing"},
        )

        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Email is required"
        assert error.field == "email"
        assert error.details == {"type": "value_error.missing"}

    def test_error_detail_without_optional_fields(self) -> None:
        """Test error detail with only required fields."""
        error = ErrorDetail(code="GENERAL_ERROR", message="Something went wrong")

        assert error.code == "GENERAL_ERROR"
        assert error.message == "Something went wrong"
        assert error.field is None
        assert error.details is None

    def test_response_envelope_success(self) -> None:
        """Test success response envelope."""
        envelope = ResponseEnvelope(
            success=True, data={"id": 123, "name": "Test"}, message="Success"
        )

        assert envelope.success is True
        assert envelope.data == {"id": 123, "name": "Test"}
        assert envelope.message == "Success"
        assert envelope.errors is None
        assert isinstance(envelope.timestamp, datetime)

    def test_response_envelope_error(self) -> None:
        """Test error response envelope."""
        errors = [ErrorDetail(code="ERROR", message="Failed")]
        envelope = ResponseEnvelope(
            success=False, data=None, message="Operation failed", errors=errors, metadata=None
        )

        assert envelope.success is False
        assert envelope.data is None
        assert envelope.message == "Operation failed"
        assert envelope.errors is not None
        assert len(envelope.errors) == 1
        assert envelope.errors[0].code == "ERROR"


class TestSuccessResponse:
    """Test success response helpers."""

    def test_success_response_basic(self) -> None:
        """Test basic success response."""
        response = success_response({"id": 1, "name": "John"})

        assert response["success"] is True
        assert response["data"] == {"id": 1, "name": "John"}
        assert response["message"] is None
        assert response["errors"] is None
        assert "timestamp" in response

    def test_success_response_with_message(self) -> None:
        """Test success response with message."""
        response = success_response({"id": 1}, "User retrieved successfully")

        assert response["success"] is True
        assert response["data"] == {"id": 1}
        assert response["message"] == "User retrieved successfully"

    def test_success_response_with_metadata(self) -> None:
        """Test success response with metadata."""
        metadata = {"request_id": "abc-123", "duration_ms": 45}
        response = success_response({"id": 1}, metadata=metadata)

        assert response["success"] is True
        assert response["metadata"] == metadata

    def test_success_response_with_all_fields(self) -> None:
        """Test success response with all optional fields."""
        metadata = {"version": "1.0"}
        response = success_response(data={"id": 1}, message="Created", metadata=metadata)

        assert response["success"] is True
        assert response["data"] == {"id": 1}
        assert response["message"] == "Created"
        assert response["metadata"] == metadata


class TestErrorResponse:
    """Test error response helpers."""

    def test_error_response_basic(self) -> None:
        """Test basic error response."""
        response = error_response("Something went wrong")

        assert response["success"] is False
        assert response["data"] is None
        assert response["message"] == "Something went wrong"
        assert response["errors"] is None

    def test_error_response_with_error_details(self) -> None:
        """Test error response with error details."""
        errors = [ErrorDetail(code="NOT_FOUND", message="User not found")]
        response = error_response("User not found", errors)

        assert response["success"] is False
        assert response["message"] == "User not found"
        assert len(response["errors"]) == 1
        assert response["errors"][0]["code"] == "NOT_FOUND"

    def test_error_response_with_dict_errors(self) -> None:
        """Test error response accepts dict errors."""
        errors = [{"code": "INVALID", "message": "Invalid input"}]
        response = error_response("Validation failed", errors)

        assert response["success"] is False
        assert len(response["errors"]) == 1
        assert response["errors"][0]["code"] == "INVALID"

    def test_error_response_with_multiple_errors(self) -> None:
        """Test error response with multiple errors."""
        errors = [
            ErrorDetail(code="E1", message="Error 1"),
            ErrorDetail(code="E2", message="Error 2"),
        ]
        response = error_response("Multiple errors", errors)

        assert len(response["errors"]) == 2
        assert response["errors"][0]["code"] == "E1"
        assert response["errors"][1]["code"] == "E2"


class TestPaginatedResponse:
    """Test paginated response helper."""

    def test_paginated_response_first_page(self) -> None:
        """Test paginated response for first page."""
        data = [{"id": 1}, {"id": 2}]
        response = paginated_response(data=data, page=1, page_size=10, total_items=25)

        assert response["success"] is True
        assert response["data"] == data
        assert "pagination" in response["metadata"]

        pagination = response["metadata"]["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 10
        assert pagination["total_items"] == 25
        assert pagination["total_pages"] == 3
        assert pagination["has_next"] is True
        assert pagination["has_previous"] is False

    def test_paginated_response_middle_page(self) -> None:
        """Test paginated response for middle page."""
        data = [{"id": 11}, {"id": 12}]
        response = paginated_response(data=data, page=2, page_size=10, total_items=25)

        pagination = response["metadata"]["pagination"]
        assert pagination["page"] == 2
        assert pagination["has_next"] is True
        assert pagination["has_previous"] is True

    def test_paginated_response_last_page(self) -> None:
        """Test paginated response for last page."""
        data = [{"id": 21}]
        response = paginated_response(data=data, page=3, page_size=10, total_items=25)

        pagination = response["metadata"]["pagination"]
        assert pagination["page"] == 3
        assert pagination["has_next"] is False
        assert pagination["has_previous"] is True

    def test_paginated_response_single_page(self) -> None:
        """Test paginated response with all items on one page."""
        data = [{"id": 1}, {"id": 2}]
        response = paginated_response(data=data, page=1, page_size=10, total_items=2)

        pagination = response["metadata"]["pagination"]
        assert pagination["total_pages"] == 1
        assert pagination["has_next"] is False
        assert pagination["has_previous"] is False

    def test_paginated_response_with_additional_metadata(self) -> None:
        """Test paginated response with additional metadata."""
        data = [{"id": 1}]
        additional_metadata = {"query_time_ms": 42, "source": "cache"}
        response = paginated_response(
            data=data,
            page=1,
            page_size=10,
            total_items=100,
            additional_metadata=additional_metadata,
        )

        assert "pagination" in response["metadata"]
        assert response["metadata"]["query_time_ms"] == 42
        assert response["metadata"]["source"] == "cache"

    def test_paginated_response_empty_results(self) -> None:
        """Test paginated response with no results."""
        response = paginated_response(data=[], page=1, page_size=10, total_items=0)

        assert response["data"] == []
        pagination = response["metadata"]["pagination"]
        assert pagination["total_items"] == 0
        assert pagination["total_pages"] == 0


class TestValidationErrorResponse:
    """Test validation error response helper."""

    def test_validation_error_response_single_error(self) -> None:
        """Test validation error response with single error."""
        errors = [
            {"loc": ["body", "email"], "msg": "field required", "type": "value_error.missing"}
        ]
        response = validation_error_response(errors)

        assert response["success"] is False
        assert response["message"] == "Validation failed"
        assert len(response["errors"]) == 1
        assert response["errors"][0]["code"] == "VALIDATION_ERROR"
        assert response["errors"][0]["field"] == "email"

    def test_validation_error_response_multiple_errors(self) -> None:
        """Test validation error response with multiple errors."""
        errors = [
            {"loc": ["body", "email"], "msg": "field required", "type": "value_error.missing"},
            {
                "loc": ["body", "age"],
                "msg": "value is not a valid integer",
                "type": "type_error.integer",
            },
        ]
        response = validation_error_response(errors)

        assert len(response["errors"]) == 2
        assert response["errors"][0]["field"] == "email"
        assert response["errors"][1]["field"] == "age"

    def test_validation_error_response_custom_message(self) -> None:
        """Test validation error response with custom message."""
        errors = [{"loc": ["body", "name"], "msg": "too short", "type": "value_error"}]
        response = validation_error_response(errors, "Input validation error")

        assert response["message"] == "Input validation error"


class TestNotFoundResponse:
    """Test not found error response helper."""

    def test_not_found_response(self) -> None:
        """Test not found response."""
        response = not_found_response("User", 123)

        assert response["success"] is False
        assert response["message"] == "User not found"
        assert len(response["errors"]) == 1
        assert response["errors"][0]["code"] == "NOT_FOUND"
        assert "123" in response["errors"][0]["message"]

    def test_not_found_response_without_identifier(self) -> None:
        """Test not found response without identifier."""
        response = not_found_response("Portfolio")

        assert response["message"] == "Portfolio not found"
        assert response["errors"][0]["details"]["resource"] == "Portfolio"
