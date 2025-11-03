"""
Core models module.

This module provides domain models for jobs, companies, metrics, and parsers
used throughout the application.
"""

from src.core.models.jobs import (
    CompanyData,
    EmploymentType,
    ExperienceLevel,
    Job,
    JobDetails,
    JobFunction,
    JobRequirements,
    JobTechnologies,
    Location,
    Province,
    Technology,
    WorkMode,
)
from src.core.models.metrics import (
    CompanyStatus,
    CompanySummaryInput,
    StageMetricsInput,
    StageStatus,
)
from src.core.models.parsers import ParserType

__all__ = [
    "CompanyData",
    "CompanyStatus",
    "CompanySummaryInput",
    "EmploymentType",
    "ExperienceLevel",
    "Job",
    "JobDetails",
    "JobFunction",
    "JobRequirements",
    "JobTechnologies",
    "Location",
    "ParserType",
    "Province",
    "StageMetricsInput",
    "StageStatus",
    "Technology",
    "WorkMode",
]
