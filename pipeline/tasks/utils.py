import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from prefect import get_run_logger, task

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData


def prepare_company_data_for_task(company: CompanyData) -> dict[str, Any]:
    """
    Convert CompanyData object to dictionary for Prefect task serialization.

    Args:
        company: CompanyData object to convert

    Returns:
        Dictionary representation of company data
    """
    return company.to_dict()


def prepare_config_for_task(config: PipelineConfig) -> dict[str, Any]:
    """
    Convert PipelineConfig object to dictionary for Prefect task serialization.

    Args:
        config: PipelineConfig object to convert

    Returns:
        Dictionary representation of configuration
    """
    return config.to_dict()


def filter_enabled_companies(companies: list[CompanyData]) -> list[CompanyData]:
    """
    Filter list to only include enabled companies.

    Args:
        companies: List of companies to filter

    Returns:
        List of enabled companies
    """
    return [company for company in companies if company.enabled]


@task(
    name="Aggregate Results",
    description="Aggregate results from multiple company processing tasks",
    tags=["aggregation", "results"],
)
async def aggregate_results_task(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate results from multiple company processing tasks.

    Args:
        results: List of processing results from individual companies

    Returns:
        Aggregated results with summary statistics
    """
    logger = get_run_logger()

    logger.info(f"📊 Aggregating results from {len(results)} companies")

    # Initialize counters
    total_companies = len(results)
    successful_companies = 0
    failed_companies = 0
    total_jobs_found = 0
    total_jobs_saved = 0
    total_processing_time = 0.0
    retryable_failures = 0
    non_retryable_failures = 0

    # Process each result
    for result in results:
        if result.get("success", False):
            successful_companies += 1
            total_jobs_found += result.get("jobs_found", 0)
            total_jobs_saved += result.get("jobs_saved", 0)
        else:
            failed_companies += 1
            if result.get("retryable", True):
                retryable_failures += 1
            else:
                non_retryable_failures += 1

        total_processing_time += result.get("processing_time", 0.0)

    # Calculate derived metrics
    success_rate = (
        successful_companies / total_companies if total_companies > 0 else 0.0
    )
    average_processing_time = (
        total_processing_time / total_companies if total_companies > 0 else 0.0
    )

    aggregated_results = {
        # Basic counts
        "total_companies": total_companies,
        "successful_companies": successful_companies,
        "failed_companies": failed_companies,
        # Success metrics
        "success_rate": success_rate,
        "total_jobs_found": total_jobs_found,
        "total_jobs_saved": total_jobs_saved,
        # Timing metrics
        "total_processing_time": total_processing_time,
        "average_processing_time": average_processing_time,
        # Error analysis
        "retryable_failures": retryable_failures,
        "non_retryable_failures": non_retryable_failures,
        # Detailed results for further analysis
        "detailed_results": results,
        # Metadata
        "aggregation_timestamp": datetime.now(UTC).isoformat(),
    }

    logger.info(
        f"✅ Aggregation complete: {successful_companies}/{total_companies} successful"
    )
    logger.info(f"📋 Total jobs: {total_jobs_found} found, {total_jobs_saved} saved")

    return aggregated_results


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


def create_processing_summary(
    results: list[dict[str, Any]],
    output_dir: Path,
) -> Path:
    """
    Create a processing summary file with key metrics and failed companies.

    Args:
        results: List of processing results
        output_dir: Directory to save summary in

    Returns:
        Path to the summary file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate summary
    successful_results = [r for r in results if r.get("success", False)]
    failed_results = [r for r in results if not r.get("success", False)]

    summary = {
        "execution_timestamp": datetime.now(UTC).isoformat(),
        "summary": {
            "total_companies": len(results),
            "successful_companies": len(successful_results),
            "failed_companies": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0.0,
            "total_jobs_found": sum(r.get("jobs_found", 0) for r in successful_results),
            "total_jobs_saved": sum(r.get("jobs_saved", 0) for r in successful_results),
        },
        "successful_companies": [
            {
                "company_name": r.get("company_name"),
                "jobs_found": r.get("jobs_found", 0),
                "jobs_saved": r.get("jobs_saved", 0),
                "processing_time": r.get("processing_time", 0.0),
                "output_path": str(r.get("output_path", "")),
            }
            for r in successful_results
        ],
        "failed_companies": [
            {
                "company_name": r.get("company_name"),
                "error": r.get("error"),
                "error_type": r.get("error_type"),
                "retryable": r.get("retryable", True),
                "processing_time": r.get("processing_time", 0.0),
            }
            for r in failed_results
        ],
    }

    # Save summary
    summary_path = output_dir / "processing_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary_path
