
"""
Utility modules for the job pipeline.

This module contains utility functions and classes used throughout the pipeline:
- Custom exceptions
- Helper functions
- Common utilities
"""

from .exceptions import (
    PipelineError,
    CompanyProcessingError,
    HTMLExtractionError,
    OpenAIProcessingError,
    FileOperationError,
    ValidationError,
    ConfigurationError
)

__all__ = [
    "PipelineError",
    "CompanyProcessingError", 
    "HTMLExtractionError",
    "OpenAIProcessingError",
    "FileOperationError",
    "ValidationError",
    "ConfigurationError"
]
