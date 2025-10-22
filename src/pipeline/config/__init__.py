"""
Pipeline configuration module.

This module provides configuration classes for the job processing pipeline,
including main pipeline settings and individual stage configurations.
"""

from .pipeline import PipelineConfig
from .stages import StageConfig, StagesConfig

__all__ = [
    "PipelineConfig",
    "StageConfig",
    "StagesConfig",
]
