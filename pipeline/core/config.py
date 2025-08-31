import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from pipeline.services.extraction_service import BrowserConfig, ExtractionConfig


@dataclass
class StageConfig:
    """Configuration for Stage processing."""

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

    def add_stage_logging(self, output_dir: Path) -> None:
        """Add logging for a specific stage without removing existing loggers."""
        if self.log_to_file and output_dir:
            log_file = output_dir / "stage.log"
            logger.add(
                sink=str(log_file),
                level=self.level,
                rotation="10 MB",
                retention="7 days",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            )

    def setup_console_logging(self) -> None:
        """Setup only console logging (call once at startup)."""
        logger.remove()
        if self.log_to_console:
            logger.add(
                sink=lambda msg: print(msg, end=""),
                level=self.level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            )


@dataclass
class PrefectConfig:
    """Prefect-specific configuration."""

    max_concurrent_companies: int = 3
    flow_timeout_seconds: int = 3600  # 1 hour
    task_timeout_seconds: int = 300  # 5 minutes
    default_retries: int = 2
    retry_delay_seconds: int = 30
    log_level: str = "INFO"

    def __post_init__(self):
        """Validate Prefect configuration."""
        if self.max_concurrent_companies < 1:
            raise ValueError("max_concurrent_companies must be at least 1")

        if self.flow_timeout_seconds < 60:
            raise ValueError("flow_timeout_seconds must be at least 60 seconds")

        if self.task_timeout_seconds < 30:
            raise ValueError("task_timeout_seconds must be at least 30 seconds")


