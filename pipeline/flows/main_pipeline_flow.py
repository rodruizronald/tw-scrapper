from prefect import flow, get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData
from pipeline.flows.stage_1_flow import stage_1_flow


@flow(
    name="Main Job Processing Pipeline",
    description="Complete end-to-end job processing pipeline (all stages)",
    version="1.0.0",
    retries=0,  # No retries at pipeline level - let individual stages handle retries
    timeout_seconds=3600,  # 1 hour total pipeline timeout
)
async def main_pipeline_flow(
    companies: list[CompanyData],
    config: PipelineConfig,
) -> None:
    """
    Main pipeline flow that orchestrates all stages of job processing.

    This flow runs the complete pipeline from job extraction to final analysis:
    - Stage 1: Extract job listings from company career pages
    - Stage 2: Extract detailed job descriptions
    - Stage 3: Extract skills and responsibilities
    - Stage 4: Extract technologies and tools

    Args:
        companies: List of companies to process
        config: Pipeline configuration
        stages_to_run: List of stage names to execute

    Returns:
        Complete pipeline execution results
    """
    logger = get_run_logger()

    logger.info("🚀 Starting Main Job Processing Pipeline")
    logger.info(f"📋 Companies to process: {len(companies)}")
    logger.info("=" * 60)

    try:
        # Execute stages
        await _execute_stages(
            config,
            companies,
            logger,
        )
    except Exception:
        # Pipeline-level failure
        raise


async def _execute_stages(
    config: PipelineConfig,
    companies: list[CompanyData],
    logger,
) -> None:
    """Execute all requested pipeline stages."""

    # Stage 1: Job Listing Extraction
    if config.stage_1.enabled:
        await _execute_stage_1(
            config,
            companies,
            logger,
        )


async def _execute_stage_1(
    config: PipelineConfig,
    companies: list[CompanyData],
    logger,
) -> None:
    """Execute Stage 1: Job Listing Extraction."""
    logger.info("\n🏭 STAGE 1: Job Listing Extraction")
    logger.info("-" * 40)

    try:
        await stage_1_flow(
            companies=companies,
            config=config,
        )

    except Exception as e:
        logger.error(f"❌ Stage 1 failed: {e}")

        logger.error("🛑 Critical failure in Stage 1 - stopping pipeline")
        raise
