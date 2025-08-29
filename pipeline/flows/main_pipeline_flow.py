from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
    stages_to_run: list[str],
    prompt_templates: dict[str, str],
    max_concurrent_companies: int = 3,
) -> dict[str, Any]:
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
        stages_to_run: List of stage names to execute (defaults to all stages)
        max_concurrent_companies: Maximum concurrent companies for Stage 1
        prompt_templates: Dictionary mapping stage names to prompt template paths

    Returns:
        Complete pipeline execution results
    """
    logger = get_run_logger()

    # Initialize pipeline execution tracking
    pipeline_start_time = datetime.now(UTC)
    pipeline_results = _initialize_pipeline_results(
        pipeline_start_time, stages_to_run, companies
    )

    logger.info("🚀 Starting Main Job Processing Pipeline")
    logger.info(f"📋 Companies to process: {len(companies)}")
    logger.info(f"🎯 Stages to run: {', '.join(stages_to_run)}")
    logger.info("=" * 60)

    try:
        # Validate pipeline inputs
        logger.info("🔍 Validating pipeline inputs...")
        _validate_pipeline_inputs(companies, config, stages_to_run, prompt_templates)
        logger.info("✅ Pipeline input validation passed")

        # Initialize stage data - this will be passed between stages
        stage_data = {"companies": companies, "config": config}

        # Execute stages
        await _execute_stages(
            stages_to_run,
            pipeline_results,
            stage_data,
            config,
            companies,
            prompt_templates,
            max_concurrent_companies,
            logger,
        )

        # Pipeline completion
        _finalize_pipeline_results(pipeline_results, pipeline_start_time)
        _log_pipeline_summary(pipeline_results, logger)

        return pipeline_results

    except Exception as e:
        # Pipeline-level failure
        _handle_pipeline_failure(pipeline_results, pipeline_start_time, e, logger)
        raise


def _validate_pipeline_inputs(
    companies: list[CompanyData],
    config: PipelineConfig,
    stages_to_run: list[str],
    prompt_templates: dict[str, str],
) -> None:
    """Validate all pipeline inputs."""
    # Validate configuration
    config.validate()

    # Validate basic inputs
    if not companies:
        raise ValueError("No companies provided")

    enabled_count = len([c for c in companies if c.enabled])
    if enabled_count == 0:
        raise ValueError("No enabled companies found")

    # Validate stages
    valid_stages = ["stage_1", "stage_2", "stage_3", "stage_4"]
    invalid_stages = [s for s in stages_to_run if s not in valid_stages]
    if invalid_stages:
        raise ValueError(
            f"Invalid stages: {invalid_stages}. Valid stages: {valid_stages}"
        )

    # Validate prompt templates for requested stages
    if prompt_templates:
        for stage in stages_to_run:
            if stage in prompt_templates:
                template_path = Path(prompt_templates[stage])
                if not template_path.exists():
                    raise ValueError(
                        f"Prompt template not found for {stage}: {template_path}"
                    )


def _log_pipeline_summary(results: dict[str, Any], logger) -> None:
    """Log a comprehensive pipeline execution summary."""

    logger.info("\n" + "=" * 60)
    logger.info("🎉 MAIN PIPELINE EXECUTION SUMMARY")
    logger.info("=" * 60)

    # Basic stats
    logger.info(f"📊 Total Companies: {results.get('total_companies', 0)}")
    logger.info(
        f"🎯 Stages Requested: {', '.join(results.get('stages_requested', []))}"
    )
    logger.info(
        f"✅ Stages Completed: {', '.join(results.get('stages_completed', []))}"
    )
    logger.info(f"❌ Stages Failed: {', '.join(results.get('stages_failed', []))}")
    logger.info(f"⏱️ Total Duration: {results.get('pipeline_duration_seconds', 0):.2f}s")
    logger.info(f"🏆 Pipeline Success: {results.get('pipeline_success', False)}")

    # Stage-specific results
    stage_results = results.get("stage_results", {})
    if stage_results:
        logger.info("\n📋 STAGE DETAILS:")
        for stage_name, stage_result in stage_results.items():
            if stage_result.get("success", False):
                logger.info(f"  ✅ {stage_name.upper()}: Success")
                if "total_jobs_found" in stage_result:
                    logger.info(
                        f"     📋 Jobs found: {stage_result['total_jobs_found']}"
                    )
                if "total_jobs_saved" in stage_result:
                    logger.info(
                        f"     💾 Jobs saved: {stage_result['total_jobs_saved']}"
                    )
            else:
                error = stage_result.get("error", "Unknown error")
                logger.info(f"  ❌ {stage_name.upper()}: Failed - {error}")

    logger.info("=" * 60)


def _initialize_pipeline_results(
    start_time: datetime, stages_to_run: list[str], companies: list[CompanyData]
) -> dict[str, Any]:
    """Initialize pipeline results tracking dictionary."""
    return {
        "pipeline_start_time": start_time.isoformat(),
        "stages_requested": stages_to_run,
        "stages_completed": [],
        "stages_failed": [],
        "total_companies": len(companies),
        "stage_results": {},
        "pipeline_success": False,
    }


async def _execute_stages(
    stages_to_run: list[str],
    pipeline_results: dict[str, Any],
    stage_data: dict[str, Any],
    config: PipelineConfig,
    companies: list[CompanyData],
    prompt_templates: dict[str, str],
    max_concurrent_companies: int,
    logger,
) -> None:
    """Execute all requested pipeline stages."""

    # Stage 1: Job Listing Extraction
    if "stage_1" in stages_to_run:
        await _execute_stage_1(
            pipeline_results,
            stage_data,
            config,
            companies,
            prompt_templates,
            max_concurrent_companies,
            logger,
        )

    # Stage 2: Job Description Extraction (Future Implementation)
    if "stage_2" in stages_to_run:
        _execute_unimplemented_stage(
            "stage_2", "Job Description Extraction", pipeline_results, logger
        )

    # Stage 3: Skills and Responsibilities Extraction (Future Implementation)
    if "stage_3" in stages_to_run:
        _execute_unimplemented_stage(
            "stage_3",
            "Skills and Responsibilities Extraction",
            pipeline_results,
            logger,
        )

    # Stage 4: Technology Extraction (Future Implementation)
    if "stage_4" in stages_to_run:
        _execute_unimplemented_stage(
            "stage_4", "Technology Extraction", pipeline_results, logger
        )


async def _execute_stage_1(
    pipeline_results: dict[str, Any],
    stage_data: dict[str, Any],
    config: PipelineConfig,
    companies: list[CompanyData],
    prompt_templates: dict[str, str],
    max_concurrent_companies: int,
    logger,
) -> None:
    """Execute Stage 1: Job Listing Extraction."""
    logger.info("\n🏭 STAGE 1: Job Listing Extraction")
    logger.info("-" * 40)

    try:
        prompt_template_path = prompt_templates.get("stage_1")
        if prompt_template_path is None:
            raise ValueError("Stage 1 prompt template not found in prompt_templates")

        stage_1_results = await stage_1_flow(
            companies=companies,
            config=config,
            prompt_template_path=prompt_template_path,
            max_concurrent_companies=max_concurrent_companies,
        )

        pipeline_results["stage_results"]["stage_1"] = stage_1_results
        pipeline_results["stages_completed"].append("stage_1")
        stage_data["stage_1_results"] = stage_1_results

        logger.info("✅ Stage 1 completed successfully")
        logger.info(f"📊 Jobs found: {stage_1_results.get('total_jobs_found', 0)}")
        logger.info(f"💾 Jobs saved: {stage_1_results.get('total_jobs_saved', 0)}")

        if stage_1_results.get("total_jobs_saved", 0) == 0:
            logger.warning(
                "⚠️ No jobs were saved in Stage 1 - pipeline may not be effective"
            )

    except Exception as e:
        logger.error(f"❌ Stage 1 failed: {e}")
        pipeline_results["stages_failed"].append("stage_1")
        pipeline_results["stage_results"]["stage_1"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }

        logger.error("🛑 Critical failure in Stage 1 - stopping pipeline")
        raise


def _execute_unimplemented_stage(
    stage_name: str, stage_description: str, pipeline_results: dict[str, Any], logger
) -> None:
    """Execute placeholder for unimplemented stages."""
    logger.info(f"\n🔧 STAGE {stage_name.upper()}: {stage_description}")
    logger.info("-" * 40)
    logger.warning(f"⚠️ {stage_name.capitalize()} not yet implemented - skipping")

    pipeline_results["stages_failed"].append(stage_name)
    pipeline_results["stage_results"][stage_name] = {
        "success": False,
        "error": f"{stage_name.capitalize()} not yet implemented",
        "error_type": "NotImplementedError",
    }


def _finalize_pipeline_results(
    pipeline_results: dict[str, Any], start_time: datetime
) -> None:
    """Finalize pipeline results with completion data."""
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    pipeline_results.update(
        {
            "pipeline_end_time": end_time.isoformat(),
            "pipeline_duration_seconds": duration,
            "pipeline_success": len(pipeline_results["stages_failed"]) == 0,
        }
    )


def _handle_pipeline_failure(
    pipeline_results: dict[str, Any], start_time: datetime, error: Exception, logger
) -> None:
    """Handle pipeline-level failures."""
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    pipeline_results.update(
        {
            "pipeline_end_time": end_time.isoformat(),
            "pipeline_duration_seconds": duration,
            "pipeline_success": False,
            "pipeline_error": str(error),
            "pipeline_error_type": type(error).__name__,
        }
    )

    logger.error(f"💥 Pipeline failed: {error}")
    _log_pipeline_summary(pipeline_results, logger)
