from pipeline.core.models import CompanyData


def filter_enabled_companies(companies: list[CompanyData]) -> list[CompanyData]:
    """
    Filter list to only include enabled companies.

    Args:
        companies: List of companies to filter

    Returns:
        List of enabled companies
    """
    return [company for company in companies if company.enabled]
