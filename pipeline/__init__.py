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
- MongoDB data layer for storage

"""

# Core pipeline components
from .core.config import (
    BrowserConfig,
    OpenAIConfig,
    PipelineConfig,
    StageConfig,
    WebExtractionConfig,
)
from .core.models import CompanyData, ParserType

# Data layer
from .data import (
    DatabaseController,
    JobListing,
    JobListingRepository,
    JobMapper,
    db_controller,
    job_listing_repository,
)

# Service layer
from .services.openai_service import OpenAIService
from .services.web_extraction_service import WebExtractionService

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
__description__ = "AI-powered job listing extraction pipeline with MongoDB integration"

# Public API
__all__ = [
    "BrowserConfig",
    "CompanyData",
    "CompanyProcessingError",
    "ConfigurationError",
    "DatabaseController",
    "FileOperationError",
    "JobListing",
    "JobListingRepository",
    "JobMapper",
    "OpenAIConfig",
    "OpenAIProcessingError",
    "OpenAIService",
    "ParserType",
    "PipelineConfig",
    "PipelineError",
    "Stage1Processor",
    "StageConfig",
    "ValidationError",
    "WebExtractionConfig",
    "WebExtractionService",
    "__author__",
    "__description__",
    "__version__",
    "db_controller",
    "job_listing_repository",
]
