"""
Job aggregate metrics data layer.

Provides models and repository for pipeline-wide daily aggregate metrics collection.
"""

from pipeline.data.job_aggregate_metrics.models import DailyAggregateMetrics
from pipeline.data.job_aggregate_metrics.repository import (
    JobAggregateMetricsRepository,
)

__all__ = [
    "DailyAggregateMetrics",
    "JobAggregateMetricsRepository",
]
