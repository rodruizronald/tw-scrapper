"""
Parser module for extracting content from web pages with different rendering strategies.

This module provides a flexible parser system that can handle:
- Standard HTML pages
- Greenhouse iframe-based job boards
- Angular single-page applications
- Extensible for additional parser types

Example usage:
    from parsers import ParserFactory, ParserType

    parser = ParserFactory.create_parser(
        ParserType.ANGULAR,
        page,
        selectors
    )
    results = await parser.parse()
"""

from .base import SelectorParser
from .factory import ParserFactory
from .instances import DefaultParser, GreenhouseParser, AngularParser
from .models import ParserType, ElementResult, ParseContext

__all__ = [
    # Main factory for creating parsers
    "ParserFactory",
    # Parser types enum
    "ParserType",
    # Data models
    "ElementResult",
    "ParseContext",
    # Base class (for extending)
    "SelectorParser",
    # Concrete parser implementations
    "DefaultParser",
    "GreenhouseParser",
    "AngularParser",
]

__version__ = "1.0.0"
