"""Factory class for creating parser instances."""

from typing import List, Type, Dict
from playwright.async_api import Page

from .base import SelectorParser
from .models import ParserType
from .parsers import DefaultParser, GreenhouseParser, AngularParser


class ParserFactory:
    """Factory class to create appropriate parser instances."""

    _parsers: Dict[ParserType, Type[SelectorParser]] = {
        ParserType.DEFAULT: DefaultParser,
        ParserType.GREENHOUSE: GreenhouseParser,
        ParserType.ANGULAR: AngularParser,
    }

    @classmethod
    def create_parser(
        cls, parser_type: ParserType, page: Page, selectors: List[str]
    ) -> SelectorParser:
        """
        Create a parser instance based on the specified type.

        Args:
            parser_type: The type of parser to create
            page: The Playwright page object
            selectors: List of CSS selectors to parse

        Returns:
            An instance of the appropriate parser class
        """
        parser_class = cls._parsers.get(parser_type, DefaultParser)
        return parser_class(page, selectors)

    @classmethod
    def register_parser(
        cls, parser_type: ParserType, parser_class: Type[SelectorParser]
    ) -> None:
        """
        Register a new parser type (for extensibility).

        Args:
            parser_type: The parser type enum value
            parser_class: The parser class to register
        """
        cls._parsers[parser_type] = parser_class

    @classmethod
    def get_available_parsers(cls) -> List[ParserType]:
        """
        Get a list of all available parser types.

        Returns:
            List of available ParserType enum values
        """
        return list(cls._parsers.keys())

    @classmethod
    def is_parser_available(cls, parser_type: ParserType) -> bool:
        """
        Check if a parser type is available.

        Args:
            parser_type: The parser type to check

        Returns:
            True if the parser is available, False otherwise
        """
        return parser_type in cls._parsers
