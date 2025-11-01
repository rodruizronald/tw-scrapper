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
from .instances import AngularParser, DefaultParser, GreenhouseParser
from .models import ElementResult, ParseContext

__all__ = [
    "AngularParser",
    "DefaultParser",
    "ElementResult",
    "GreenhouseParser",
    "ParseContext",
    "ParserFactory",
    "SelectorParser",
]

__version__ = "1.0.0"
