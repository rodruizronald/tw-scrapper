from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from parsers import ParserType


@dataclass
class WebParserSelectors:
    """HTML selectors for web parsing."""

    job_board: list[str]
    job_description: list[str]


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
class CompanyData:
    """Data structure for company information."""

    name: str
    career_url: str
    web_parser: dict[str, Any]
    enabled: bool = True

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if not self.name or not self.career_url:
            raise ValueError("Company name and career_url are required")

        # Convert web_parser dict to WebParserConfig object
        if isinstance(self.web_parser, dict):
            self.web_parser = WebParserConfig(
                type=self.web_parser.get("type", "default"),
                selectors=self.web_parser.get("selectors", {}),
            )

    @property
    def parser_type(self) -> ParserType:
        """Get parser type."""
        return self.web_parser.parser_type

    @property
    def job_board_selectors(self) -> list[str]:
        """Get job board selectors."""
        return self.web_parser.job_board_selectors

    @property
    def job_card_selectors(self) -> list[str]:
        """Get job card selectors."""
        return self.web_parser.job_card_selectors

    def to_dict(self) -> dict[str, Any]:
        """Convert CompanyData to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "career_url": self.career_url,
            "web_parser": {
                "type": self.web_parser.type,
                "selectors": self.web_parser.selectors,
            },
            "enabled": self.enabled,
        }


@dataclass
class JobData:
    """Data structure for individual job information."""

    title: str
    url: str
    signature: str
    company: str
    timestamp: str

    def __post_init__(self):
        """Validate job data after initialization."""
        if not self.url:
            raise ValueError("Job URL is required")


@dataclass
class ProcessingResult:
    """Result of processing a single company."""

    # Basic result information
    success: bool
    company_name: str

    # Success metrics
    jobs_found: int = 0
    jobs_saved: int = 0
    processing_time: float = 0.0

    # File paths
    output_path: Path | None = None

    # Error information
    error: str | None = None
    error_type: str | None = None

    # Timing information
    start_time: datetime | None = None
    end_time: datetime | None = None

    # Additional metadata
    stage: str = "stage_1"
    retryable: bool = True

    @property
    def is_successful(self) -> bool:
        """Check if processing was successful."""
        return self.success and self.error is None

    def __str__(self) -> str:
        """String representation of the result."""
        if self.success:
            return f"✅ {self.company_name}: {self.jobs_found} jobs found, {self.jobs_saved} saved"
        else:
            return f"❌ {self.company_name}: {self.error}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "company_name": self.company_name,
            "jobs_found": self.jobs_found,
            "jobs_saved": self.jobs_saved,
            "processing_time": self.processing_time,
            "output_path": str(self.output_path) if self.output_path else None,
            "error": self.error,
            "error_type": self.error_type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "stage": self.stage,
            "retryable": self.retryable,
        }
