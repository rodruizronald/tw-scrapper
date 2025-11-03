"""
Data repositories module.

This module provides repository classes for database operations following
the repository pattern, with a base repository for common CRUD operations
and specialized repositories for different data models.
"""

from src.data.repositories.aggregate_metrics_repo import AggregateMetricsRepository
from src.data.repositories.base_repo import BaseRepository
from src.data.repositories.daily_metrics_repo import DailyMetricsRepository
from src.data.repositories.job_listing_repo import JobListingRepository

__all__ = [
    "AggregateMetricsRepository",
    "BaseRepository",
    "DailyMetricsRepository",
    "JobListingRepository",
]
