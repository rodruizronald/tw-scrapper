"""
Configuration settings for the persistence layer.

This module provides configuration management for database connections
and persistence layer settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load environment variables when this module is imported
# Try to find .env file in current directory or parent directories
current_dir = Path.cwd()
for parent in [current_dir, *list(current_dir.parents)]:
    env_path = parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        break


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    # Connection settings
    host: str = field(default_factory=lambda: os.getenv("MONGO_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("MONGO_PORT", "27017")))
    username: str | None = field(default_factory=lambda: os.getenv("MONGO_USERNAME"))
    password: str | None = field(default_factory=lambda: os.getenv("MONGO_PASSWORD"))
    database: str = field(
        default_factory=lambda: os.getenv("MONGO_DATABASE", "tw_scrapper")
    )
    auth_source: str = field(
        default_factory=lambda: os.getenv("MONGO_AUTH_SOURCE", "admin")
    )

    # Connection string (if provided, overrides individual settings)
    connection_string: str | None = field(
        default_factory=lambda: os.getenv("MONGO_CONNECTION_STRING")
    )

    # Timeout settings (in milliseconds)
    connection_timeout: int = field(
        default_factory=lambda: int(os.getenv("MONGO_CONNECTION_TIMEOUT", "5000"))
    )
    server_selection_timeout: int = field(
        default_factory=lambda: int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT", "5000"))
    )

    # Collection names
    job_listings_collection: str = field(
        default_factory=lambda: os.getenv(
            "MONGO_JOB_LISTINGS_COLLECTION", "job_listings"
        )
    )

    def build_connection_string(self) -> str:
        """Build MongoDB connection string from configuration."""
        if self.connection_string:
            return self.connection_string

        if self.username and self.password:
            # Include the database name in the connection string
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?authSource={self.auth_source}"
        else:
            return f"mongodb://{self.host}:{self.port}/{self.database}"

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "connection_string": self.build_connection_string(),
            "connection_timeout": self.connection_timeout,
            "server_selection_timeout": self.server_selection_timeout,
            "job_listings_collection": self.job_listings_collection,
        }


# Global configuration instances
db_config = DatabaseConfig()


def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return db_config
