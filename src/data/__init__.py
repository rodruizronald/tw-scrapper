"""
Data layer for MongoDB storage.

This module provides database connectivity, models, repositories, and mappers
for storing and retrieving job data.
"""

from .controller import DatabaseController, db_controller
from .mappers.job_listing_mapper import JobMapper
from .models.job_daily_metrics import CompanyDailyMetrics
from .models.job_listing import JobListing, TechnologyInfo
from .repositories.job_aggregate_repo import JobAggregateMetricsRepository
from .repositories.job_daily_metrics_repo import JobDailyMetricsRepository
from .repositories.job_listing_repo import JobListingRepository

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
