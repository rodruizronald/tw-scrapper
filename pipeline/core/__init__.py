"""
Core pipeline components.

This module contains the fundamental building blocks of the job pipeline:
- Pipeline orchestrator
- Configuration management
- Data models
- Type definitions
"""

from .config import (
    BrowserConfig,
    LoguruConfig,
    OpenAIConfig,
    PipelineConfig,
    StageConfig,
    WebExtractionConfig,
)
from .models import CompanyData, JobData, ProcessingResult

__all__ = [
    "BrowserConfig",
    "CompanyData",
    "JobData",
    "LoguruConfig",
    "OpenAIConfig",
    "PipelineConfig",
    "ProcessingResult",
    "StageConfig",
    "WebExtractionConfig",
]
