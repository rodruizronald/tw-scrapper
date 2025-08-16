"""
Services module for high-level web operations.

This module contains service classes that orchestrate complex operations
involving multiple components like parsers, browsers, and data processing.
"""

from .extraction import (
    WebExtractionService,
    ExtractionConfig,
    BrowserConfig,
    extract_by_selectors,
    extract_from_urls_batch,
)

__all__ = [
    # Main service class
    "WebExtractionService",
    # Configuration classes
    "ExtractionConfig",
    "BrowserConfig",
    # Convenience functions
    "extract_by_selectors",
    "extract_from_urls_batch",
]

__version__ = "1.0.0"
