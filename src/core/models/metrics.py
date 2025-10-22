from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class StageStatus(str, Enum):
    """Valid status values for stage metrics."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


class CompanyStatus(str, Enum):
    """Valid status values for company processing."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"
    UNKNOWN = "unknown"


@dataclass
class StageMetricsInput:
    """Input model for stage metrics from pipeline components.

    This model is used by the service layer to accept stage metrics data
    from pipeline components. It will be mapped to StageMetrics in the repository.
    """

    status: StageStatus | str
    jobs_processed: int = 0
    jobs_completed: int = 0
    jobs_failed: int = 0
    execution_seconds: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    def __post_init__(self):
        """Validate stage metrics input."""
        # Convert string to enum if needed
        if isinstance(self.status, str):
            try:
                self.status = StageStatus(self.status)
            except ValueError as e:
                raise ValueError(
                    f"Invalid status: {self.status}. Must be one of: {', '.join([s.value for s in StageStatus])}"
                ) from e

        if self.jobs_processed < 0 or self.jobs_completed < 0 or self.jobs_failed < 0:
            raise ValueError("Job counts cannot be negative")
        if self.execution_seconds < 0:
            raise ValueError("Execution time cannot be negative")


@dataclass
class CompanySummaryInput:
    """Input model for company summary metrics from pipeline components.

    This model is used by the service layer to accept company summary data
    from pipeline components. It will be mapped to CompanyDailyMetrics in the repository.
    """

    new_jobs_found: int
    total_active_jobs: int
    overall_status: CompanyStatus | str
    total_inactive_jobs: int = 0
    jobs_deactivated_today: int = 0
    prefect_flow_run_id: str | None = None
    pipeline_version: str | None = None

    def __post_init__(self):
        """Validate company summary input."""
        # Convert string to enum if needed
        if isinstance(self.overall_status, str):
            try:
                self.overall_status = CompanyStatus(self.overall_status)
            except ValueError as e:
                raise ValueError(
                    f"Invalid overall_status: {self.overall_status}. Must be one of: {', '.join([s.value for s in CompanyStatus])}"
                ) from e

        if self.new_jobs_found < 0 or self.total_active_jobs < 0:
            raise ValueError("Job counts cannot be negative")
        if self.total_inactive_jobs < 0 or self.jobs_deactivated_today < 0:
            raise ValueError("Job counts cannot be negative")
