"""Data models for Company API."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CompanyCreate:
    """Model for creating a new company."""

    name: str
    is_active: bool = True


@dataclass
class Company:
    """Model representing a company from the API."""

    id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "Company":
        """Create Company instance from API response dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            is_active=data["is_active"],
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            ),
        )

    def to_dict(self) -> dict:
        """Convert Company instance to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
