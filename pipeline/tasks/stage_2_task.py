from prefect import task
from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, Job
from pipeline.stages.stage_2 import Stage2Processor
from pipeline.tasks.utils import company_task_run_name
from pipeline.utils.exceptions import (
    FileOperationError,
    OpenAIProcessingError,
    ValidationError,
    WebExtractionError,
)


@task(
    name="Process Job",
    description="Extract eligibility and metadata from a single job posting",
    tags=["stage-2", "job-processing"],
    retries=2,
    retry_delay_seconds=30,
    timeout_seconds=180,
    task_run_name=company_task_run_name,  # type: ignore[arg-type]
)
async def process_job_details_task(
    company: CompanyData,
    jobs: list[Job],
    config: PipelineConfig,
) -> None:
    """
    Prefect task to process jobs for eligibility analysis.

    Args:
        company: Company data containing configuration
        jobs: Job objects from Stage 1
        config: Pipeline configuration

    """
    logger = get_run_logger()

    try:
        logger.info(f"Starting task for company: {company.name}")

        # Initialize processor
        processor = Stage2Processor(config, company.web_parser_config)

        # Process all jobs for the company
        await processor.process_jobs(jobs, company.name)

    except ValidationError as e:
        # Non-retryable errors - don't retry these
        logger.error(f"Validation error for {company.name}: t{e}")

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
