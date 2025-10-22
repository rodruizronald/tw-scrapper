"""
Data layer for MongoDB storage.

This module provides database connectivity, models, repositories, and mappers
for storing and retrieving job data.
"""

from .database import DatabaseController, db_controller
from .job_aggregate_metrics.repository import JobAggregateMetricsRepository
from .job_daily_metrics import CompanyDailyMetrics
from .job_daily_metrics.repository import JobDailyMetricsRepository
from .job_listing import JobListing, JobListingRepository, JobMapper, TechnologyInfo

# Initialize global repository
job_listing_repository = JobListingRepository(db_controller)
job_daily_metrics_repository = JobDailyMetricsRepository(db_controller)
job_aggregate_metrics_repository = JobAggregateMetricsRepository(db_controller)

__all__ = [
    "CompanyDailyMetrics",
    "DatabaseController",
    "JobAggregateMetricsRepository",
    "JobDailyMetricsRepository",
    "JobListing",
    "JobListingRepository",
    "JobMapper",
    "TechnologyInfo",
    "db_controller",
    "job_aggregate_metrics_repository",
    "job_daily_metrics_repository",
    "job_listing_repository",
]
