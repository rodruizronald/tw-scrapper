"""
Service layer for the job pipeline.

This module contains service classes that handle specific aspects of the pipeline:
- HTML extraction from web pages
- OpenAI API interactions
- File operations and data persistence
"""

from .extraction_service import (
    BrowserConfig,
    ExtractionConfig,
    WebExtractionService,
    extract_by_selectors,
)
from .file_service import FileService
from .html_service import HTMLExtractor
from .job_extraction_service import JobExtractionService
from .openai_service import OpenAIService

__all__ = [
    "BrowserConfig",
    "ExtractionConfig",
    "FileService",
    "HTMLExtractor",
    "JobExtractionService",
    "OpenAIService",
    "WebExtractionService",
    "extract_by_selectors",
]
