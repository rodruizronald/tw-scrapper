"""
Main entry point for the job processing pipeline using Prefect.

This module provides a command-line interface and programmatic API
for running the job processing pipeline with Prefect orchestration.
"""

import asyncio
import sys
from pathlib import Path

import click
from loguru import logger

from pipeline.core.config import PipelineConfig
from pipeline.flows import (
    create_flow_summary_report,
    estimate_flow_duration,
    load_companies_from_file,
    main_pipeline_flow,
    quick_pipeline_flow,
    stage_1_flow,
    validate_flow_inputs,
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@click.group()
@click.option(
    "--log-level", default="INFO", help="Log level (DEBUG, INFO, WARNING, ERROR)"
)
@click.pass_context
def cli(ctx, log_level):
    """Job Processing Pipeline with Prefect orchestration."""

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level=log_level)

    # Store log level in context
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level


@cli.command()
@click.option(
    "--companies-file",
    "-c",
    default="input/companies.json",
    help="Path to companies JSON file",
)
@click.option(
    "--prompt-template",
    "-p",
    default="input/prompts/job_title_url_parser.md",
    help="Path to prompt template file",
)
@click.option(
    "--max-concurrent", "-m", default=3, help="Maximum concurrent companies to process"
)
@click.option(
    "--stages",
    default="stage_1",
    help="Comma-separated list of stages to run (e.g., stage_1,stage_2)",
)
def run(companies_file, prompt_template, max_concurrent, stages):
    """Run the complete job processing pipeline."""

    async def _run_pipeline():
        try:
            # Load configuration
            config = PipelineConfig.load_from_env()
            logger.info("✅ Configuration loaded")

            # Load companies
            companies_path = Path(companies_file)
            if not companies_path.is_absolute():
                companies_path = config.project_root / companies_path

            companies = load_companies_from_file(companies_path)
            logger.info(f"✅ Loaded {len(companies)} companies")

            # Parse stages
            stages_to_run = [s.strip() for s in stages.split(",")]
            logger.info(f"🎯 Stages to run: {', '.join(stages_to_run)}")

            # Validate inputs
            prompt_template_path = Path(prompt_template)
            if not prompt_template_path.is_absolute():
                prompt_template_path = config.project_root / prompt_template_path

            validate_flow_inputs(companies, config, str(prompt_template_path))
            logger.info("✅ Input validation passed")

            # Estimate duration
            duration_estimate = estimate_flow_duration(companies, max_concurrent)
            logger.info(
                f"⏱️ Estimated duration: {duration_estimate['estimated_duration_minutes']:.1f} minutes"
            )

            # Run pipeline
            logger.info("🚀 Starting pipeline execution...")

            if len(stages_to_run) == 1 and stages_to_run[0] == "stage_1":
                # Use optimized Stage 1 flow
                results = await stage_1_flow(
                    companies=companies,
                    config=config,
                    prompt_template_path=str(prompt_template_path),
                    max_concurrent_companies=max_concurrent,
                )
            else:
                # Use main pipeline flow
                prompt_templates = {
                    "stage_1": str(prompt_template_path),
                    # Add other stage templates as they become available
                }

                results = await main_pipeline_flow(
                    companies=companies,
                    config=config,
                    stages_to_run=stages_to_run,
                    max_concurrent_companies=max_concurrent,
                    prompt_templates=prompt_templates,
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


@cli.command()
@click.option(
    "--companies-file",
    "-c",
    default="input/companies.json",
    help="Path to companies JSON file",
)
@click.option(
    "--prompt-template",
    "-p",
    default="input/prompts/job_title_url_parser.md",
    help="Path to prompt template file",
)
@click.option(
    "--max-concurrent", "-m", default=3, help="Maximum concurrent companies to process"
)
def quick(companies_file, prompt_template, max_concurrent):
    """Quick job extraction (Stage 1 only) using simplified flow."""

    async def _run_quick():
        try:
            # Resolve paths
            config = PipelineConfig.load_from_env()

            companies_path = Path(companies_file)
            if not companies_path.is_absolute():
                companies_path = config.project_root / companies_path

            prompt_path = Path(prompt_template)
            if not prompt_path.is_absolute():
                prompt_path = config.project_root / prompt_path

            logger.info("⚡ Starting quick job extraction...")

            # Run quick pipeline
            results = await quick_pipeline_flow(
                companies_file=str(companies_path),
                prompt_template_path=str(prompt_path),
                max_concurrent_companies=max_concurrent,
            )

            # Extract Stage 1 results
            stage_1_results = results.get("stage_results", {}).get("stage_1", {})

            logger.info("🎉 Quick extraction completed!")
            print("\n" + create_flow_summary_report(stage_1_results))

            return results

        except Exception as e:
            logger.error(f"❌ Quick extraction failed: {e}")
            raise

    # Run the async pipeline
    asyncio.run(_run_quick())


@cli.command()
@click.option(
    "--companies-file",
    "-c",
    default="input/companies.json",
    help="Path to companies JSON file",
)
@click.option(
    "--max-concurrent", "-m", default=3, help="Maximum concurrent companies to process"
)
def estimate(companies_file, max_concurrent):
    """Estimate pipeline execution time and resource requirements."""

    try:
        # Load configuration and companies
        config = PipelineConfig.load_from_env()

        companies_path = Path(companies_file)
        if not companies_path.is_absolute():
            companies_path = config.project_root / companies_path

        companies = load_companies_from_file(companies_path)

        # Generate estimates
        duration_estimate = estimate_flow_duration(companies, max_concurrent)

        # Display estimates
        print("📊 PIPELINE EXECUTION ESTIMATES")
        print("=" * 40)
        print(f"📋 Total companies: {duration_estimate['total_companies']}")
        print(f"🏭 Max concurrent: {duration_estimate['max_concurrent']}")
        print(f"📦 Processing batches: {duration_estimate['batches']}")
        print(
            f"⏱️ Estimated duration: {duration_estimate['estimated_duration_minutes']:.1f} minutes"
        )
        print(
            f"⚡ Avg time per company: {duration_estimate['avg_processing_time']:.1f} seconds"
        )

        # Resource recommendations
        print("\n💡 RECOMMENDATIONS:")
        if duration_estimate["total_companies"] > 10:
            print("   Consider increasing concurrency for faster processing")
        if duration_estimate["estimated_duration_minutes"] > 30:
            print("   Long execution time - consider running in smaller batches")

    except Exception as e:
        logger.error(f"❌ Estimation failed: {e}")
        raise


if __name__ == "__main__":
    cli()
