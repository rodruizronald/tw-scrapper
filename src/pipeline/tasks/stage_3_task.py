from prefect import task
from prefect.logging import get_run_logger
from utils.exceptions import (
    FileOperationError,
    OpenAIProcessingError,
    ValidationError,
    WebExtractionError,
)

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, Job
from pipeline.stages.stage_3 import Stage3Processor
from pipeline.tasks.utils import company_task_run_name


@task(
    name="Process Job Skills",
    description="Extract skills and responsibilities from a single job posting",
    retries=0,
    retry_delay_seconds=30,
    timeout_seconds=None,
    task_run_name=company_task_run_name,  # type: ignore[arg-type]
)
async def process_job_skills_task(
    company: CompanyData,
    jobs: list[Job],
    config: PipelineConfig,
) -> list[Job]:
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

    try:
        logger.info(f"Starting task for company: {company.name}")

        # Initialize processor
        processor = Stage3Processor(config, company.web_parser_config)

        # Process all jobs for the company
        results = await processor.process_jobs(jobs, company.name)

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
