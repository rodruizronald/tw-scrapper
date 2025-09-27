import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from pipeline.parsers.models import ParserType

##
## Stages Configuration
##


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
class StageConfig:
    """Configuration for Stage processing."""

    name: str
    tag: str
    description: str
    enabled: bool
    openai_service: OpenAIServiceConfig

    @property
    def system_message(self) -> str:
        """Get OpenAI service system message."""
        return self.openai_service.system_message

    @property
    def prompt_template(self) -> str:
        """Get OpenAI service prompt template."""
        return self.openai_service.prompt_template

    @property
    def prompt_variables(self) -> list[str]:
        """Get OpenAI service prompt variables."""
        return self.openai_service.prompt_variables

    @property
    def response_format(self) -> dict[str, Any]:
        """Get OpenAI service response format."""
        return self.openai_service.response_format


@dataclass
class StagesConfig:
    """Configuration for all stages."""

    stage_1: StageConfig
    stage_2: StageConfig
    stage_3: StageConfig
    stage_4: StageConfig

    def get_enabled_stage_tags(self) -> list[str]:
        """
        Get a list of all enabled stages from the configuration.

        Returns:
            List of enabled stage tags (e.g., ["stage_1", "stage_2"])
        """
        enabled_stages = []

        if self.stage_1.enabled:
            enabled_stages.append(self.stage_1.tag)

        if self.stage_2.enabled:
            enabled_stages.append(self.stage_2.tag)

        if self.stage_3.enabled:
            enabled_stages.append(self.stage_3.tag)

        if self.stage_4.enabled:
            enabled_stages.append(self.stage_4.tag)

        return enabled_stages


##
## System Paths Configuration
##


@dataclass
class StageOutputPatterns:
    """Configuration for stage output patterns."""

    output_dir: str
    output_file: str


@dataclass
class PathsConfig:
    """Configuration for file paths."""

    output_dir: Path
    prompts_dir: Path
    companies_file: Path
    stage_output_patterns: StageOutputPatterns
    project_root: Path = field(default_factory=lambda: Path.cwd())

    def initialize_paths(self, timestamp: str) -> None:
        """Convert relative paths to absolute paths using project_root."""
        self.output_dir = self.project_root / self.output_dir
        self.prompts_dir = self.project_root / self.prompts_dir
        self.companies_file = self.project_root / self.companies_file

        # Create the timestamped output directory (this will be the base for FileService)
        timestamped_output_dir = self.project_root / self.output_dir / timestamp
        timestamped_output_dir.mkdir(parents=True, exist_ok=True)

        # Update the output_dir to include timestamp for FileService compatibility
        self.output_dir = timestamped_output_dir

    def get_stage_output_filename(self, stage_tag: str) -> str:
        """
        Get the full path to a stage's output file.

        Args:
            stage_tag: The stage tag (e.g., "stage_1")
            timestamp: The timestamp string (e.g., "20241201")

        Returns:
            Full path to the stage's output file
        """
        return self.stage_output_patterns.output_file.format(stage_tag=stage_tag)


##
## Intergrations Configuration
##


@dataclass
class BrowserConfig:
    """Configuration for browser instances."""

    headless: bool
    timeout: int  # ms
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
    retry_delay: float  # seconds
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
    timeout: int  # seconds
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
class IntegrationsConfig:
    """Integrations configuration for different services."""

    openai: OpenAIConfig
    web_extraction: WebExtractionConfig


##
## Pipeline Configuration
##


