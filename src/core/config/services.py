from dataclasses import dataclass
from typing import Any

from core.models.parsers import ParserType


@dataclass
class WebParserConfig:
    """Web parser configuration."""

    type: str
    selectors: dict[str, list[str]]

    def __post_init__(self):
        """Validate parser configuration."""
        # Normalize parser type
        if isinstance(self.type, str):
            try:
                ParserType[self.type.upper()]
            except KeyError as e:
                raise ValueError(f"Invalid parser type: {self.type}") from e

    @property
    def parser_type(self) -> ParserType:
        """Get parser type as enum."""
        return ParserType[self.type.upper()]

    @property
    def job_board_selectors(self) -> list[str]:
        """Get job board selectors."""
        return self.selectors.get("job_board", [])

    @property
    def job_card_selectors(self) -> list[str]:
        """Get job card selectors."""
        return self.selectors.get("job_card", [])


@dataclass
class OpenAIServiceConfig:
    """Configuration for OpenAI service."""

    system_message: str
    prompt_template: str
    prompt_variables: list[str]
    response_format: dict[str, Any]

    def __post_init__(self):
        """Validate OpenAI service configuration."""
        if not self.system_message or not self.system_message.strip():
            raise ValueError("system_message cannot be empty")

        if not self.prompt_template or not self.prompt_template.strip():
            raise ValueError("prompt_template cannot be empty")

        if not isinstance(self.prompt_variables, list):
            raise ValueError("prompt_variables must be a list")

        if not self.prompt_variables:
            raise ValueError("prompt_variables cannot be empty")

        if not isinstance(self.response_format, dict):
            raise ValueError("response_format must be a dictionary")

        if not self.response_format:
            raise ValueError("response_format cannot be empty")
