"""
Data models for daily job metrics.

These models represent daily metrics for individual companies in the job scraping pipeline.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId


@dataclass
class StageMetrics:
    """Metrics for a specific pipeline stage."""

    status: str  # success|failed|skipped
    jobs_processed: int = 0
    jobs_completed: int = 0
    jobs_failed: int = 0
    execution_seconds: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        data = {
            "status": self.status,
            "jobs_processed": self.jobs_processed,
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "execution_seconds": self.execution_seconds,
        }

        if self.started_at:
            data["started_at"] = self.started_at
        if self.completed_at:
            data["completed_at"] = self.completed_at
        if self.error_message:
            data["error_message"] = self.error_message

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StageMetrics":
        """Create from dictionary."""
        return cls(
            status=data.get("status", "unknown"),
            jobs_processed=data.get("jobs_processed", 0),
            jobs_completed=data.get("jobs_completed", 0),
            jobs_failed=data.get("jobs_failed", 0),
            execution_seconds=data.get("execution_seconds", 0.0),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            error_message=data.get("error_message"),
        )


@dataclass
class CompanyDailyMetrics:
    """Daily metrics for a single company's pipeline run."""

    date: str  # YYYY-MM-DD
    company_name: str
    document_type: str = "company_daily"

    # MongoDB unique identifier
    _id: ObjectId | None = None

    # Company-level metrics
    new_jobs_found: int = 0
    total_active_jobs: int = 0
    total_inactive_jobs: int = 0
    jobs_deactivated_today: int = 0
    overall_status: str = "pending"  # success|partial|failed|pending

    # Stage metrics (stored as flat fields in MongoDB)
    stage_1_metrics: StageMetrics | None = None
    stage_2_metrics: StageMetrics | None = None
    stage_3_metrics: StageMetrics | None = None
    stage_4_metrics: StageMetrics | None = None

    # Metadata
    prefect_flow_run_id: str | None = None
    pipeline_version: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_updated_stage: str | None = None

    def to_flat_dict(self) -> dict[str, Any]:
        """
        Convert to flat dictionary structure for MongoDB storage.

        This flattens stage metrics into individual fields like:
        stage_1_status, stage_1_jobs_processed, etc.
        """
        doc = {
            "date": self.date,
            "company_name": self.company_name,
            "document_type": self.document_type,
            "new_jobs_found": self.new_jobs_found,
            "total_active_jobs": self.total_active_jobs,
            "total_inactive_jobs": self.total_inactive_jobs,
            "jobs_deactivated_today": self.jobs_deactivated_today,
            "overall_status": self.overall_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        # Add _id if present
        if self._id:
            doc["_id"] = self._id

        # Add optional metadata fields
        if self.prefect_flow_run_id:
            doc["prefect_flow_run_id"] = self.prefect_flow_run_id
        if self.pipeline_version:
            doc["pipeline_version"] = self.pipeline_version
        if self.last_updated_stage:
            doc["last_updated_stage"] = self.last_updated_stage

        # Flatten stage metrics
        for stage_num in range(1, 5):
            stage_metrics = getattr(self, f"stage_{stage_num}_metrics", None)
            if stage_metrics:
                stage_dict = stage_metrics.to_dict()
                for key, value in stage_dict.items():
                    doc[f"stage_{stage_num}_{key}"] = value

        return doc

    @classmethod
    def from_flat_dict(cls, data: dict[str, Any]) -> "CompanyDailyMetrics":
        """
        Create from flat dictionary structure.

        Reconstructs stage metrics from flattened fields.
        """
        # Extract stage metrics
        stage_metrics = {}
        for stage_num in range(1, 5):
            stage_prefix = f"stage_{stage_num}_"
            stage_data = {}

            for key, value in data.items():
                if key.startswith(stage_prefix):
                    field_name = key.replace(stage_prefix, "")
                    stage_data[field_name] = value

            if stage_data:
                stage_metrics[f"stage_{stage_num}_metrics"] = StageMetrics.from_dict(
                    stage_data
                )

        return cls(
            date=data.get("date", ""),
            company_name=data.get("company_name", ""),
            document_type=data.get("document_type", "company_daily"),
            _id=data.get("_id"),
            new_jobs_found=data.get("new_jobs_found", 0),
            total_active_jobs=data.get("total_active_jobs", 0),
            total_inactive_jobs=data.get("total_inactive_jobs", 0),
            jobs_deactivated_today=data.get("jobs_deactivated_today", 0),
            overall_status=data.get("overall_status", "pending"),
            prefect_flow_run_id=data.get("prefect_flow_run_id"),
            pipeline_version=data.get("pipeline_version"),
            created_at=data.get("created_at", datetime.now(UTC)),
            updated_at=data.get("updated_at", datetime.now(UTC)),
            last_updated_stage=data.get("last_updated_stage"),
            **stage_metrics,
        )
