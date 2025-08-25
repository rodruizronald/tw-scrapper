import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StageConfig:
    """Configuration for Stage 1 processing."""

    output_dir: Path
    save_output: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API integration."""

    model: str = "gpt-4o-mini"
    max_retries: int = 3
    timeout: int = 30
    api_key: str | None = None

    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide api_key in config."
            )


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True

    def __post_init__(self):
        """Validate logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level: {self.level}. Must be one of {valid_levels}"
            )
        self.level = self.level.upper()


@dataclass
class PipelineConfig:
    """Main configuration for the job pipeline."""

    stage_1: StageConfig
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def validate(self) -> None:
        """Validate the entire configuration."""
        # Stage 1 validation
        if not self.stage_1.output_dir.exists():
            raise ValueError(
                f"Output directory does not exist: {self.stage_1.output_dir}"
            )

        # OpenAI validation
        if not self.openai.api_key:
            raise ValueError("OpenAI API key is required")

        # Additional validations can be added here

    @classmethod
    def from_dict(cls, config_dict: dict) -> "PipelineConfig":
        """Create configuration from dictionary."""
        stage_1_config = StageConfig(**config_dict.get("stage_1", {}))
        openai_config = OpenAIConfig(**config_dict.get("openai", {}))
        logging_config = LoggingConfig(**config_dict.get("logging", {}))

        config = cls(
            stage_1=stage_1_config, openai=openai_config, logging=logging_config
        )

        config.validate()
        return config

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "stage_1": {
                "output_dir": str(self.stage_1.output_dir),
                "save_output": self.stage_1.save_output,
            },
            "openai": {
                "model": self.openai.model,
                "max_retries": self.openai.max_retries,
                "timeout": self.openai.timeout,
            },
            "logging": {
                "level": self.logging.level,
                "log_to_file": self.logging.log_to_file,
                "log_to_console": self.logging.log_to_console,
            },
        }
