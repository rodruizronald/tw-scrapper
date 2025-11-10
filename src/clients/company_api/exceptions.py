"""Exceptions for Company API client."""


class CompanyAPIError(Exception):
    """Base exception for Company API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
        details: list[str] | None = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []
        super().__init__(message)


class CompanyNotFoundError(CompanyAPIError):
    """Company with specified ID was not found."""

    def __init__(self, company_id: int, details: list[str] | None = None):
        super().__init__(
            f"Company with ID {company_id} not found",
            status_code=404,
            error_code="COMPANY_NOT_FOUND",
            details=details,
        )


class CompanyDuplicateError(CompanyAPIError):
    """Company with the same name already exists."""

    def __init__(self, company_name: str, details: list[str] | None = None):
        super().__init__(
            f"Company with name '{company_name}' already exists",
            status_code=409,
            error_code="COMPANY_DUPLICATE",
            details=details,
        )


class InvalidRequestError(CompanyAPIError):
    """Invalid request parameters or body."""

    def __init__(self, message: str, details: list[str] | None = None):
        super().__init__(
            f"Invalid request: {message}",
            status_code=400,
            error_code="INVALID_REQUEST",
            details=details,
        )


class InternalServerError(CompanyAPIError):
    """Server-side error occurred."""

    def __init__(self, message: str, details: list[str] | None = None):
        super().__init__(
            f"Internal server error: {message}",
            status_code=500,
            error_code="INTERNAL_ERROR",
            details=details,
        )


class NetworkError(CompanyAPIError):
    """Network-related error (timeout, connection failure, etc.)."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(f"Network error: {message}", status_code=None)


class CircuitBreakerError(CompanyAPIError):
    """Circuit breaker is open, preventing requests."""

    def __init__(self):
        super().__init__(
            "Circuit breaker is open - too many failures. Please try again later.",
            status_code=None,
        )
