"""
Service layer for the job pipeline.

This module contains service classes that handle specific aspects of the pipeline:
- HTML extraction from web pages
- OpenAI API interactions
- Database operations for pipeline stages
- Job metrics collection and aggregation
- Web page parsing strategies
"""

from .data_service import JobDataService
from .metrics_service import JobMetricsService, job_metrics_service
from .openai_service import OpenAIService
from .parsers import ParserFactory
from .web_extraction_service import WebExtractionService

__all__ = [
    "JobDataService",
    "JobMetricsService",
    "OpenAIService",
    "ParserFactory",
    "WebExtractionService",
    "job_metrics_service",
]
