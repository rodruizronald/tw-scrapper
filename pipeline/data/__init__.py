"""
Data layer for MongoDB storage.

This module provides database connectivity, models, repositories, and mappers
for storing and retrieving job data.
"""

from .database import DatabaseController, db_controller
from .job_listing import JobListing, JobListingRepository, JobMapper, TechnologyInfo

# Initialize global repository
job_listing_repository = JobListingRepository(db_controller)

__all__ = [
    "DatabaseController",
    "JobListing",
    "JobListingRepository",
    "JobMapper",
    "TechnologyInfo",
    "db_controller",
    "job_listing_repository",
]
