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

"""

# Core pipeline components
from .core.config import LoggingConfig, OpenAIConfig, PipelineConfig, StageConfig
from .core.models import CompanyData, JobData, ParserType, ProcessingResult

# Service layer
from .services.extraction_service import (
    BrowserConfig,
    ExtractionConfig,
    WebExtractionService,
)
from .services.file_service import FileService
from .services.openai_service import OpenAIService

# Stage processors
from .stages.stage_1 import Stage1Processor

# Utilities
from .utils.exceptions import (
    CompanyProcessingError,
    ConfigurationError,
    FileOperationError,
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
    "BrowserConfig",
    "CompanyData",
    "CompanyProcessingError",
    "ConfigurationError",
    "ExtractionConfig",
    "FileOperationError",
    "FileService",
    "JobData",
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
    "WebExtractionService",
    "__author__",
    "__description__",
    "__version__",
]
