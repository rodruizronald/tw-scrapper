"""
Core configuration module.

This module provides configuration classes for system paths, external service
integrations, and service-specific settings used throughout the application.
"""

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
    "IntegrationsConfig",
    "OpenAIConfig",
    "OpenAIServiceConfig",
    "PathsConfig",
    "WebExtractionConfig",
    "WebParserConfig",
]
