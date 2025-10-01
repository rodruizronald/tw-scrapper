from prefect import flow, get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData
from pipeline.services.file_service import FileService
from pipeline.tasks.stage_4_task import process_job_technologies_task
from pipeline.tasks.utils import (
    filter_enabled_companies,
)


@flow(
    name="stage_4_technologies_extraction",
    description="Extract technologies and tools from job postings",
    version="1.0.0",
    retries=1,
    retry_delay_seconds=60,
)
async def stage_4_flow(
    companies: list[CompanyData],
    config: PipelineConfig,
) -> None:
    """
    Main flow for Stage 4: Extract technologies and tools from job postings.

    This flow orchestrates the processing of multiple companies concurrently,
    with proper error handling, validation, and result aggregation.

    Args:
        companies: List of companies to process
        config: Pipeline configuration
    """
    logger = get_run_logger()
    logger.info("STAGE 4: Technologies and Tools Extraction")

    file_service = FileService(config.paths)

    # Filter enabled companies
    enabled_companies = filter_enabled_companies(companies)

    if not enabled_companies:
        logger.warning("No enabled companies found to process")
        return None

    logger.info(f"Processing {len(enabled_companies)} enabled companies")

    for company in enabled_companies:
        try:
            # Load jobs found in stage 3
            jobs_data = file_service.load_stage_results(
                company.name, config.stage_3.tag
            )
            if not jobs_data:
                logger.debug(f"No jobs data found for {company.name}")
                continue

            # Submit Prefect task and await its result (sequential)
            future = process_job_technologies_task.submit(company, jobs_data, config)

            # Wait for the future to complete and get the actual result
            await future.result()
            logger.info(f"Completed: {company.name}")
        except Exception as e:
            logger.error(f"Unexpected task failure: {company.name} - {e}")