@dataclass
class PipelineConfig:
    """Main configuration for the job pipeline."""

    name: str
    version: str
    description: str
    paths: PathsConfig
    integrations: IntegrationsConfig
    stages: StagesConfig

    @classmethod
    def _create_stage_config(cls, stage_data: dict[str, Any]) -> StageConfig:
        """
        Create a StageConfig from stage data dictionary.

        Args:
            stage_data: Dictionary containing stage configuration data

        Returns:
            Configured StageConfig instance
        """
        openai_service_data = stage_data.get("openai_service", {})
        openai_service = OpenAIServiceConfig(**openai_service_data)

        return StageConfig(
            name=stage_data.get("name", ""),
            tag=stage_data.get("tag", ""),
            description=stage_data.get("description", ""),
            enabled=stage_data.get("enabled", True),
            openai_service=openai_service,
        )

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "PipelineConfig":
        """Create configuration from dictionary with proper type conversion."""
        # Convert paths
        paths_data = config_dict.get("paths", {})
        stage_output_patterns_data = paths_data.get("stage_output_patterns", {})
        stage_output_patterns = StageOutputPatterns(**stage_output_patterns_data)

        paths = PathsConfig(
            output_dir=Path(paths_data.get("output_dir", "data")),
            prompts_dir=Path(paths_data.get("prompts_dir", "prompts")),
            companies_file=Path(paths_data.get("companies_file", "companies.yaml")),
            stage_output_patterns=stage_output_patterns,
        )

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

        integrations = IntegrationsConfig(
            openai=openai_config,
            web_extraction=web_extraction_config,
        )

        # Convert stages
        stages_data = config_dict.get("stages", {})
        stage_1_data = stages_data.get("stage_1", {})
        stage_2_data = stages_data.get("stage_2", {})
        stage_3_data = stages_data.get("stage_3", {})
        stage_4_data = stages_data.get("stage_4", {})

        # Create stage configurations using helper method
        stage_1_config = cls._create_stage_config(stage_1_data)
        stage_2_config = cls._create_stage_config(stage_2_data)
        stage_3_config = cls._create_stage_config(stage_3_data)
        stage_4_config = cls._create_stage_config(stage_4_data)

        stages = StagesConfig(
            stage_1=stage_1_config,
            stage_2=stage_2_config,
            stage_3=stage_3_config,
            stage_4=stage_4_config,
        )

        return cls(
            name=config_dict["name"],
            version=config_dict["version"],
            description=config_dict["description"],
            paths=paths,
            integrations=integrations,
            stages=stages,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "paths": {
                "output_dir": str(self.paths.output_dir),
                "prompts_dir": str(self.paths.prompts_dir),
                "companies_file": str(self.paths.companies_file),
                "project_root": str(self.paths.project_root),
                "stage_output_patterns": {
                    "output_dir": self.paths.stage_output_patterns.output_dir,
                    "output_file": self.paths.stage_output_patterns.output_file,
                },
            },
            "integrations": {
                "openai": {
                    "model": self.openai.model,
                    "max_retries": self.openai.max_retries,
                    "timeout": self.openai.timeout,
                    "api_key": self.openai.api_key,
                },
                "web_extraction": {
                    "browser_config": {
                        "headless": self.web_extraction.browser_config.headless,
                        "viewport": self.web_extraction.browser_config.viewport,
                        "user_agent": self.web_extraction.browser_config.user_agent,
                        "timeout": self.web_extraction.browser_config.timeout,
                        "wait_until": self.web_extraction.browser_config.wait_until,
                        "extra_headers": self.web_extraction.browser_config.extra_headers,
                    },
                    "parser_type": self.web_extraction.parser_type.value,
                    "max_retries": self.web_extraction.max_retries,
                    "retry_delay": self.web_extraction.retry_delay,
                },
            },
            "stages": {
                "stage_1": {
                    "name": self.stage_1.name,
                    "tag": self.stage_1.tag,
                    "description": self.stage_1.description,
                    "enabled": self.stage_1.enabled,
                    "openai_service": {
                        "system_message": self.stage_1.openai_service.system_message,
                        "prompt_template": self.stage_1.openai_service.prompt_template,
                        "prompt_variables": self.stage_1.openai_service.prompt_variables,
                        "response_format": self.stage_1.openai_service.response_format,
                    },
                },
                "stage_2": {
                    "name": self.stage_2.name,
                    "tag": self.stage_2.tag,
                    "description": self.stage_2.description,
                    "enabled": self.stage_2.enabled,
                    "openai_service": {
                        "system_message": self.stage_2.openai_service.system_message,
                        "prompt_template": self.stage_2.openai_service.prompt_template,
                        "prompt_variables": self.stage_2.openai_service.prompt_variables,
                        "response_format": self.stage_2.openai_service.response_format,
                    },
                },
                "stage_3": {
                    "name": self.stage_3.name,
                    "tag": self.stage_3.tag,
                    "description": self.stage_3.description,
                    "enabled": self.stage_3.enabled,
                    "openai_service": {
                        "system_message": self.stage_3.openai_service.system_message,
                        "prompt_template": self.stage_3.openai_service.prompt_template,
                        "prompt_variables": self.stage_3.openai_service.prompt_variables,
                        "response_format": self.stage_3.openai_service.response_format,
                    },
                },
                "stage_4": {
                    "name": self.stage_4.name,
                    "tag": self.stage_4.tag,
                    "description": self.stage_4.description,
                    "enabled": self.stage_4.enabled,
                    "openai_service": {
                        "system_message": self.stage_4.openai_service.system_message,
                        "prompt_template": self.stage_4.openai_service.prompt_template,
                        "prompt_variables": self.stage_4.openai_service.prompt_variables,
                        "response_format": self.stage_4.openai_service.response_format,
                    },
                },
            },
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
            config = cls.from_dict(pipeline_dict)

        config.paths.project_root = project_root
        return config

    def get_prompt_path(self, prompt_filename: str) -> Path:
        """
        Get the full path to a prompt template file.

        Args:
            prompt_filename: Name of the prompt file (e.g., "job_extraction.md")

        Returns:
            Full path to the prompt template file
        """
        return self.paths.prompts_dir / prompt_filename

    def initialize_paths(self) -> None:
        """Initialize all paths using the project root and stages configuration."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d")
        # Initialize paths with stages configuration
        self.paths.initialize_paths(timestamp)

    @property
    def companies_file_path(self) -> Path:
        """Get the full path to the companies file."""
        return self.paths.companies_file

    @property
    def openai(self) -> OpenAIConfig:
        """Get OpenAI configuration."""
        return self.integrations.openai

    @property
    def web_extraction(self) -> WebExtractionConfig:
        """Get web extraction configuration."""
        return self.integrations.web_extraction

    @property
    def stage_1(self) -> StageConfig:
        """Get Stage 1 configuration."""
        return self.stages.stage_1

    @property
    def stage_2(self) -> StageConfig:
        """Get Stage 2 configuration."""
        return self.stages.stage_2

    @property
    def stage_3(self) -> StageConfig:
        """Get Stage 3 configuration."""
        return self.stages.stage_3

    @property
    def stage_4(self) -> StageConfig:
        """Get Stage 4 configuration."""
        return self.stages.stage_4
