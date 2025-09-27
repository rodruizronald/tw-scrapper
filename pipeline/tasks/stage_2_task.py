from prefect import task
from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, Job, JobData, ProcessingResult
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
    timeout_seconds=180,  # 3 minutes per job
    task_run_name=company_task_run_name,  # type: ignore[arg-type]
)
async def process_job_details_task(
    company: CompanyData,
    jobs_data: list[JobData],
    config: PipelineConfig,
) -> ProcessingResult:
    """
    Prefect task to process a single job for eligibility analysis.

    Args:
        job_data: Job data from Stage 1 containing:
            - title: Job title
            - url: Job posting URL
            - signature: Job signature for deduplication
        company_config: Company configuration containing selectors
        config: Pipeline configuration

    Returns:
        Dictionary containing:
            - success: bool
            - job_data: Enhanced job data (if eligible and successful)
            - error: Error message (if failed)
            - company_name: Company name
            - job_title: Job title
            - processing_time: Time taken to process
    """
    logger = get_run_logger()
    logger.info("-" * 80)

    try:
        logger.info(f"Starting task for company: {company.name}")
        logger.info(f"Processing {len(jobs_data)} jobs")

        # Initialize processor
        processor = Stage2Processor(config, company.web_parser_config)
        empty_job_list: list[Job] = []

        result = await processor.process_jobs(empty_job_list, company.name)

        # Return as dict format expected by the function signature
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
