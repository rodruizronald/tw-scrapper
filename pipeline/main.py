"""
Main entry point for the job processing pipeline using Prefect.

This module provides a command-line interface and programmatic API
for running the job processing pipeline with Prefect orchestration.
"""

import asyncio
from datetime import UTC, datetime

from loguru import logger

from pipeline.core.config import PipelineConfig
from pipeline.flows import main_pipeline_flow
from pipeline.flows.utils import (
    load_companies_from_file,
    validate_flow_inputs,
)


def run():
    """Run the complete job processing pipeline."""

    async def _run_pipeline():
        try:
            # Create timestamp
            timestamp = datetime.now(UTC).strftime("%Y%m%d")

            # Load configuration
            config = PipelineConfig.load()
            config.setup_logging()
            logger.info("✅ Configuration loaded")

            # Initialize paths
            config.initialize_paths(timestamp)
            logger.info("✅ Paths initialized")

            # Load companies
            companies = load_companies_from_file(config.companies_file_path)
            logger.info(f"✅ Loaded {len(companies)} companies")

            # Parse stages
            stages_to_run = config.stages.get_enabled_stage_tags()
            logger.info(f"🎯 Stages to run: {', '.join(stages_to_run)}")

            validate_flow_inputs(companies, config)
            logger.info("✅ Input validation passed")

            # Run pipeline
            logger.info("🚀 Starting pipeline execution...")

            await main_pipeline_flow(
                companies=companies,
                config=config,
            )

            # Display results
            logger.info("🎉 Pipeline execution completed!")

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise

    # Run the async pipeline
    asyncio.run(_run_pipeline())


if __name__ == "__main__":
    run()
