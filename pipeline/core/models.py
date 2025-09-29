from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pipeline.parsers.models import ParserType


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
    web_parser: dict[str, Any] | WebParserConfig
    enabled: bool = True

    # After __post_init__, web_parser is always WebParserConfig
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
    def web_parser_config(self) -> WebParserConfig:
        """Get parser type."""
        assert isinstance(self.web_parser, WebParserConfig)
        return self.web_parser

    @property
    def parser_type(self) -> ParserType:
        """Get parser type."""
        assert isinstance(self.web_parser, WebParserConfig)
        return self.web_parser.parser_type

    @property
    def job_board_selectors(self) -> list[str]:
        """Get job board selectors."""
        assert isinstance(self.web_parser, WebParserConfig)
        return self.web_parser.job_board_selectors

    @property
    def job_card_selectors(self) -> list[str]:
        """Get job card selectors."""
        assert isinstance(self.web_parser, WebParserConfig)
        return self.web_parser.job_card_selectors

    def to_dict(self) -> dict[str, Any]:
        """Convert CompanyData to dictionary for JSON serialization."""
        assert isinstance(self.web_parser, WebParserConfig)
        return {
            "name": self.name,
            "career_url": self.career_url,
            "web_parser": {
                "type": self.web_parser.type,
                "selectors": self.web_parser.selectors,
            },
            "enabled": self.enabled,
        }


class Location(str, Enum):
    COSTA_RICA = "Costa Rica"
    LATAM = "LATAM"


class WorkMode(str, Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ONSITE = "Onsite"


class EmploymentType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    FREELANCE = "Freelance"
    TEMPORARY = "Temporary"
    INTERNSHIP = "Internship"


class ExperienceLevel(str, Enum):
    ENTRY_LEVEL = "Entry-level"
    JUNIOR = "Junior"
    MID_LEVEL = "Mid-level"
    SENIOR = "Senior"
    LEAD = "Lead"
    PRINCIPAL = "Principal"
    EXECUTIVE = "Executive"


@dataclass
class JobDetails:
    """Job details extracted from Stage 2 analysis."""

    eligible: bool
    location: Location
    work_mode: WorkMode
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    description: str


@dataclass
class Job:
    """Evolving job model that grows through pipeline stages."""

    # Stage 1 data (always present)
    title: str
    url: str
    signature: str
    company: str
    timestamp: str

    # Stage 2 data (optional, populated after stage 2)
    details: JobDetails | None = None

    @property
    def is_stage_2_processed(self) -> bool:
        """Check if job has been processed through Stage 2."""
        return self.details is not None

    @property
    def is_eligible(self) -> bool:
        """Check if job is eligible (requires Stage 2 processing)."""
        return self.details is not None and self.details.eligible

    def __post_init__(self):
        """Validate required fields."""
        if not self.title:
            raise ValueError("Job title is required")
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
