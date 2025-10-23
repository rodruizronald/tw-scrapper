"""
Core configuration module.

This module provides configuration classes for system paths, external service
integrations, and service-specific settings used throughout the application.
"""

from .database import DatabaseConfig, get_database_config
from .integrations import (
    BrowserConfig,
    IntegrationsConfig,
    OpenAIConfig,
    WebExtractionConfig,
)
from .services import OpenAIServiceConfig, WebParserConfig
from .system import PathsConfig

__all__ = [
    "BrowserConfig",
    "DatabaseConfig",
    "IntegrationsConfig",
    "OpenAIConfig",
    "OpenAIServiceConfig",
    "PathsConfig",
    "WebExtractionConfig",
    "WebParserConfig",
    "get_database_config",
]
