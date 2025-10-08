"""
Configuration settings for the persistence layer.

This module provides configuration management for database connections
and persistence layer settings.
"""

import os
from dataclasses import dataclass, field
from typing import Any


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
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/?authSource={self.auth_source}"
        else:
            return f"mongodb://{self.host}:{self.port}/"

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


@dataclass
class RepositoryConfig:
    """Repository layer configuration settings."""

    # Query limits
    default_query_limit: int = field(
        default_factory=lambda: int(os.getenv("REPO_DEFAULT_QUERY_LIMIT", "100"))
    )
    max_query_limit: int = field(
        default_factory=lambda: int(os.getenv("REPO_MAX_QUERY_LIMIT", "1000"))
    )

    # Cleanup settings
    cleanup_enabled: bool = field(
        default_factory=lambda: os.getenv("REPO_CLEANUP_ENABLED", "true").lower()
        == "true"
    )
    cleanup_days: int = field(
        default_factory=lambda: int(os.getenv("REPO_CLEANUP_DAYS", "30"))
    )

    # Batch operation settings
    batch_size: int = field(
        default_factory=lambda: int(os.getenv("REPO_BATCH_SIZE", "100"))
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "default_query_limit": self.default_query_limit,
            "max_query_limit": self.max_query_limit,
            "cleanup_enabled": self.cleanup_enabled,
            "cleanup_days": self.cleanup_days,
            "batch_size": self.batch_size,
        }


# Global configuration instances
db_config = DatabaseConfig()
repo_config = RepositoryConfig()


def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return db_config


def get_repository_config() -> RepositoryConfig:
    """Get repository configuration."""
    return repo_config


def print_config_summary():
    """Print a summary of current configuration."""
    print("=== Database Configuration ===")
    config_dict = db_config.to_dict()
    for key, value in config_dict.items():
        if "password" in key.lower() or "connection_string" in key.lower():
            # Mask sensitive information
            print(f"{key}: {'*' * len(str(value)) if value else None}")
        else:
            print(f"{key}: {value}")

    print("\n=== Repository Configuration ===")
    repo_dict = repo_config.to_dict()
    for key, value in repo_dict.items():
        print(f"{key}: {value}")


def validate_config() -> tuple[bool, list[str]]:
    """
    Validate configuration settings.

    Returns:
        tuple[bool, list[str]]: (is_valid, list_of_errors)
    """
    errors = []

    # Validate database config
    if not db_config.host:
        errors.append("MONGO_HOST is required")

    if db_config.port <= 0 or db_config.port > 65535:
        errors.append("MONGO_PORT must be between 1 and 65535")

    if not db_config.database:
        errors.append("MONGO_DATABASE is required")

    if db_config.connection_timeout <= 0:
        errors.append("MONGO_CONNECTION_TIMEOUT must be positive")

    if db_config.server_selection_timeout <= 0:
        errors.append("MONGO_SERVER_SELECTION_TIMEOUT must be positive")

    # Validate repository config
    if repo_config.default_query_limit <= 0:
        errors.append("REPO_DEFAULT_QUERY_LIMIT must be positive")

    if repo_config.max_query_limit <= 0:
        errors.append("REPO_MAX_QUERY_LIMIT must be positive")

    if repo_config.default_query_limit > repo_config.max_query_limit:
        errors.append(
            "REPO_DEFAULT_QUERY_LIMIT cannot be greater than REPO_MAX_QUERY_LIMIT"
        )

    if repo_config.cleanup_days <= 0:
        errors.append("REPO_CLEANUP_DAYS must be positive")

    if repo_config.batch_size <= 0:
        errors.append("REPO_BATCH_SIZE must be positive")

    return len(errors) == 0, errors
