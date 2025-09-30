from prefect import flow, get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, Job
from pipeline.tasks.stage_1_task import (
    process_job_listings_task,
)
from pipeline.tasks.utils import (
    filter_enabled_companies,
)


@flow(
    name="stage_1_job_listing_extraction",
    description="Extract job listings from company career pages with concurrent processing",
    version="1.0.0",
    retries=1,
    retry_delay_seconds=60,
)
async def stage_1_flow(
    companies: list[CompanyData],
    config: PipelineConfig,
) -> dict[str, list[Job]]:
    """
    Main flow for Stage 1: Extract job listings from company career pages.

    This flow orchestrates the processing of multiple companies concurrently,
    with proper error handling, validation, and result aggregation.

    Args:
        companies: List of companies to process
        config: Pipeline configuration

    Returns:
        Aggregated results from all company processing
    """
    logger = get_run_logger()

    logger.info(f"Starting Stage 1 flow with {len(companies)} companies")

    # Filter enabled companies
    enabled_companies = filter_enabled_companies(companies)

    if not enabled_companies:
        logger.warning("No enabled companies found to process")
        return {}

    logger.info(f"Processing {len(enabled_companies)} enabled companies")

    # Initialize results map
    results_map = {}

    for company in enabled_companies:
        try:
            # Submit Prefect task and await its result (sequential)
            future = process_job_listings_task.submit(company, config)
            # Wait for the future to complete and get the actual result
            result = await future.result()

            # Store result in the map
            results_map[company.name] = result

            logger.info(f"Completed: {company.name}")
        except Exception as e:
            logger.error(f"Unexpected task failure: {company.name} - {e}")
            # Store empty list for failed companies
            results_map[company.name] = []

    return results_map
