"""
Service layer for the job pipeline.

This module contains service classes that handle specific aspects of the pipeline:
- HTML extraction from web pages
- OpenAI API interactions
- File operations and data persistence
"""

from .file_service import FileService
from .job_extraction_service import JobExtractionService
from .openai_service import OpenAIService
from .web_extraction_service import (
    BrowserConfig,
    WebExtractionConfig,
    WebExtractionService,
)

__all__ = [
    "BrowserConfig",
    "FileService",
    "JobExtractionService",
    "OpenAIService",
    "WebExtractionConfig",
    "WebExtractionService",
]
