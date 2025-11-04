from typing import Any


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
