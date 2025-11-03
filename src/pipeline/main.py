"""
Main entry point for the job processing pipeline using Prefect.

This module provides a command-line interface and programmatic API
for running the job processing pipeline with Prefect orchestration.
"""

import asyncio
import logging
import sys

from src.pipeline.flows import main_pipeline_flow


def setup_logging():
    """Configure root logger for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
        stream=sys.stdout,
        force=True,
    )

    # Set specific loggers to INFO level - now with src. prefix
    for logger_name in [
        "src.services.data_service",
        "src.services.openai_service",
        "src.services.web_extraction_service",
        "src.services.metrics_service",
    ]:
        logging.getLogger(logger_name).setLevel(logging.INFO)


def run():
    """Run the complete job processing pipeline."""

    async def _run_pipeline():
        await main_pipeline_flow()

    # Run the async pipeline
    asyncio.run(_run_pipeline())


if __name__ == "__main__":
    run()
