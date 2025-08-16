"""Data models for the parser module."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from playwright.async_api import Frame, Page


class ParserType(Enum):
    """Enumeration of available parser types."""

    DEFAULT = "default"
    GREENHOUSE = "greenhouse"
    ANGULAR = "angular"


@dataclass
class ElementResult:
    """Data class to hold element extraction results."""

    selector: str
    found: bool
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    error_message: Optional[str] = None
    context: str = "main_page"


@dataclass
class ParseContext:
    """Context information for parsing operations."""

    page: Page
    frame: Optional[Frame] = None
    parser_type: ParserType = ParserType.DEFAULT

    @property
    def target(self) -> Page | Frame:
        """Returns the appropriate target for selector queries."""
        return self.frame if self.frame else self.page
