
from prefect import task
from prefect.logging import get_run_logger
from typing import Dict, Any
import asyncio
from pathlib import Path

from pipeline.core.models import CompanyData, ProcessingResult
from pipeline.core.config import PipelineConfig
from pipeline.stages.stage_1 import Stage1Processor
from pipeline.utils.exceptions import (
    ValidationError,
    HTMLExtractionError,
    OpenAIProcessingError,
    FileOperationError,
)


@task(
    name="Process Company",
    description="Extract job listings from a single company's career page",
    tags=["stage-1", "company-processing"],
    retries=2,
    retry_delay_seconds=30,
    timeout_seconds=300,  # 5 minutes per company
)
async def process_company_task(
    company_data: Dict[str, Any],
    config: Dict[str, Any],
    prompt_template_path: str,
) -> Dict[str, Any]:
    """
    Prefect task to process a single company for job listings.
    
    Args:
        company_data: Dictionary representation of CompanyData
        config: Dictionary representation of PipelineConfig
        prompt_template_path: Path to the OpenAI prompt template
        
    Returns:
        Dictionary representation of ProcessingResult
        
    Raises:
        ValidationError: For non-retryable validation errors
        Exception: For retryable errors (network, API, file operations)
    """
    logger = get_run_logger()
    
    try:
        # Convert dictionaries back to objects
        company = CompanyData(**company_data)
        pipeline_config = PipelineConfig.from_dict(config)
        
        logger.info(f"🏢 Starting task for company: {company.name}")
        
        # Initialize processor
        processor = Stage1Processor(pipeline_config, prompt_template_path)
        
        # Process the company
        result = await processor.process_single_company(company)
        
        # Log result summary
        if result.success:
            logger.info(
                f"✅ {company.name}: Successfully processed "
                f"({result.jobs_found} found, {result.jobs_saved} saved) "
                f"in {result.processing_time:.2f}s"
            )
        else:
            logger.error(f"❌ {company.name}: Processing failed - {result.error}")
        
        # Convert result to dictionary for Prefect serialization
        result_dict = result.to_dict()
        
        # Add task-specific metadata
        result_dict["task_metadata"] = {
            "prefect_task_run_id": None,  # Will be populated by Prefect
            "retry_count": 0,  # Will be updated by Prefect on retries
        }
        
        return result_dict
        
    except ValidationError as e:
        # Non-retryable errors - don't retry these
        logger.error(f"❌ Validation error for {company_data.get('name', 'unknown')}: {e}")
        
        # Create failed result
        failed_result = ProcessingResult(
            success=False,
            company_name=company_data.get('name', 'unknown'),
            error=str(e),
            error_type="ValidationError",
            retryable=False,
            stage="stage_1"
        )
        
        # Return the failed result instead of raising (so flow continues)
        return failed_result.to_dict()
        
    except (HTMLExtractionError, OpenAIProcessingError, FileOperationError) as e:
        # Retryable errors - let Prefect handle retries
        logger.warning(
            f"⚠️ Retryable error for {company_data.get('name', 'unknown')}: {e}"
        )
        # Re-raise to trigger Prefect retry mechanism
        raise
        
    except Exception as e:
        # Unexpected errors - log and re-raise for retry
        logger.error(
            f"💥 Unexpected error for {company_data.get('name', 'unknown')}: {e}"
        )
        # Re-raise to trigger Prefect retry mechanism
        raise


@task(
    name="Validate Company Data",
    description="Validate company data before processing",
    tags=["stage-1", "validation"],
    retries=0,  # No retries for validation
    timeout_seconds=10,
)
def validate_company_data_task(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate company data structure and required fields.
    
    Args:
        company_data: Dictionary representation of company data
        
    Returns:
        Validated company data dictionary
        
    Raises:
        ValidationError: If company data is invalid
    """
    logger = get_run_logger()
    
    try:
        # Create CompanyData object to validate structure
        company = CompanyData(**company_data)
        
        # Additional validation
        if not company.enabled:
            raise ValidationError(
                field="enabled",
                value=str(company.enabled),
                message="Company is disabled"
            )
            
        if not company.career_url.startswith(('http://', 'https://')):
            raise ValidationError(
                field="career_url",
                value=company.career_url,
                message="Invalid URL format"
            )
        
        logger.info(f"✅ Validation passed for company: {company.name}")
        return company_data
        
    except Exception as e:
        logger.error(f"❌ Validation failed for {company_data.get('name', 'unknown')}: {e}")
        raise ValidationError(
            field="company_data",
            value=str(company_data),
            message=str(e)
        )


@task(
    name="Aggregate Results",
    description="Aggregate processing results from all companies",
    tags=["stage-1", "aggregation"],
    retries=0,
    timeout_seconds=60,
)
def aggregate_results_task(
    company_results: list[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate results from all company processing tasks.
    
    Args:
        company_results: List of ProcessingResult dictionaries
        
    Returns:
        Aggregated statistics and summary
    """
    logger = get_run_logger()
    
    successful_companies = [r for r in company_results if r.get('success', False)]
    failed_companies = [r for r in company_results if not r.get('success', False)]
    
    total_jobs_found = sum(r.get('jobs_found', 0) for r in company_results)
    total_jobs_saved = sum(r.get('jobs_saved', 0) for r in company_results)
    total_processing_time = sum(r.get('processing_time', 0) for r in company_results)
    
    # Categorize failures
    retryable_failures = [r for r in failed_companies if r.get('retryable', True)]
    non_retryable_failures = [r for r in failed_companies if not r.get('retryable', True)]
    
    summary = {
        "total_companies": len(company_results),
        "successful_companies": len(successful_companies),
        "failed_companies": len(failed_companies),
        "retryable_failures": len(retryable_failures),
        "non_retryable_failures": len(non_retryable_failures),
        "total_jobs_found": total_jobs_found,
        "total_jobs_saved": total_jobs_saved,
        "total_processing_time": total_processing_time,
        "average_processing_time": total_processing_time / len(company_results) if company_results else 0,
        "success_rate": len(successful_companies) / len(company_results) if company_results else 0,
        "detailed_results": company_results,
    }
    
    # Log summary
    logger.info("📊 STAGE 1 TASK AGGREGATION SUMMARY")
    logger.info(f"✅ Successful: {len(successful_companies)}/{len(company_results)}")
    logger.info(f"❌ Failed: {len(failed_companies)} (retryable: {len(retryable_failures)}, non-retryable: {len(non_retryable_failures)})")
    logger.info(f"📋 Jobs found: {total_jobs_found}")
    logger.info(f"💾 Jobs saved: {total_jobs_saved}")
    logger.info(f"⏱️ Total time: {total_processing_time:.2f}s")
    logger.info(f"📈 Success rate: {summary['success_rate']:.1%}")
    
    if failed_companies:
        logger.warning("Failed companies:")
        for result in failed_companies:
            company_name = result.get('company_name', 'unknown')
            error = result.get('error', 'unknown error')
            retryable = result.get('retryable', True)
            retry_indicator = "🔄" if retryable else "🚫"
            logger.warning(f"  {retry_indicator} {company_name}: {error}")
    
    return summary
