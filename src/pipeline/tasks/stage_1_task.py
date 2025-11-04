from prefect import task
from prefect.logging import get_run_logger

from core.models.jobs import CompanyData, Job
from pipeline.config import PipelineConfig
from pipeline.stages.stage_1 import Stage1Processor
from pipeline.tasks.helpers import company_task_run_name
from utils.exceptions import (
    FileOperationError,
    OpenAIProcessingError,
    ValidationError,
    WebExtractionError,
)


@task(
    name="Process Company",
    description="Extract job listings from a single company's career page",
    retries=0,
    retry_delay_seconds=30,
    timeout_seconds=None,
    task_run_name=company_task_run_name,  # type: ignore[arg-type]
)
async def process_job_listings_task(
    company: CompanyData,
    config: PipelineConfig,
) -> list[Job]:
    """
    Prefect task to process a single company for job listings.

    Args:
        company_data: Dictionary representation of CompanyData
        config: Dictionary representation of PipelineConfig

    Raises:
        ValidationError: For non-retryable validation errors
        Exception: For retryable errors (network, API, file operations)
    """
    logger = get_run_logger()

    try:
        logger.info(f"Starting task for company: {company.name}")

        # Initialize processor
        processor = Stage1Processor(config)

        # Process the company
        results: list[Job] = await processor.process_single_company(company)

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
