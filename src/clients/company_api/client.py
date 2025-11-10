"""HTTP client for Company API."""

import logging

import httpx
from pybreaker import CircuitBreaker
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from clients.company_api.config import CompanyAPIConfig
from clients.company_api.exceptions import (
    CircuitBreakerError,
    CompanyAPIError,
    CompanyDuplicateError,
    CompanyNotFoundError,
    InternalServerError,
    InvalidRequestError,
    NetworkError,
)
from clients.company_api.models import Company, CompanyCreate

logger = logging.getLogger(__name__)


class CompanyAPIClient:
    """HTTP client for interacting with the Company API."""

    def __init__(self, config: CompanyAPIConfig | None = None):
        """
        Initialize Company API client.

        Args:
            config: API client configuration. Uses defaults if not provided.
        """
        self.config = config or CompanyAPIConfig()
        self._client = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

        # Initialize circuit breaker
        self._circuit_breaker = CircuitBreaker(
            fail_max=self.config.circuit_failure_threshold,
            reset_timeout=self.config.circuit_recovery_timeout,
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close HTTP client."""
        self.close()

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def list_companies(self) -> list[Company]:
        """
        Retrieve all companies from the API.

        Returns:
            List of Company objects

        Raises:
            InternalServerError: If server returns 500 error
            NetworkError: If network operation fails
            CircuitBreakerError: If circuit breaker is open
            CompanyAPIError: For other API errors
        """
        try:
            response = self._circuit_breaker.call(
                self._make_request_with_retry, "GET", "/companies"
            )
        except Exception as e:
            if self._circuit_breaker.current_state == "open":
                raise CircuitBreakerError() from e
            raise

        if response.status_code == 200:
            companies_data = response.json()
            logger.info(f"Retrieved {len(companies_data)} companies")
            return [Company.from_dict(data) for data in companies_data]

        self._handle_error_response(response)
        return []  # unreachable, but makes type checker happy

    def create_company(self, company: CompanyCreate) -> Company:
        """
        Create a new company.

        Args:
            company: Company data to create

        Returns:
            Created Company object

        Raises:
            InvalidRequestError: If request data is invalid (400)
            CompanyDuplicateError: If company name already exists (409)
            InternalServerError: If server returns 500 error
            NetworkError: If network operation fails
            CircuitBreakerError: If circuit breaker is open
            CompanyAPIError: For other API errors
        """
        payload = {"name": company.name, "is_active": company.is_active}

        try:
            response = self._circuit_breaker.call(
                self._make_request_with_retry, "POST", "/companies", json=payload
            )
        except Exception as e:
            if self._circuit_breaker.current_state == "open":
                raise CircuitBreakerError() from e
            raise

        if response.status_code == 201:
            company_data = response.json()
            created_company = Company.from_dict(company_data)
            logger.info(
                f"Created company: {created_company.name} (ID: {created_company.id})"
            )
            return created_company

        self._handle_error_response(response)
        return Company(
            0, "", False, "", ""
        )  # unreachable, but makes type checker happy

    def delete_company(self, company_id: int) -> None:
        """
        Delete a company by ID.

        Args:
            company_id: ID of the company to delete

        Raises:
            InvalidRequestError: If company ID is invalid (400)
            CompanyNotFoundError: If company doesn't exist (404)
            InternalServerError: If server returns 500 error
            NetworkError: If network operation fails
            CircuitBreakerError: If circuit breaker is open
            CompanyAPIError: For other API errors
        """
        try:
            response = self._circuit_breaker.call(
                self._make_request_with_retry, "DELETE", f"/companies/{company_id}"
            )
        except Exception as e:
            if self._circuit_breaker.current_state == "open":
                raise CircuitBreakerError() from e
            raise

        if response.status_code == 204:
            logger.info(f"Deleted company with ID: {company_id}")
            return

        self._handle_error_response(response, company_id=company_id)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    def _make_request_with_retry(
        self, method: str, endpoint: str, **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with automatic retry on network errors.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to httpx request

        Returns:
            HTTP response

        Raises:
            NetworkError: If network operation fails after retries
        """
        try:
            logger.debug(f"{method} {endpoint}")
            return self._client.request(method, endpoint, **kwargs)

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.warning(f"Network error during {method} {endpoint}: {e}")
            raise NetworkError(str(e), original_error=e) from e

        except Exception as e:
            logger.error(f"Unexpected error during {method} {endpoint}: {e}")
            raise CompanyAPIError(f"Request failed: {e}") from e

    def _handle_error_response(
        self, response: httpx.Response, company_id: int | None = None
    ) -> None:
        """
        Handle error responses from the API.

        Args:
            response: HTTP response object
            company_id: Optional company ID for context

        Raises:
            Appropriate CompanyAPIError subclass based on status code and error code
        """
        try:
            error_data = response.json().get("error", {})
            error_code = error_data.get("code", "UNKNOWN")
            error_message = error_data.get("message", "Unknown error")
            error_details = error_data.get("details", [])
        except Exception:
            # If we can't parse the error response, create a generic one
            error_code = "UNKNOWN"
            error_message = response.text or f"HTTP {response.status_code}"
            error_details = []

        logger.error(
            f"API error - Status: {response.status_code}, Code: {error_code}, "
            f"Message: {error_message}, Details: {error_details}"
        )

        # Map status codes and error codes to specific exceptions
        if response.status_code == 400:
            raise InvalidRequestError(error_message, details=error_details)

        if response.status_code == 404:
            if company_id:
                raise CompanyNotFoundError(company_id, details=error_details)
            raise CompanyNotFoundError(0, details=error_details)

        if response.status_code == 409:
            raise CompanyDuplicateError("unknown", details=error_details)

        if response.status_code == 500:
            raise InternalServerError(error_message, details=error_details)

        # Generic error for unexpected status codes
        raise CompanyAPIError(
            error_message,
            status_code=response.status_code,
            error_code=error_code,
            details=error_details,
        )
