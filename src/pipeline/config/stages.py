from dataclasses import dataclass
from typing import Any

from src.core.config.services import OpenAIServiceConfig


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
