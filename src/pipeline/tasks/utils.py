from typing import Any

from src.core.models.domain import CompanyData


def company_task_run_name(parameters: dict[str, Any]) -> str:
    """Generate a clean task run name from company data."""
    try:
        company = parameters.get("company")
        if company and hasattr(company, "name"):
            # Create a URL-safe slug from company name
            company_slug = company.name.lower().replace(" ", "-")
            return f"{company_slug[:30]}"
    except Exception:
        pass
    return "company-extraction"


def filter_enabled_companies(companies: list[CompanyData]) -> list[CompanyData]:
    """
    Filter list to only include enabled companies.

    Args:
        companies: List of companies to filter

    Returns:
        List of enabled companies
    """
    return [company for company in companies if company.enabled]
