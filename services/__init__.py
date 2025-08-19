"""
Services module for high-level web operations.

This module contains service classes that orchestrate complex operations
involving multiple components like parsers, browsers, and data processing.
"""

from .extraction import (
    BrowserConfig,
    ExtractionConfig,
    WebExtractionService,
    extract_by_selectors,
    extract_from_urls_batch,
)

__all__ = [
    # Configuration classes
    "BrowserConfig",
    "ExtractionConfig",
    # Main service class
    "WebExtractionService",
    # Convenience functions
    "extract_by_selectors",
    "extract_from_urls_batch",
]

__version__ = "1.0.0"
