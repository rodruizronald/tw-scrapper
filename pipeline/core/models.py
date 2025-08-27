from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ParserType(Enum):
    """HTML parser types supported by the pipeline."""

    DEFAULT = "DEFAULT"
    GREENHOUSE = "GREENHOUSE"
    ANGULAR = "ANGULAR"


@dataclass
class CompanyData:
    """Data structure for company information."""

    name: str
    career_url: str
    html_parser: str
    job_board_selector: list[str]
    job_eligibility_selector: list[str]
    job_description_selector: list[str]
    enabled: bool = True

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if not self.name or not self.career_url:
            raise ValueError("Company name and career_url are required")

        # Normalize parser type
        if isinstance(self.html_parser, str):
            try:
                ParserType[self.html_parser.upper()]
            except KeyError as e:
                raise ValueError(f"Invalid parser type: {self.html_parser}") from e


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
    output_path: Optional[Path] = None

    # Error information
    error: Optional[str] = None
    error_type: Optional[str] = None  # New: for categorizing errors

    # Timing information (enhanced for Prefect)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Additional metadata for Prefect
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
