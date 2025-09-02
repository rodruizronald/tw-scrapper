"""
Main entry point for the job processing pipeline using Prefect.

This module provides a command-line interface and programmatic API
for running the job processing pipeline with Prefect orchestration.
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger

from pipeline.core.config import PipelineConfig
from pipeline.flows.main_pipeline_flow import main_pipeline_flow
from pipeline.flows.utils import (
    create_flow_summary_report,
    load_companies_from_file,
    validate_flow_inputs,
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run():
    """Run the complete job processing pipeline."""

    async def _run_pipeline():
        try:
            stages = ["stage_1"]

            # Load configuration
            config = PipelineConfig.load()
            logger.info("✅ Configuration loaded")

            # Load companies
            companies_path = Path("companies_file")
            if not companies_path.is_absolute():
                companies_path = config.project_root / companies_path

            companies = load_companies_from_file(companies_path)
            logger.info(f"✅ Loaded {len(companies)} companies")

            # Parse stages
            stages_to_run = [s.strip() for s in stages.split(",")]
            logger.info(f"🎯 Stages to run: {', '.join(stages_to_run)}")

            # Validate inputs
            prompt_template_path = Path("prompt_template")
            if not prompt_template_path.is_absolute():
                prompt_template_path = config.project_root / prompt_template_path

            validate_flow_inputs(companies, config, str(prompt_template_path))
            logger.info("✅ Input validation passed")

            # Run pipeline
            logger.info("🚀 Starting pipeline execution...")

            # Use main pipeline flow
            prompt_templates = {
                "stage_1": str(prompt_template_path),
                # Add other stage templates as they become available
            }

            results = await main_pipeline_flow(
                companies=companies,
                config=config,
                stages_to_run=stages_to_run,
                prompt_templates=prompt_templates,
                max_concurrent_companies=3,
            )

            # Display results
            logger.info("🎉 Pipeline execution completed!")

            if "stage_1" in stages_to_run:
                # Show Stage 1 specific summary
                print("\n" + create_flow_summary_report(results))
            else:
                # Show general pipeline summary
                print("\n📊 Pipeline Results:")
                print(f"✅ Success: {results.get('pipeline_success', False)}")
                print(
                    f"📋 Stages completed: {', '.join(results.get('stages_completed', []))}"
                )
                print(
                    f"❌ Stages failed: {', '.join(results.get('stages_failed', []))}"
                )

            return results

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise

    # Run the async pipeline
    asyncio.run(_run_pipeline())


if __name__ == "__main__":
    run()
