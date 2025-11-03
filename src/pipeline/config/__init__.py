"""
Pipeline configuration module.

This module provides configuration classes for the job processing pipeline,
including main pipeline settings and individual stage configurations.
"""

from src.pipeline.config.pipeline import PipelineConfig
from src.pipeline.config.stages import StageConfig, StagesConfig

__all__ = [
    "PipelineConfig",
    "StageConfig",
    "StagesConfig",
]
