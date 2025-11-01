"""
Core models module.

This module provides domain models for jobs, companies, metrics, and parsers
used throughout the application.
"""

from .jobs import (
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
from .metrics import CompanyStatus, CompanySummaryInput, StageMetricsInput, StageStatus
from .parsers import ParserType

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
