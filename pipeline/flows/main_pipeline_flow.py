from prefect import flow, get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData
from pipeline.flows.stage_1_flow import stage_1_flow
from pipeline.flows.stage_2_flow import stage_2_flow
from pipeline.flows.stage_3_flow import stage_3_flow
from pipeline.flows.stage_4_flow import stage_4_flow
from pipeline.flows.utils import (
    load_companies_from_file,
    validate_flow_inputs,
)


@flow(
    name="job_processing_pipeline",
    description="Complete end-to-end job processing pipeline",
    version="1.0.0",
    retries=0,  # No retries at pipeline level - let individual stages handle retries
    timeout_seconds=3600,  # 1 hour total pipeline timeout
)
async def main_pipeline_flow() -> None:
    """
    Main pipeline flow that orchestrates all stages of job processing.

    This flow runs the complete pipeline from job extraction to final analysis:
    - Stage 1: Extract job listings from company career pages
    - Stage 2: Extract detailed job descriptions
    - Stage 3: Extract skills and responsibilities
    - Stage 4: Extract technologies and tools

    Returns:
        Complete pipeline execution results
    """
    logger = get_run_logger()
    logger.info("Starting Job Processing Pipeline")

    try:
        # Load configuration
        config = PipelineConfig.load()
        logger.info("Configuration loaded")

        # Initialize paths
        config.initialize_paths()
        logger.info("Paths initialized")

        # Load companies
        companies = load_companies_from_file(config.companies_file_path, logger)
        logger.info(f"Loaded {len(companies)} companies")

        # Parse stages
        stages_to_run = config.stages.get_enabled_stage_tags()
        logger.info(f"Stages to run: {', '.join(stages_to_run)}")

        validate_flow_inputs(companies, config)
        logger.info("Input validation passed")

        # Run pipeline
        logger.info("Starting pipeline execution...")

        # Execute stages
        await _execute_stages(
            config,
            companies,
            logger,
        )

        logger.info("Pipeline execution completed!")
    except Exception as e:
        # Pipeline-level failure
        logger.error(f"Pipeline failed: {e}")
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

    # Stage 2: Job Listing Extraction
    if config.stage_2.enabled:
        await _execute_stage_2(
            config,
            companies,
            logger,
        )

    # Stage 3: Skills and Responsibilities Extraction
    if config.stage_3.enabled:
        await _execute_stage_3(
            config,
            companies,
            logger,
        )

    # Stage 4: Technologies and Tools Extraction
    if config.stage_4.enabled:
        await _execute_stage_4(
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
    logger.info("STAGE 1: Job Listing Extraction")
    logger.info("=" * 80)

    try:
        await stage_1_flow(
            companies=companies,
            config=config,
        )

    except Exception as e:
        logger.error(f"Stage 1 failed: {e}")

        logger.error("Critical failure in Stage 1 - stopping pipeline")
        raise


async def _execute_stage_2(
    config: PipelineConfig,
    companies: list[CompanyData],
    logger,
) -> None:
    """Execute Stage 2: Job Details Extraction."""
    logger.info("=" * 80)

    try:
        await stage_2_flow(
            companies=companies,
            config=config,
        )

    except Exception as e:
        logger.error(f"Stage 2 failed: {e}")

        logger.error("Critical failure in Stage 2 - stopping pipeline")
        raise


async def _execute_stage_3(
    config: PipelineConfig,
    companies: list[CompanyData],
    logger,
) -> None:
    """Execute Stage 3: Skills and Responsibilities Extraction."""
    logger.info("STAGE 3: Skills and Responsibilities Extraction")
    logger.info("=" * 80)

    try:
        await stage_3_flow(
            companies=companies,
            config=config,
        )

    except Exception as e:
        logger.error(f"Stage 3 failed: {e}")

        logger.error("Critical failure in Stage 3 - stopping pipeline")
        raise


async def _execute_stage_4(
    config: PipelineConfig,
    companies: list[CompanyData],
    logger,
) -> None:
    """Execute Stage 4: Technologies and Tools Extraction."""
    logger.info("STAGE 4: Technologies and Tools Extraction")
    logger.info("=" * 80)

    try:
        await stage_4_flow(
            companies=companies,
            config=config,
        )

    except Exception as e:
        logger.error(f"Stage 4 failed: {e}")

        logger.error("Critical failure in Stage 4 - stopping pipeline")
        raise
