import json
from pathlib import Path
from typing import Any

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


def save_task_results(
    results: dict[str, Any],
    output_dir: Path,
    filename: str,
) -> Path:
    """
    Save task results to a JSON file.

    Args:
        results: Results dictionary to save
        output_dir: Directory to save results in
        filename: Name of the output file

    Returns:
        Path to the saved file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return output_path
