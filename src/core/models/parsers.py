"""Parser-related models."""

from enum import Enum


class ParserType(str, Enum):
    """Types of parsers available for job extraction."""

    DEFAULT = "default"
    GREENHOUSE = "greenhouse"
    ANGULAR = "angular"
