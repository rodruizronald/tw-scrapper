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
            except KeyError:
                raise ValueError(f"Invalid parser type: {self.html_parser}")


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
    """Result of processing a company's job listings."""

    success: bool
    company_name: str
    jobs_found: int = 0
    jobs_saved: int = 0
    output_path: Path | None = None
    error: str | None = None
    processing_time: float = 0.0

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