@dataclass
class PipelineConfig:
    """Main configuration for the job pipeline."""

    stage_1: StageConfig
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    prefect: PrefectConfig = field(default_factory=PrefectConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)

    # Project paths (for Prefect integration)
    project_root: Path = field(default_factory=lambda: Path.cwd())
    input_dir: Path = field(default_factory=lambda: Path("input"))
    output_dir: Path = field(default_factory=lambda: Path("data"))

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

        # Project paths validation
        if not self.project_root.exists():
            raise ValueError(
                f"Project root directory does not exist: {self.project_root}"
            )

        if not self.input_dir.exists():
            raise ValueError(f"Input directory does not exist: {self.input_dir}")

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_dict(cls, config_dict: dict) -> "PipelineConfig":
        """Create configuration from dictionary."""
        stage_1_config = StageConfig(**config_dict.get("stage_1", {}))
        openai_config = OpenAIConfig(**config_dict.get("openai", {}))
        logging_config = LoggingConfig(**config_dict.get("logging", {}))
        prefect_config = PrefectConfig(**config_dict.get("prefect", {}))
        extraction_config = ExtractionConfig(**config_dict.get("extraction", {}))

        # Handle project paths
        project_root = Path(config_dict.get("project_root", Path.cwd()))
        input_dir = Path(config_dict.get("input_dir", "input"))
        output_dir = Path(config_dict.get("output_dir", "data"))

        config = cls(
            stage_1=stage_1_config,
            openai=openai_config,
            logging=logging_config,
            prefect=prefect_config,
            extraction=extraction_config,
            project_root=project_root,
            input_dir=input_dir,
            output_dir=output_dir,
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
                "api_key": self.openai.api_key,  # Include for serialization
            },
            "logging": {
                "level": self.logging.level,
                "log_to_file": self.logging.log_to_file,
                "log_to_console": self.logging.log_to_console,
            },
            "prefect": {
                "max_concurrent_companies": self.prefect.max_concurrent_companies,
                "flow_timeout_seconds": self.prefect.flow_timeout_seconds,
                "task_timeout_seconds": self.prefect.task_timeout_seconds,
                "default_retries": self.prefect.default_retries,
                "retry_delay_seconds": self.prefect.retry_delay_seconds,
                "log_level": self.prefect.log_level,
            },
            "extraction": {
                "browser_config": {
                    "headless": self.extraction.browser_config.headless,
                    "timeout": self.extraction.browser_config.timeout,
                    "wait_until": self.extraction.browser_config.wait_until,
                    "user_agent": self.extraction.browser_config.user_agent,
                },
                "retry_on_failure": self.extraction.retry_on_failure,
                "max_retries": self.extraction.max_retries,
                "retry_delay": self.extraction.retry_delay,
            },
            "project_root": str(self.project_root),
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
        }

    @classmethod
    def load_from_env(cls, env_file: Path | None = None) -> "PipelineConfig":
        """
        Load configuration from environment variables.

        This method provides enhanced environment loading for Prefect integration
        while maintaining backward compatibility with existing usage.

        Args:
            env_file: Optional path to .env file

        Returns:
            Configured PipelineConfig instance
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env file in current directory or parent directories
            current_dir = Path.cwd()
            for parent in [current_dir, *list(current_dir.parents)]:
                env_path = parent / ".env"
                if env_path.exists():
                    load_dotenv(env_path)
                    break

        # Get project root (directory containing this file's parent's parent)
        project_root = Path(__file__).parent.parent.parent

        # Create output directory with timestamp for Prefect runs
        timestamp = datetime.now(UTC).strftime("%Y%m%d")
        output_dir = project_root / "data" / timestamp

        # Create Stage 1 configuration
        stage_1_output_dir = output_dir / "pipeline_stage_1"
        stage_1_config = StageConfig(
            output_dir=stage_1_output_dir,
            save_output=os.getenv("STAGE_1_SAVE_OUTPUT", "true").lower() == "true",
        )

        # Create OpenAI configuration
        openai_config = OpenAIConfig(
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
            timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        # Create Logging configuration
        logging_config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            log_to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true",
            log_to_console=os.getenv("LOG_TO_CONSOLE", "true").lower() == "true",
        )

        # Create Prefect configuration
        prefect_config = PrefectConfig(
            max_concurrent_companies=int(os.getenv("PREFECT_MAX_CONCURRENT", "3")),
            flow_timeout_seconds=int(os.getenv("PREFECT_FLOW_TIMEOUT", "3600")),
            task_timeout_seconds=int(os.getenv("PREFECT_TASK_TIMEOUT", "300")),
            default_retries=int(os.getenv("PREFECT_DEFAULT_RETRIES", "2")),
            retry_delay_seconds=int(os.getenv("PREFECT_RETRY_DELAY", "30")),
            log_level=os.getenv("PREFECT_LOG_LEVEL", "INFO"),
        )

        # Create Extraction configuration
        extraction_config = ExtractionConfig(
            browser_config=BrowserConfig(
                headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
                timeout=int(os.getenv("BROWSER_TIMEOUT", "30000")),
                wait_until=os.getenv("BROWSER_WAIT_UNTIL", "domcontentloaded"),
                user_agent=os.getenv("BROWSER_USER_AGENT", None),
            ),
            retry_on_failure=os.getenv(
                "WEB_EXTRACTION_RETRY_ON_FAILURE", "false"
            ).lower()
            == "true",
            max_retries=int(os.getenv("WEB_EXTRACTION_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("WEB_EXTRACTION_RETRY_DELAY", "1.0")),
        )

        config = cls(
            stage_1=stage_1_config,
            openai=openai_config,
            logging=logging_config,
            prefect=prefect_config,
            extraction=extraction_config,
            project_root=project_root,
            input_dir=project_root / "input",
            output_dir=output_dir,
        )

        config.validate()
        return config

    def setup_logging(self) -> None:
        """Setup complete logging configuration for the pipeline."""
        self.logging.setup_console_logging()

        if self.stage_1 is not None:
            self.logging.add_stage_logging(self.stage_1.output_dir)

    # Backward compatibility methods
    @property
    def stage_1_config(self) -> StageConfig:
        """Backward compatibility property."""
        return self.stage_1

    @property
    def openai_config(self) -> OpenAIConfig:
        """Backward compatibility property."""
        return self.openai

    @property
    def logging_config(self) -> LoggingConfig:
        """Backward compatibility property."""
        return self.logging
