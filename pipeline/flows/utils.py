import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData


def load_companies_from_file(companies_file: Path) -> list[CompanyData]:
    """
    Load companies from JSON file.

    Args:
        companies_file: Path to companies JSON file

    Returns:
        List of CompanyData objects

    Raises:
        FileNotFoundError: If companies file doesn't exist
        ValueError: If companies file format is invalid
    """
    if not companies_file.exists():
        raise FileNotFoundError(f"Companies file not found: {companies_file}")

    try:
        with open(companies_file, encoding="utf-8") as f:
            companies_data = json.load(f)

        companies = []
        for company_dict in companies_data:
            try:
                company = CompanyData(**company_dict)
                companies.append(company)
            except Exception as e:
                print(
                    f"⚠️ Skipping invalid company data: {company_dict.get('name', 'unknown')} - {e}"
                )

        return companies

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in companies file: {e}") from e
    except Exception as e:
        raise ValueError(f"Error loading companies file: {e}") from e


def create_flow_run_name(prefix: str = "stage-1") -> str:
    """
    Create a unique flow run name with timestamp.

    Args:
        prefix: Prefix for the flow run name

    Returns:
        Formatted flow run name
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{timestamp}"


def validate_flow_inputs(
    companies: list[CompanyData],
    config: PipelineConfig,
    prompt_template_path: str,
) -> None:
    """
    Validate inputs before starting flow execution.

    Args:
        companies: List of companies to validate
        config: Pipeline configuration to validate
        prompt_template_path: Prompt template path to validate

    Raises:
        ValueError: If any input is invalid
    """
    # Validate companies
    if not companies:
        raise ValueError("No companies provided")

    enabled_count = len([c for c in companies if c.enabled])
    if enabled_count == 0:
        raise ValueError("No enabled companies found")

    # Validate config
    if not config.openai.api_key:
        raise ValueError("OpenAI API key not configured")

    if not config.stage_1.output_dir:
        raise ValueError("Output directory not configured")

    # Validate prompt template
    prompt_path = Path(prompt_template_path)
    if not prompt_path.exists():
        raise ValueError(f"Prompt template file not found: {prompt_template_path}")

    if not prompt_path.is_file():
        raise ValueError(f"Prompt template path is not a file: {prompt_template_path}")


def estimate_flow_duration(
    companies: list[CompanyData],
    max_concurrent: int = 3,
    avg_processing_time: float = 60.0,
) -> dict[str, Any]:
    """
    Estimate flow execution duration based on company count and concurrency.

    Args:
        companies: List of companies to process
        max_concurrent: Maximum concurrent companies
        avg_processing_time: Average processing time per company in seconds

    Returns:
        Dictionary with duration estimates
    """
    enabled_companies = [c for c in companies if c.enabled]
    total_companies = len(enabled_companies)

    if total_companies == 0:
        return {
            "total_companies": 0,
            "estimated_duration_seconds": 0,
            "estimated_duration_minutes": 0,
            "batches": 0,
        }

    # Calculate batches and duration
    batches = (
        total_companies + max_concurrent - 1
    ) // max_concurrent  # Ceiling division
    estimated_seconds = batches * avg_processing_time
    estimated_minutes = estimated_seconds / 60

    return {
        "total_companies": total_companies,
        "max_concurrent": max_concurrent,
        "estimated_duration_seconds": estimated_seconds,
        "estimated_duration_minutes": estimated_minutes,
        "batches": batches,
        "avg_processing_time": avg_processing_time,
    }


def create_flow_summary_report(results: dict[str, Any]) -> str:
    """
    Create a human-readable summary report from flow results.

    Args:
        results: Flow execution results

    Returns:
        Formatted summary report string
    """
    report_lines = [
        "=" * 60,
        "🚀 STAGE 1 FLOW EXECUTION SUMMARY",
        "=" * 60,
        f"📊 Total Companies: {results.get('total_companies', 0)}",
        f"✅ Successful: {results.get('successful_companies', 0)}",
        f"❌ Failed: {results.get('failed_companies', 0)}",
        f"📈 Success Rate: {results.get('success_rate', 0):.1%}",
        "",
        f"📋 Jobs Found: {results.get('total_jobs_found', 0)}",
        f"💾 Jobs Saved: {results.get('total_jobs_saved', 0)}",
        f"⏱️ Total Processing Time: {results.get('total_processing_time', 0):.2f}s",
        f"⚡ Average Processing Time: {results.get('average_processing_time', 0):.2f}s",
        "",
    ]

    # Add failure details if any
    if results.get("failed_companies", 0) > 0:
        report_lines.extend(
            [
                "❌ FAILURE DETAILS:",
                f"🔄 Retryable Failures: {results.get('retryable_failures', 0)}",
                f"🚫 Non-retryable Failures: {results.get('non_retryable_failures', 0)}",
                "",
            ]
        )

        # Add individual failure details
        detailed_results = results.get("detailed_results", [])
        failed_results = [r for r in detailed_results if not r.get("success", False)]

        if failed_results:
            report_lines.append("Failed Companies:")
            for result in failed_results[:10]:  # Limit to first 10 failures
                company_name = result.get("company_name", "unknown")
                error = result.get("error", "unknown error")
                retryable = result.get("retryable", True)
                retry_indicator = "🔄" if retryable else "🚫"
                report_lines.append(f"  {retry_indicator} {company_name}: {error}")

            if len(failed_results) > 10:
                report_lines.append(
                    f"  ... and {len(failed_results) - 10} more failures"
                )

            report_lines.append("")

    report_lines.append("=" * 60)

    return "\n".join(report_lines)
