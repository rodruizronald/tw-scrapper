
from prefect import flow, get_run_logger
from prefect.task_runners import ConcurrentTaskRunner
from typing import Dict, Any, List
from pathlib import Path
import asyncio

from pipeline.core.models import CompanyData
from pipeline.core.config import PipelineConfig
from pipeline.tasks.company_processing import (
    process_company_task,
    validate_company_data_task,
    aggregate_results_task,
)
from pipeline.tasks.utils import (
    prepare_company_data_for_task,
    prepare_config_for_task,
    filter_enabled_companies,
    save_task_results,
)


@flow(
    name="Stage 1: Job Extraction Pipeline",
    description="Extract job listings from company career pages with concurrent processing",
    version="1.0.0",
    task_runner=ConcurrentTaskRunner(),
    retries=1,
    retry_delay_seconds=60,
)
async def stage_1_flow(
    companies: List[CompanyData],
    config: PipelineConfig,
    prompt_template_path: str,
    max_concurrent_companies: int = 3,
) -> Dict[str, Any]:
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
            "message": "No enabled companies to process"
        }
    
    logger.info(f"📋 Processing {len(enabled_companies)} enabled companies")
    
    # Prepare data for tasks (convert objects to dictionaries)
    config_dict = prepare_config_for_task(config)
    
    # Step 1: Validate all company data first
    logger.info("🔍 Step 1: Validating company data...")
    validation_tasks = []
    
    for company in enabled_companies:
        company_dict = prepare_company_data_for_task(company)
        validation_task = validate_company_data_task.submit(company_dict)
        validation_tasks.append((company, validation_task))
    
    # Wait for all validations to complete
    validated_companies = []
    validation_failures = []
    
    for company, validation_task in validation_tasks:
        try:
            validated_data = await validation_task
            validated_companies.append((company, validated_data))
            logger.debug(f"✅ Validation passed: {company.name}")
        except Exception as e:
            logger.warning(f"❌ Validation failed: {company.name} - {e}")
            validation_failures.append({
                "company_name": company.name,
                "error": str(e),
                "error_type": "ValidationError",
                "retryable": False,
                "success": False,
                "stage": "validation"
            })
    
    logger.info(f"✅ Validation complete: {len(validated_companies)} passed, {len(validation_failures)} failed")
    
    # Step 2: Process validated companies concurrently
    if validated_companies:
        logger.info(f"🏭 Step 2: Processing {len(validated_companies)} companies concurrently...")
        
        # Create processing tasks with concurrency control
        processing_tasks = []
        semaphore = asyncio.Semaphore(max_concurrent_companies)
        
        async def process_with_semaphore(company_data_dict: Dict[str, Any]):
            async with semaphore:
                return await process_company_task.submit(
                    company_data_dict,
                    config_dict,
                    prompt_template_path
                )
        
        # Submit all processing tasks
        for company, validated_data in validated_companies:
            task = process_with_semaphore(validated_data)
            processing_tasks.append(task)
        
        # Wait for all processing tasks to complete
        processing_results = []
        for i, task in enumerate(processing_tasks):
            try:
                result = await task
                processing_results.append(result)
                company_name = validated_companies[i][0].name
                if result.get('success', False):
                    logger.info(f"✅ Completed: {company_name}")
                else:
                    logger.warning(f"❌ Failed: {company_name}")
            except Exception as e:
                # This shouldn't happen as tasks handle their own exceptions
                company_name = validated_companies[i][0].name
                logger.error(f"💥 Unexpected task failure: {company_name} - {e}")
                processing_results.append({
                    "success": False,
                    "company_name": company_name,
                    "error": f"Task execution failed: {e}",
                    "error_type": "TaskExecutionError",
                    "retryable": True,
                    "stage": "processing"
                })
    else:
        processing_results = []
        logger.warning("⚠️ No companies passed validation - skipping processing step")
    
    # Step 3: Combine all results (validation failures + processing results)
    all_results = validation_failures + processing_results
    
    logger.info(f"📊 Step 3: Aggregating results from {len(all_results)} companies...")
    
    # Aggregate results
    aggregated_results = await aggregate_results_task.submit(all_results)
    
    # Step 4: Save results if configured
    if config.stage_1.save_output:
        try:
            results_path = save_task_results(
                aggregated_results,
                config.stage_1.output_dir,
                "stage_1_flow_results.json"
            )
            logger.info(f"💾 Results saved to: {results_path}")
            aggregated_results["results_file_path"] = str(results_path)
        except Exception as e:
            logger.warning(f"⚠️ Failed to save results file: {e}")
    
    # Final summary
    summary = aggregated_results
    logger.info("🎉 Stage 1 flow completed!")
    logger.info(f"📈 Success rate: {summary['success_rate']:.1%}")
    logger.info(f"📋 Total jobs found: {summary['total_jobs_found']}")
    logger.info(f"💾 Total jobs saved: {summary['total_jobs_saved']}")
    
    return summary


@flow(
    name="Stage 1: Single Company Processing",
    description="Process a single company for job listings (useful for testing)",
    version="1.0.0",
)
async def stage_1_single_company_flow(
    company: CompanyData,
    config: PipelineConfig,
    prompt_template_path: str,
) -> Dict[str, Any]:
    """
    Simplified flow for processing a single company.
    
    Useful for testing individual companies or debugging.
    
    Args:
        company: Company to process
        config: Pipeline configuration
        prompt_template_path: Path to OpenAI prompt template
        
    Returns:
        Processing result for the single company
    """
    logger = get_run_logger()
    
    logger.info(f"🏢 Processing single company: {company.name}")
    
    # Prepare data
    company_dict = prepare_company_data_for_task(company)
    config_dict = prepare_config_for_task(config)
    
    # Validate
    try:
        validated_data = await validate_company_data_task.submit(company_dict)
        logger.info(f"✅ Validation passed for {company.name}")
    except Exception as e:
        logger.error(f"❌ Validation failed for {company.name}: {e}")
        return {
            "success": False,
            "company_name": company.name,
            "error": str(e),
            "error_type": "ValidationError",
            "retryable": False,
        }
    
    # Process
    try:
        result = await process_company_task.submit(
            validated_data,
            config_dict,
            prompt_template_path
        )
        
        if result.get('success', False):
            logger.success(f"✅ Successfully processed {company.name}")
        else:
            logger.error(f"❌ Failed to process {company.name}: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"💥 Unexpected error processing {company.name}: {e}")
        return {
            "success": False,
            "company_name": company.name,
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "retryable": True,
        }
