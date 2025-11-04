"""
Data layer for MongoDB storage.

This module provides database connectivity, models, repositories, and mappers
for storing and retrieving job data.
"""

from data.controller import DatabaseController, db_controller
from data.mappers.job_mapper import JobMapper
from data.models.daily_metrics import CompanyDailyMetrics
from data.models.job_listing import JobListing, TechnologyInfo
from data.repositories.aggregate_metrics_repo import AggregateMetricsRepository
from data.repositories.daily_metrics_repo import DailyMetricsRepository
from data.repositories.job_listing_repo import JobListingRepository

# Initialize global repository
job_listing_repository = JobListingRepository(db_controller)
job_daily_metrics_repository = DailyMetricsRepository(db_controller)
job_aggregate_metrics_repository = AggregateMetricsRepository(db_controller)

__all__ = [
    "AggregateMetricsRepository",
    "CompanyDailyMetrics",
    "DailyMetricsRepository",
    "DatabaseController",
    "JobListing",
    "JobListingRepository",
    "JobMapper",
    "TechnologyInfo",
    "db_controller",
    "job_aggregate_metrics_repository",
    "job_daily_metrics_repository",
    "job_listing_repository",
]
