import asyncio

from prefect import flow, get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, Job
from pipeline.services.database_service import DatabaseService
from pipeline.tasks.stage_2_task import process_job_details_task
from pipeline.tasks.utils import (
    filter_enabled_companies,
)


@flow(
    name="stage_2_job_details_extraction",
    description="Extract job eligibility, metadata, and detailed descriptions from individual job postings",
    version="1.0.0",
    retries=0,
    retry_delay_seconds=60,
    timeout_seconds=None,
)
async def stage_2_flow(
    companies: list[CompanyData],
    config: PipelineConfig,
) -> dict[str, list[Job]]:
    """
    Main flow for Stage 2: Extract job eligibility, metadata, and detailed descriptions from individual job postings.

    This flow orchestrates the processing of multiple companies concurrently,
    with proper error handling, validation, and result aggregation.

    Args:
        companies: List of companies to process
        config: Pipeline configuration
        stage_1_results: Results from stage 1 or None to load from database
    """
    logger = get_run_logger()
    logger.info("Stage 2: Job Details Extraction")

    db_service = DatabaseService()

    # Filter enabled companies
    enabled_companies = filter_enabled_companies(companies)

    if not enabled_companies:
        logger.warning("No enabled companies found to process")
        return {}

    logger.info(f"Processing {len(enabled_companies)} enabled companies")

    async def process_with_semaphore(
        company: CompanyData, semaphore: asyncio.Semaphore
    ) -> tuple[str, list[Job]]:
        """Process a company with semaphore to limit concurrency."""
        async with semaphore:
            try:
                # Get jobs data from stage 1 results
                jobs_data = db_service.load_stage_results(
                    company.name, config.stage_1.tag
                )

                if not jobs_data:
                    logger.info(f"No jobs data found for {company.name}")
                    return company.name, []

                result = await process_job_details_task(company, jobs_data, config)
                logger.info(f"Completed: {company.name}")
                return company.name, result
            except Exception as e:
                logger.error(f"Unexpected task failure: {company.name} - {e}")
                return company.name, []

    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(3)

    # Create tasks for all companies
    tasks = [
        process_with_semaphore(company, semaphore) for company in enabled_companies
    ]

    # Run all tasks concurrently (limited by semaphore)
    results = await asyncio.gather(*tasks)

    # Build results map
    results_map = dict(results)

    return results_map
