
from typing import Dict, Any, List
from pathlib import Path
import json

from pipeline.core.models import CompanyData
from pipeline.core.config import PipelineConfig


def prepare_company_data_for_task(company: CompanyData) -> Dict[str, Any]:
    """
    Convert CompanyData object to dictionary for Prefect task serialization.
    
    Args:
        company: CompanyData object
        
    Returns:
        Dictionary representation suitable for task parameters
    """
    return {
        "name": company.name,
        "career_url": company.career_url,
        "enabled": company.enabled,
        "selectors": company.selectors,
        "parser_type": company.parser_type.value if company.parser_type else "default",
    }


def prepare_config_for_task(config: PipelineConfig) -> Dict[str, Any]:
    """
    Convert PipelineConfig object to dictionary for Prefect task serialization.
    
    Args:
        config: PipelineConfig object
        
    Returns:
        Dictionary representation suitable for task parameters
    """
    return {
        "stage_1": {
            "output_dir": str(config.stage_1.output_dir),
            "save_output": config.stage_1.save_output,
        },
        "openai": {
            "api_key": config.openai.api_key,
            "model": config.openai.model,
            "max_retries": config.openai.max_retries,
            "timeout": config.openai.timeout,
        },
        "logging": {
            "level": config.logging.level,
            "log_to_file": config.logging.log_to_file,
            "log_to_console": config.logging.log_to_console,
        },
    }


def filter_enabled_companies(companies: List[CompanyData]) -> List[CompanyData]:
    """
    Filter out disabled companies before task execution.
    
    Args:
        companies: List of CompanyData objects
        
    Returns:
        List of enabled companies only
    """
    enabled = [c for c in companies if c.enabled]
    disabled_count = len(companies) - len(enabled)
    
    if disabled_count > 0:
        print(f"⏭️ Filtered out {disabled_count} disabled companies")
    
    return enabled


def save_task_results(
    results: Dict[str, Any], 
    output_dir: Path, 
    filename: str = "stage_1_task_results.json"
) -> Path:
    """
    Save task results to file for debugging and analysis.
    
    Args:
        results: Aggregated task results
        output_dir: Output directory
        filename: Output filename
        
    Returns:
        Path to saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return output_path
