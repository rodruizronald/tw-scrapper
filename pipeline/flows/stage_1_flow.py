from prefect import flow, get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData
from pipeline.tasks.company_processing import (
    process_company_task,
)
from pipeline.tasks.utils import (
    filter_enabled_companies,
)


async def _process_companies(
    companies: list[CompanyData],
    config: PipelineConfig,
) -> None:
    """Process validated companies sequentially."""
    logger = get_run_logger()

    logger.info(f"🏭 Step 2: Processing {len(companies)} companies sequentially...")

    for company in companies:
        try:
            # Submit Prefect task and await its result (sequential)
            future = process_company_task.submit(company, config)
            # Wait for the future to complete and get the actual result
            result = await future.result()

            # Now check if the result has a success attribute
            if hasattr(result, "success") and result.success:
                logger.info(f"✅ Completed: {company.name}")
            else:
                logger.warning(f"❌ Failed: {company.name}")
        except Exception as e:
            logger.error(f"💥 Unexpected task failure: {company.name} - {e}")


@flow(
    name="Stage 1: Job Extraction Pipeline",
    description="Extract job listings from company career pages with concurrent processing",
    version="1.0.0",
    retries=1,
    retry_delay_seconds=60,
)
async def stage_1_flow(
    companies: list[CompanyData],
    config: PipelineConfig,
) -> None:
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

    logger.info(f"🚀 Starting Stage 1 flow with {len(companies)} companies")

    # Filter enabled companies
    enabled_companies = filter_enabled_companies(companies)

    if not enabled_companies:
        logger.warning("⚠️ No enabled companies found to process")
        return None

    logger.info(f"📋 Processing {len(enabled_companies)} enabled companies")

    await _process_companies(
        enabled_companies,
        config,
    )
