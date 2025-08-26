"""
Job Pipeline Package

A modular pipeline for extracting and processing job listings from company career pages.
Combines web scraping with AI-powered content analysis for intelligent job data extraction.

Key Features:
- Automated job listing extraction from career pages
- AI-powered job parsing using OpenAI
- Duplicate detection and historical tracking
- Concurrent processing with rate limiting
- Comprehensive error handling and logging
- Modular architecture for easy extension

Basic Usage:
    from pipeline import JobPipeline
    from pathlib import Path

    # Create pipeline with default configuration
    pipeline = JobPipeline.create_default_config(
        output_dir=Path("data/pipeline_output"),
        openai_api_key="your-api-key"
    )

    # Run the pipeline
    results = await pipeline.run_full_pipeline(
        companies_file=Path("input/companies.json"),
        prompt_template_path=Path("input/prompts/job_title_url_parser.md")
    )

Advanced Usage:
    from pipeline import JobPipeline, PipelineConfig, StageConfig, OpenAIConfig

    # Create custom configuration
    config = PipelineConfig(
        stage_1=StageConfig(
            output_dir=Path("custom/output"),
            save_output=True
        ),
        openai=OpenAIConfig(
            model="gpt-4",
            max_retries=5,
            timeout=60
        )
    )

    pipeline = JobPipeline(config)
"""

# Package initialization logging
import logging
from pathlib import Path

# Core pipeline components
from .core.config import LoggingConfig, OpenAIConfig, PipelineConfig, StageConfig
from .core.models import CompanyData, JobData, ParserType, ProcessingResult
from .core.pipeline import JobPipeline
from .services.file_service import FileService

# Service layer
from .services.html_service import HTMLExtractor
from .services.openai_service import OpenAIService

# Stage processors
from .stages.stage_1 import Stage1Processor

# Utilities
from .utils.exceptions import (
    CompanyProcessingError,
    ConfigurationError,
    FileOperationError,
    HTMLExtractionError,
    OpenAIProcessingError,
    PipelineError,
    ValidationError,
)

# Version information
__version__ = "1.0.0"
__author__ = "Job Pipeline Team"
__description__ = "AI-powered job listing extraction pipeline"

# Public API
__all__ = [
    "CompanyData",
    "CompanyProcessingError",
    "ConfigurationError",
    "FileOperationError",
    "FileService",
    "HTMLExtractionError",
    "HTMLExtractor",
    "JobData",
    "JobPipeline",
    "LoggingConfig",
    "OpenAIConfig",
    "OpenAIProcessingError",
    "OpenAIService",
    "ParserType",
    "PipelineConfig",
    "PipelineError",
    "ProcessingResult",
    "Stage1Processor",
    "StageConfig",
    "ValidationError",
    "__author__",
    "__description__",
    "__version__",
]


# Package-level convenience functions
def create_pipeline(
    output_dir: str, openai_api_key: str = "", log_level: str = "INFO"
) -> JobPipeline:
    """
    Convenience function to create a pipeline with default settings.

    Args:
        output_dir: Directory for pipeline output
        openai_api_key: OpenAI API key (uses env var if None)
        log_level: Logging level

    Returns:
        Configured JobPipeline instance
    """

    return JobPipeline.create_default_config(
        output_dir=Path(output_dir), openai_api_key=openai_api_key, log_level=log_level
    )


def load_pipeline_from_config(config_file: str) -> JobPipeline:
    """
    Convenience function to load pipeline from configuration file.

    Args:
        config_file: Path to configuration JSON file

    Returns:
        Configured JobPipeline instance
    """

    return JobPipeline.from_config_file(Path(config_file))


logger = logging.getLogger(__name__)
logger.info(f"Job Pipeline package v{__version__} initialized")
