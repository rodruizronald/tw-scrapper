"""Service for managing company data through the Company API."""

import logging

from clients.company_api.client import CompanyAPIClient
from clients.company_api.config import CompanyAPIConfig
from clients.company_api.exceptions import (
    CircuitBreakerError,
    CompanyAPIError,
    CompanyDuplicateError,
    CompanyNotFoundError,
    NetworkError,
)
from clients.company_api.models import Company, CompanyCreate

logger = logging.getLogger(__name__)


class CompanyService:
    """High-level service for managing company operations."""

    def __init__(self, config: CompanyAPIConfig | None = None):
        """
        Initialize Company service.

        Args:
            config: API client configuration. Uses defaults if not provided.
        """
        self.config = config or CompanyAPIConfig()
        self._client: CompanyAPIClient | None = None

    def __enter__(self):
        """Context manager entry - initialize client."""
        self._client = CompanyAPIClient(self.config)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close client."""
        if self._client:
            self._client.close()
            self._client = None

    @property
    def client(self) -> CompanyAPIClient:
        """Get or create the API client."""
        if self._client is None:
            self._client = CompanyAPIClient(self.config)
        return self._client

    def get_all_companies(self) -> list[Company]:
        """
        Retrieve all companies.

        Returns:
            List of all companies

        Raises:
            CompanyAPIError: If API request fails
            NetworkError: If network operation fails
            CircuitBreakerError: If too many failures occurred
        """
        try:
            logger.info("Retrieving all companies...")
            companies: list[Company] = self.client.list_companies()
            logger.info(f"Successfully retrieved {len(companies)} companies")
            return companies

        except CircuitBreakerError:
            logger.error("Circuit breaker is open - service temporarily unavailable")
            raise

        except NetworkError as e:
            logger.error(f"Network error while retrieving companies: {e}")
            raise

        except CompanyAPIError as e:
            logger.error(f"API error while retrieving companies: {e}")
            raise

    def create_company(self, name: str, is_active: bool = True) -> Company | None:
        """
        Create a new company.

        Args:
            name: Company name
            is_active: Whether company is active (default: True)

        Returns:
            Created Company object, or None if creation failed due to duplicate

        Raises:
            CompanyAPIError: If API request fails
            NetworkError: If network operation fails
            CircuitBreakerError: If too many failures occurred
        """
        try:
            logger.info(f"Creating company: {name} (active={is_active})")
            company_data = CompanyCreate(name=name, is_active=is_active)
            company = self.client.create_company(company_data)
            logger.info(
                f"Successfully created company: {company.name} (ID: {company.id})"
            )
            return company

        except CompanyDuplicateError as e:
            logger.warning(f"Company already exists: {name}")
            logger.debug(f"Duplicate error details: {e.details}")
            return None

        except CircuitBreakerError:
            logger.error("Circuit breaker is open - service temporarily unavailable")
            raise

        except NetworkError as e:
            logger.error(f"Network error while creating company '{name}': {e}")
            raise

        except CompanyAPIError as e:
            logger.error(f"API error while creating company '{name}': {e}")
            raise

    def delete_company(self, company_id: int) -> bool:
        """
        Delete a company by ID.

        Args:
            company_id: ID of the company to delete

        Returns:
            True if deleted successfully, False if company not found

        Raises:
            CompanyAPIError: If API request fails
            NetworkError: If network operation fails
            CircuitBreakerError: If too many failures occurred
        """
        try:
            logger.info(f"Deleting company with ID: {company_id}")
            self.client.delete_company(company_id)
            logger.info(f"Successfully deleted company with ID: {company_id}")
            return True

        except CompanyNotFoundError:
            logger.warning(f"Company with ID {company_id} not found")
            return False

        except CircuitBreakerError:
            logger.error("Circuit breaker is open - service temporarily unavailable")
            raise

        except NetworkError as e:
            logger.error(f"Network error while deleting company {company_id}: {e}")
            raise

        except CompanyAPIError as e:
            logger.error(f"API error while deleting company {company_id}: {e}")
            raise

    def find_company_by_name(self, name: str) -> Company | None:
        """
        Find a company by name.

        Args:
            name: Company name to search for

        Returns:
            Company object if found, None otherwise

        Raises:
            CompanyAPIError: If API request fails
            NetworkError: If network operation fails
            CircuitBreakerError: If too many failures occurred
        """
        logger.info(f"Searching for company: {name}")
        companies = self.get_all_companies()

        for company in companies:
            if company.name.lower() == name.lower():
                logger.info(f"Found company: {company.name} (ID: {company.id})")
                return company

        logger.info(f"Company not found: {name}")
        return None

    def get_active_companies(self) -> list[Company]:
        """
        Get all active companies.

        Returns:
            List of active companies

        Raises:
            CompanyAPIError: If API request fails
            NetworkError: If network operation fails
            CircuitBreakerError: If too many failures occurred
        """
        logger.info("Retrieving active companies...")
        companies = self.get_all_companies()
        active_companies = [c for c in companies if c.is_active]
        logger.info(f"Found {len(active_companies)} active companies")
        return active_companies

    def close(self):
        """Close the underlying API client."""
        if self._client:
            self._client.close()
            self._client = None
