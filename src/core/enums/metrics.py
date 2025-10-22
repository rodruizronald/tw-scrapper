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
