"""Configuration for Company API client."""

from dataclasses import dataclass


@dataclass
class CompanyAPIConfig:
    """Configuration for Company API client."""

    base_url: str = "http://localhost:8080/api/v1"
    timeout: float = 30.0  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

    # Circuit breaker settings
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: int = 60  # seconds

    def __post_init__(self):
        """Validate configuration values."""
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        if self.retry_delay <= 0:
            raise ValueError("retry_delay must be positive")

        if self.circuit_failure_threshold <= 0:
            raise ValueError("circuit_failure_threshold must be positive")

        if self.circuit_recovery_timeout <= 0:
            raise ValueError("circuit_recovery_timeout must be positive")
