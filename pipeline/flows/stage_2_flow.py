from prefect import flow, get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData
from pipeline.services.file_service import FileService
from pipeline.tasks.stage_2_task import process_job_details_task
from pipeline.tasks.utils import (
    filter_enabled_companies,
)


@flow(
    name="stage_2_job_details_extraction",
    description="Extract job eligibility, metadata, and detailed descriptions from individual job postings",
    version="1.0.0",
    retries=1,
    retry_delay_seconds=60,
)
async def stage_2_flow(
    companies: list[CompanyData],
    config: PipelineConfig,
) -> None:
    """
    Main flow for Stage 2: Extract job eligibility, metadata, and detailed descriptions from individual job postings.

    This flow orchestrates the processing of multiple companies concurrently,
    with proper error handling, validation, and result aggregation.

    Args:
        companies: List of companies to process
        config: Pipeline configuration
    """
    logger = get_run_logger()

    logger.info("STAGE 2: Job Details Extraction")
    file_service = FileService(config.paths)

    # Filter enabled companies
    enabled_companies = filter_enabled_companies(companies)

    if not enabled_companies:
        logger.warning("No enabled companies found to process")
        return None

    logger.info(f"Processing {len(enabled_companies)} enabled companies")

    for company in enabled_companies:
        try:
            # Load jobs found in stage 1
            jobs_data = file_service.load_stage_results(
                company.name, config.stage_1.tag
            )
            if not jobs_data:
                logger.debug(f"No jobs data found for {company.name}")
                continue

            # Submit Prefect task and await its result (sequential)
            future = process_job_details_task.submit(company, jobs_data, config)
            # Wait for the future to complete and get the actual result
            result = future.result()

            # Now check if the result has a success attribute
            if hasattr(result, "success") and result.success:
                logger.info(f"Completed: {company.name}")
            else:
                logger.warning(f"Failed: {company.name}")
        except Exception as e:
            logger.error(f"Unexpected task failure: {company.name} - {e}")
