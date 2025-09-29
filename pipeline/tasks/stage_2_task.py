from prefect import task
from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, Job, ProcessingResult
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
) -> ProcessingResult:
    """
    Prefect task to process jobs for eligibility analysis.

    Args:
        company: Company data containing configuration
        jobs: Job objects from Stage 1
        config: Pipeline configuration

    Returns:
        ProcessingResult with success status and processing info
    """
    logger = get_run_logger()
    logger.info("-" * 80)

    try:
        logger.info(f"Starting task for company: {company.name}")
        logger.info(f"Processing {len(jobs)} jobs")

        # No need to convert - jobs are already Job objects
        # Initialize processor
        processor = Stage2Processor(config, company.web_parser_config)

        # Process all jobs for the company
        result = await processor.process_jobs(jobs, company.name)

        return result

    except ValidationError as e:
        # Non-retryable errors - don't retry these
        logger.error(f"Validation error for {company.name}: t{e}")

        # Create failed result
        failed_result = ProcessingResult(
            success=False,
            company_name=company.name,
            error=str(e),
            error_type="ValidationError",
            retryable=False,
            stage="stage_2",
        )

        return failed_result

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
