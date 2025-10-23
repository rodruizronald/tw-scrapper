import os
from dataclasses import dataclass

from services.parsers.models import ParserType


@dataclass
class BrowserConfig:
    """Configuration for browser instances."""

    headless: bool
    timeout: int  # ms
    wait_until: str
    user_agent: str | None = None
    viewport: dict[str, int] | None = None
    extra_headers: dict[str, str] | None = None

    def __post_init__(self):
        """Validate browser wait_until and timeout configuration."""
        valid_wait_until = ["load", "domcontentloaded", "networkidle", "commit"]
        if self.wait_until not in valid_wait_until:
            raise ValueError(
                f"Invalid wait_until: {self.wait_until}. Must be one of {valid_wait_until}"
            )

        if self.timeout <= 0:
            raise ValueError("timeout must be positive")


@dataclass
class WebExtractionConfig:
    """Configuration for extraction operations."""

    browser_config: BrowserConfig
    max_retries: int
    retry_delay: float  # seconds
    parser_type: ParserType = ParserType.DEFAULT

    def __post_init__(self):
        """Validate that max_retries and retry_delay."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        if self.retry_delay <= 0:
            raise ValueError("retry_delay must be positive")


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API integration."""

    model: str
    max_retries: int
    timeout: int  # seconds
    api_key: str | None = None

    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide api_key in config."
            )


@dataclass
class IntegrationsConfig:
    """Integrations configuration for different services."""

    openai: OpenAIConfig
    web_extraction: WebExtractionConfig
