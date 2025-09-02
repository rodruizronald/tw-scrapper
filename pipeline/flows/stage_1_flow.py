import asyncio
from typing import Any

from prefect import flow, get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData
from pipeline.tasks.company_processing import (
    aggregate_results_task,
    process_company_task,
    validate_company_data_task,
)
from pipeline.tasks.utils import (
    filter_enabled_companies,
    prepare_company_data_for_task,
    prepare_config_for_task,
    save_task_results,
)


async def _validate_companies(
    enabled_companies: list[CompanyData],
) -> tuple[list[tuple[CompanyData, dict]], list[dict]]:
    """Validate all company data and return validated companies and failures."""
    logger = get_run_logger()

    logger.info("🔍 Step 1: Validating company data...")

    # In Prefect 3.x, call tasks directly within flows
    validated_companies = []
    validation_failures = []

    for company in enabled_companies:
        company_dict = prepare_company_data_for_task(company)
        try:
            validated_data = await validate_company_data_task(company_dict)
            validated_companies.append((company, validated_data))
            logger.debug(f"✅ Validation passed: {company.name}")
        except Exception as e:
            logger.warning(f"❌ Validation failed: {company.name} - {e}")
            validation_failures.append(
                {
                    "company_name": company.name,
                    "error": str(e),
                    "error_type": "ValidationError",
                    "retryable": False,
                    "success": False,
                    "stage": "validation",
                }
            )

    logger.info(
        f"✅ Validation complete: {len(validated_companies)} passed, {len(validation_failures)} failed"
    )

    return validated_companies, validation_failures


async def _process_companies_concurrently(
    validated_companies: list[tuple[CompanyData, dict]],
    config_dict: dict,
    prompt_template_path: str,
    max_concurrent_companies: int,
) -> list[dict]:
    """Process validated companies concurrently with semaphore control."""
    logger = get_run_logger()

    logger.info(
        f"🏭 Step 2: Processing {len(validated_companies)} companies concurrently..."
    )

    # Create processing tasks with concurrency control
    semaphore = asyncio.Semaphore(max_concurrent_companies)

    async def process_single_company(
        company_data_dict: dict[str, Any], company_name: str
    ):
        async with semaphore:
            try:
                result = await process_company_task(
                    company_data_dict, config_dict, prompt_template_path
                )
                if result.get("success", False):
                    logger.info(f"✅ Completed: {company_name}")
                else:
                    logger.warning(f"❌ Failed: {company_name}")
                return result
            except Exception as e:
                logger.error(f"💥 Unexpected task failure: {company_name} - {e}")
                return {
                    "success": False,
                    "company_name": company_name,
                    "error": f"Task execution failed: {e}",
                    "error_type": "TaskExecutionError",
                    "retryable": True,
                    "stage": "processing",
                }

    # Create tasks for all companies
    tasks = []
    for company, validated_data in validated_companies:
        task = process_single_company(validated_data, company.name)
        tasks.append(task)

    # Wait for all tasks to complete
    processing_results = await asyncio.gather(*tasks, return_exceptions=False)

    return processing_results


async def _save_results_if_configured(
    aggregated_results: dict,
    config: PipelineConfig,
) -> dict:
    """Save results to file if configured and update results with file path."""
    logger = get_run_logger()

    try:
        results_path = save_task_results(
            aggregated_results,
            config.stage_1_output_dir,
            "stage_1_flow_results.json",
        )
        logger.info(f"💾 Results saved to: {results_path}")
        aggregated_results["results_file_path"] = str(results_path)
    except Exception as e:
        logger.warning(f"⚠️ Failed to save results file: {e}")

    return aggregated_results


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
    prompt_template_path: str,
    max_concurrent_companies: int = 3,
) -> dict[str, Any]:
    """
    Main flow for Stage 1: Extract job listings from company career pages.

    This flow orchestrates the processing of multiple companies concurrently,
    with proper error handling, validation, and result aggregation.

    Args:
        companies: List of companies to process
        config: Pipeline configuration
        prompt_template_path: Path to OpenAI prompt template
        max_concurrent_companies: Maximum number of companies to process concurrently

    Returns:
        Aggregated results from all company processing
    """
    logger = get_run_logger()

    logger.info(f"🚀 Starting Stage 1 flow with {len(companies)} companies")
    logger.info(f"⚙️ Max concurrent companies: {max_concurrent_companies}")

    # Filter enabled companies
    enabled_companies = filter_enabled_companies(companies)

    if not enabled_companies:
        logger.warning("⚠️ No enabled companies found to process")
        return {
            "total_companies": 0,
            "successful_companies": 0,
            "failed_companies": 0,
            "total_jobs_found": 0,
            "total_jobs_saved": 0,
            "message": "No enabled companies to process",
        }

    logger.info(f"📋 Processing {len(enabled_companies)} enabled companies")

    # Prepare data for tasks (convert objects to dictionaries)
    config_dict = prepare_config_for_task(config)

    # Step 1: Validate all company data
    validated_companies, validation_failures = await _validate_companies(
        enabled_companies
    )

    # Step 2: Process validated companies concurrently
    processing_results = []
    if validated_companies:
        processing_results = await _process_companies_concurrently(
            validated_companies,
            config_dict,
            prompt_template_path,
            max_concurrent_companies,
        )
    else:
        logger.warning("⚠️ No companies passed validation - skipping processing step")

    # Step 3: Combine all results and aggregate
    all_results = validation_failures + processing_results
    logger.info(f"📊 Step 3: Aggregating results from {len(all_results)} companies...")
    aggregated_results = await aggregate_results_task(all_results)

    # Step 4: Save results if configured
    aggregated_results = await _save_results_if_configured(aggregated_results, config)

    # Final summary
    summary = aggregated_results
    logger.info("🎉 Stage 1 flow completed!")
    logger.info(f"📈 Success rate: {summary['success_rate']:.1%}")
    logger.info(f"📋 Total jobs found: {summary['total_jobs_found']}")
    logger.info(f"💾 Total jobs saved: {summary['total_jobs_saved']}")

    return summary
