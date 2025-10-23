from prefect import task
from prefect.logging import get_run_logger

from core.models.jobs import CompanyData, Job
from pipeline.config import PipelineConfig
from pipeline.stages.stage_4 import Stage4Processor
from pipeline.tasks.utils import company_task_run_name
from utils.exceptions import (
    FileOperationError,
    OpenAIProcessingError,
    ValidationError,
    WebExtractionError,
)


@task(
    name="Process Job Technologies",
    description="Extract technologies and tools from a single job posting",
    retries=0,
    retry_delay_seconds=30,
    timeout_seconds=None,
    task_run_name=company_task_run_name,  # type: ignore[arg-type]
)
async def process_job_technologies_task(
    company: CompanyData,
    jobs: list[Job],
    config: PipelineConfig,
) -> list[Job]:
    """
    Prefect task to process a single job for technologies and tools extraction.

    Args:
        job_data: Job data from Stage 3 containing:
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

    try:
        logger.info(f"Starting task for company: {company.name}")

        # Initialize processor
        processor = Stage4Processor(config, company.web_parser_config)

        # Process each job individually
        results: list[Job] = await processor.process_jobs(jobs, company.name)

        return results

    except ValidationError as e:
        # Non-retryable errors - don't retry these
        logger.error(f"Validation error for {company.name}: {e}")
        return []  # Return empty list instead of None

    except (WebExtractionError, OpenAIProcessingError, FileOperationError) as e:
        # Retryable errors - let Prefect handle retries
        logger.warning(f"Retryable error for {company.name}: {e}")
        # Re-raise to trigger Prefect retry mechanism
        raise

    except Exception as e:
        # Unexpected errors - log and re-raise for retry
        logger.error(f"Unexpected error for {company.name}: {e}")
        # Re-raise to trigger Prefect retry mechanism
        raise
