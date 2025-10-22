"""
Job aggregate metrics data layer.

Provides models and repository for pipeline-wide daily aggregate metrics collection.
"""

from .models import DailyAggregateMetrics
from .repository import (
    JobAggregateMetricsRepository,
)

__all__ = [
    "DailyAggregateMetrics",
    "JobAggregateMetricsRepository",
]
