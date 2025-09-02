import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from loguru import logger

from pipeline.parsers.models import ParserType


@dataclass
class PathsConfig:
    """Configuration for file paths."""

    output_dir: str
    prompts_dir: str
    companies_file: str


@dataclass
class BrowserConfig:
    """Configuration for browser instances."""

    headless: bool
    timeout: int
    wait_until: str
    user_agent: str | None = None
    viewport: dict[str, int] | None = None
    extra_headers: dict[str, str] | None = None

    def __post_init__(self):
        """Validate browser wait_until and timeout configuration."""
        valid_wait_until = ["load", "domcontentloaded", "networkidle", "commit"]
        if self.wait_until not in valid_wait_until:
            raise ValueError(
                f"Invalid wait_until: {self.wait_until}. Must be one of {valid_wait_until}"
            )

        if self.timeout <= 0:
            raise ValueError("timeout must be positive")


@dataclass
class WebExtractionConfig:
    """Configuration for extraction operations."""

    browser_config: BrowserConfig
    max_retries: int
    retry_delay: float
    parser_type: ParserType = ParserType.DEFAULT

    def __post_init__(self):
        """Validate that max_retries and retry_delay."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        if self.retry_delay <= 0:
            raise ValueError("retry_delay must be positive")


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API integration."""

    model: str
    max_retries: int
    timeout: int
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
class OpenAIServiceConfig:
    """Configuration for OpenAI service."""

    system_message: str
    prompt_template: str
    prompt_variables: list[str]
    response_format: dict[str, Any]

    def __post_init__(self):
        """Validate OpenAI service configuration."""
        if not self.system_message or not self.system_message.strip():
            raise ValueError("system_message cannot be empty")

        if not self.prompt_template or not self.prompt_template.strip():
            raise ValueError("prompt_template cannot be empty")

        if not isinstance(self.prompt_variables, list):
            raise ValueError("prompt_variables must be a list")

        if not self.prompt_variables:
            raise ValueError("prompt_variables cannot be empty")

        if not isinstance(self.response_format, dict):
            raise ValueError("response_format must be a dictionary")

        if not self.response_format:
            raise ValueError("response_format cannot be empty")


@dataclass
class LoguruConfig:
    """Configuration for logging."""

    level: str
    log_file: str
    log_to_file: bool
    log_to_console: bool
    format_console: str
    format_file: str
    rotation: str
    retention: str

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
            logger.add(
                sink=str(output_dir / self.log_file),
                level=self.level,
                rotation=self.rotation,
                retention=self.retention,
                format=self.format_file,
            )

    def setup_console_logging(self) -> None:
        """Setup only console logging (call once at startup)."""
        logger.remove()
        if self.log_to_console:
            logger.add(
                sink=lambda msg: print(msg, end=""),
                level=self.level,
                format=self.format_console,
            )


@dataclass
class IntegrationsConfig:
    """Integrations configuration for different services."""

    openai: OpenAIConfig
    web_extraction: WebExtractionConfig
    loguru: LoguruConfig


@dataclass
class StageConfig:
    """Configuration for Stage processing."""

    name: str
    description: str
    enabled: bool
    output_dir: str
    output_file: str
    openai_service: OpenAIServiceConfig


@dataclass
class StagesConfig:
    """Configuration for all stages."""

    stage_1: StageConfig


