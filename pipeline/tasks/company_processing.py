from datetime import UTC, datetime

from prefect import task
from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, ProcessingResult
from pipeline.stages.stage_1 import Stage1Processor
from pipeline.utils.exceptions import (
    FileOperationError,
    OpenAIProcessingError,
    ValidationError,
    WebExtractionError,
)


@task(
    name="Process Company",
    description="Extract job listings from a single company's career page",
    tags=["stage-1", "company-processing"],
    retries=2,
    retry_delay_seconds=30,
    timeout_seconds=300,  # 5 minutes per company
)
async def process_company_task(
    company: CompanyData,
    config: PipelineConfig,
) -> ProcessingResult:
    """
    Prefect task to process a single company for job listings.

    Args:
        company_data: Dictionary representation of CompanyData
        config: Dictionary representation of PipelineConfig

    Returns:
        Dictionary representation of ProcessingResult

    Raises:
        ValidationError: For non-retryable validation errors
        Exception: For retryable errors (network, API, file operations)
    """
    logger = get_run_logger()

    try:
        logger.info(f"Starting task for company: {company.name}")

        timestamp = datetime.now(UTC).astimezone().strftime("%Y%m%d")

        # Initialize processor
        processor = Stage1Processor(config, timestamp)

        # Process the company
        result = await processor.process_single_company(company)

        # Log result summary
        if result.success:
            logger.info(
                f"{company.name}: Successfully processed "
                f"({result.jobs_found} found, {result.jobs_saved} saved) "
                f"in {result.processing_time:.2f}s"
            )
        else:
            logger.error(f"{company.name}: Processing failed - {result.error}")

        return result

    except ValidationError as e:
        # Non-retryable errors - don't retry these
        logger.error(f"Validation error for {company.name}: {e}")

        # Create failed result
        failed_result = ProcessingResult(
            success=False,
            company_name=company.name,
            error=str(e),
            error_type="ValidationError",
            retryable=False,
            stage="stage_1",
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
