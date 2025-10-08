"""
Database models for job listing storage.

This module contains the JobListing model optimized for MongoDB storage
following the exact structure specified for job data.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId


@dataclass
class TechnologyInfo:
    """Technology information with categorization and requirement status."""

    name: str
    category: str
    required: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return {
            "name": self.name,
            "category": self.category,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TechnologyInfo":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            category=data.get("category", ""),
            required=data.get("required", False),
        )


@dataclass
class JobListing:
    """
    Database model for job listings optimized for MongoDB storage.

    This model represents the complete job data structure as stored in the database,
    following the exact flat structure specified.
    """

    # Core job identification
    signature: str  # Unique identifier for deduplication
    title: str
    url: str
    company: str

    # Job details (flat structure)
    location: str
    work_mode: str
    employment_type: str
    experience_level: str
    job_function: str
    province: str
    city: str
    description: str

    # Job requirements (flat lists)
    responsibilities: list[str]
    skill_must_have: list[str]
    skill_nice_to_have: list[str]
    benefits: list[str]

    # Technologies
    technologies: list[TechnologyInfo]
    main_technologies: list[str]

    # Database metadata
    _id: ObjectId | None = None
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.signature:
            raise ValueError("Job signature is required")
        if not self.title:
            raise ValueError("Job title is required")
        if not self.url:
            raise ValueError("Job URL is required")
        if not self.company:
            raise ValueError("Company name is required")

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """Mark job listing as inactive."""
        self.active = False
        self.update_timestamp()

    def activate(self) -> None:
        """Mark job listing as active."""
        self.active = True
        self.update_timestamp()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert JobListing to dictionary for MongoDB storage.

        Returns:
            dict: Dictionary representation suitable for MongoDB
        """
        result: dict[str, Any] = {
            "signature": self.signature,
            "active": self.active,
            "title": self.title,
            "url": self.url,
            "company": self.company,
            "location": self.location,
            "work_mode": self.work_mode,
            "employment_type": self.employment_type,
            "experience_level": self.experience_level,
            "job_function": self.job_function,
            "province": self.province,
            "city": self.city,
            "description": self.description,
            "responsibilities": self.responsibilities,
            "skill_must_have": self.skill_must_have,
            "skill_nice_to_have": self.skill_nice_to_have,
            "benefits": self.benefits,
            "technologies": [tech.to_dict() for tech in self.technologies],
            "main_technologies": self.main_technologies,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        # Add MongoDB ObjectId if present
        if self._id is not None:
            result["_id"] = self._id

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobListing":
        """
        Create JobListing from dictionary (e.g., from MongoDB).

        Args:
            data: Dictionary containing job listing data

        Returns:
            JobListing: Created instance
        """
        # Create TechnologyInfo objects from technologies list
        technologies = [
            TechnologyInfo.from_dict(tech_data)
            for tech_data in data.get("technologies", [])
        ]

        # Create JobListing instance
        job_listing = cls(
            signature=data.get("signature", ""),
            title=data.get("title", ""),
            url=data.get("url", ""),
            company=data.get("company", ""),
            location=data.get("location", ""),
            work_mode=data.get("work_mode", ""),
            employment_type=data.get("employment_type", ""),
            experience_level=data.get("experience_level", ""),
            job_function=data.get("job_function", ""),
            province=data.get("province", ""),
            city=data.get("city", ""),
            description=data.get("description", ""),
            responsibilities=data.get("responsibilities", []),
            skill_must_have=data.get("skill_must_have", []),
            skill_nice_to_have=data.get("skill_nice_to_have", []),
            benefits=data.get("benefits", []),
            technologies=technologies,
            main_technologies=data.get("main_technologies", []),
        )

        # Set MongoDB metadata
        job_listing._id = data.get("_id")
        job_listing.active = data.get("active", True)

        # Set timestamps
        if "created_at" in data:
            job_listing.created_at = data["created_at"]
        if "updated_at" in data:
            job_listing.updated_at = data["updated_at"]

        return job_listing

    def __str__(self) -> str:
        """String representation of JobListing."""
        return f"JobListing(title='{self.title}', company='{self.company}', active={self.active})"

    def __repr__(self) -> str:
        """Detailed string representation of JobListing."""
        return (
            f"JobListing(signature='{self.signature}', title='{self.title}', "
            f"company='{self.company}', active={self.active})"
        )