@dataclass
class PipelineConfig:
    """Main configuration for the job pipeline."""

    name: str
    version: str
    description: str
    paths: PathsConfig
    integrations: IntegrationsConfig
    stages: StagesConfig
    project_root: Path = field(default_factory=lambda: Path.cwd())

    @property
    def openai(self) -> OpenAIConfig:
        """Get OpenAI configuration."""
        return self.integrations.openai

    @property
    def web_extraction(self) -> WebExtractionConfig:
        """Get web extraction configuration."""
        return self.integrations.web_extraction

    @property
    def loguru(self) -> LoguruConfig:
        """Get Loguru logging configuration."""
        return self.integrations.loguru

    @property
    def stage_1(self) -> StageConfig:
        """Get Stage 1 configuration."""
        return self.stages.stage_1

    @property
    def stage_1_output_dir(self) -> Path:
        """Get Stage 1 output directory with timestamp."""
        return self.get_stage_output_dir(self.stages.stage_1.output_dir)

    def get_stage_output_dir(self, stage_output_dir: str) -> Path:
        """
        Get the full output directory path for a stage with timestamp.

        Args:
            stage_output_dir: The stage's output directory name (e.g., "pipeline_stage_1")

        Returns:
            Full path to the stage output directory with timestamp
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d")
        data_output_dir = self.project_root / self.paths.output_dir / timestamp
        return data_output_dir / stage_output_dir

    def create_output_dirs(self) -> None:
        """Create output directories with timestamp for Prefect runs."""
        stage_1_output_dir = self.get_stage_output_dir(self.stages.stage_1.output_dir)
        stage_1_output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "PipelineConfig":
        """Create configuration from dictionary with proper type conversion."""
        # Convert paths
        paths_data = config_dict.get("paths", {})
        paths = PathsConfig(**paths_data)

        # Convert integrations
        integrations_data = config_dict.get("integrations", {})

        # Handle OpenAI config
        openai_data = integrations_data.get("openai", {})
        openai_config = OpenAIConfig(**openai_data)

        # Handle web extraction config with nested browser config
        web_extraction_data = integrations_data.get("web_extraction", {})
        browser_config_data = web_extraction_data.get("browser_config", {})
        browser_config = BrowserConfig(**browser_config_data)

        # Convert parser_type string to enum if needed
        parser_type_value = web_extraction_data.get("parser_type", "default")
        if isinstance(parser_type_value, str):
            parser_type = ParserType(parser_type_value)
        else:
            parser_type = parser_type_value

        web_extraction_config = WebExtractionConfig(
            browser_config=browser_config,
            max_retries=web_extraction_data.get("max_retries", 3),
            retry_delay=web_extraction_data.get("retry_delay", 1.0),
            parser_type=parser_type,
        )

        # Handle loguru config
        loguru_data = integrations_data.get("loguru", {})
        loguru_config = LoguruConfig(**loguru_data)

        integrations = IntegrationsConfig(
            openai=openai_config,
            web_extraction=web_extraction_config,
            loguru=loguru_config,
        )

        # Convert stages
        stages_data = config_dict.get("stages", {})
        stage_1_data = stages_data.get("stage_1", {})

        # Handle nested openai_service
        openai_service_data = stage_1_data.get("openai_service", {})
        openai_service = OpenAIServiceConfig(**openai_service_data)

        stage_1_config = StageConfig(
            name=stage_1_data.get("name", ""),
            description=stage_1_data.get("description", ""),
            enabled=stage_1_data.get("enabled", True),
            output_dir=stage_1_data.get("output_dir", ""),
            output_file=stage_1_data.get("output_file", ""),
            openai_service=openai_service,
        )

        stages = StagesConfig(stage_1=stage_1_config)

        # Get project root
        project_root_str = config_dict.get("project_root")
        project_root = Path(project_root_str) if project_root_str else Path.cwd()

        return cls(
            name=config_dict["name"],
            version=config_dict["version"],
            description=config_dict["description"],
            paths=paths,
            integrations=integrations,
            stages=stages,
            project_root=project_root,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "paths": {
                "output_dir": self.paths.output_dir,
                "prompts_dir": self.paths.prompts_dir,
                "companies_file": self.paths.companies_file,
            },
            "integrations": {
                "openai": {
                    "model": self.integrations.openai.model,
                    "max_retries": self.integrations.openai.max_retries,
                    "timeout": self.integrations.openai.timeout,
                    "api_key": self.integrations.openai.api_key,
                },
                "web_extraction": {
                    "browser_config": {
                        "headless": self.integrations.web_extraction.browser_config.headless,
                        "viewport": self.integrations.web_extraction.browser_config.viewport,
                        "user_agent": self.integrations.web_extraction.browser_config.user_agent,
                        "timeout": self.integrations.web_extraction.browser_config.timeout,
                        "wait_until": self.integrations.web_extraction.browser_config.wait_until,
                        "extra_headers": self.integrations.web_extraction.browser_config.extra_headers,
                    },
                    "parser_type": self.integrations.web_extraction.parser_type.value,
                    "max_retries": self.integrations.web_extraction.max_retries,
                    "retry_delay": self.integrations.web_extraction.retry_delay,
                },
                "loguru": {
                    "level": self.integrations.loguru.level,
                    "log_file": self.integrations.loguru.log_file,
                    "log_to_file": self.integrations.loguru.log_to_file,
                    "log_to_console": self.integrations.loguru.log_to_console,
                    "format_console": self.integrations.loguru.format_console,
                    "format_file": self.integrations.loguru.format_file,
                    "rotation": self.integrations.loguru.rotation,
                    "retention": self.integrations.loguru.retention,
                },
            },
            "stages": {
                "stage_1": {
                    "name": self.stages.stage_1.name,
                    "description": self.stages.stage_1.description,
                    "enabled": self.stages.stage_1.enabled,
                    "output_dir": self.stages.stage_1.output_dir,
                    "output_file": self.stages.stage_1.output_file,
                    "openai_service": {
                        "system_message": self.stages.stage_1.openai_service.system_message,
                        "prompt_template": self.stages.stage_1.openai_service.prompt_template,
                        "prompt_variables": self.stages.stage_1.openai_service.prompt_variables,
                        "response_format": self.stages.stage_1.openai_service.response_format,
                    },
                },
            },
            "project_root": str(self.project_root),
        }

    @classmethod
    def load(cls, env_file: Path | None = None) -> "PipelineConfig":
        """
        Load configuration from environment variables and YAML file.

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

        # Load pipeline.yaml configuration
        pipeline_config_file = os.getenv("PIPELINE_CONFIG_FILE", "pipeline.yaml")
        pipeline_config_path = project_root / pipeline_config_file

        if not pipeline_config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {pipeline_config_path}"
            )

        with open(pipeline_config_path, encoding="utf-8") as f:
            full_config = yaml.safe_load(f)
            pipeline_dict = full_config.get("pipeline", {})

            # Add project_root to the config dict
            pipeline_dict["project_root"] = str(project_root)

            config = cls.from_dict(pipeline_dict)

        # Create output directory if it doesn't exist
        config.create_output_dirs()

        return config

    def setup_logging(self) -> None:
        """Setup complete logging configuration for the pipeline."""
        self.integrations.loguru.setup_console_logging()

        # Use the new method to get the stage output directory
        stage_1_output_dir = self.get_stage_output_dir(self.stages.stage_1.output_dir)
        self.integrations.loguru.add_stage_logging(stage_1_output_dir)
