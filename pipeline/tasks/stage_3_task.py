from typing import Any

from prefect import task
from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import JobData, ProcessingResult
from pipeline.stages.stage_3 import Stage3Processor
from pipeline.utils.exceptions import (
    FileOperationError,
    OpenAIProcessingError,
    ValidationError,
    WebExtractionError,
)


def company_task_run_name(parameters: dict[str, Any]) -> str:
    """Generate a clean task run name from company data."""
    try:
        company_name = parameters.get("company_name")
        if company_name:
            company_slug = company_name.lower().replace(" ", "-")
            return f"{company_slug[:30]}"
    except Exception:
        pass
    return "company-extraction"


@task(
    name="Process Job Skills",
    description="Extract skills and responsibilities from a single job posting",
    tags=["stage-3", "job-processing"],
    retries=2,
    retry_delay_seconds=30,
    timeout_seconds=180,  # 3 minutes per job
    task_run_name=company_task_run_name,  # type: ignore[arg-type]
)
async def process_job_skills_task(
    company_name: str,
    jobs_data: list[JobData],
    config: PipelineConfig,
) -> ProcessingResult:
    """
    Prefect task to process a single job for skills and responsibilities extraction.

    Args:
        job_data: Job data from Stage 2 containing:
            - title: Job title
            - url: Job posting URL
            - signature: Job signature for deduplication
        company_config: Company configuration containing selectors
        config: Pipeline configuration

    Returns:
        Dictionary containing:
            - success: bool
            - job_data: Enhanced job data (if successful)
            - error: Error message (if failed)
            - company_name: Company name
            - job_title: Job title
            - processing_time: Time taken to process
    """
    logger = get_run_logger()
    logger.info("-" * 80)

    try:
        logger.info(f"Starting task for company: {company_name}")
        logger.info(f"Processing {len(jobs_data)} jobs")

        # Initialize processor
        processor = Stage3Processor(config)

        # Process each job individually
        for job_data in jobs_data:
            result = await processor.process_single_job(job_data)

        # Return as dict format expected by the function signature
        return result

    except ValidationError as e:
        # Non-retryable errors - don't retry these
        logger.error(f"Validation error for {company_name}: {e}")

        # Create failed result
        failed_result = ProcessingResult(
            success=False,
            company_name=company_name,
            error=str(e),
            error_type="ValidationError",
            retryable=False,
            stage="stage_3",
        )

        return failed_result

    except (WebExtractionError, OpenAIProcessingError, FileOperationError) as e:
        # Retryable errors - let Prefect handle retries
        logger.warning(f"Retryable error for {company_name}: {e}")
        # Re-raise to trigger Prefect retry mechanism
        raise

    except Exception as e:
        # Unexpected errors - log and re-raise for retry
        logger.error(f"Unexpected error for {company_name}: {e}")
        # Re-raise to trigger Prefect retry mechanism
        raise
