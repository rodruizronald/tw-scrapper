import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger

from pipeline.stages.stage_1 import Stage1Processor
from pipeline.utils.exceptions import (
    ConfigurationError,
    FileOperationError,
    PipelineError,
)

from .config import LoggingConfig, OpenAIConfig, PipelineConfig, StageConfig
from .models import CompanyData, ProcessingResult


class JobPipeline:
    """Main pipeline orchestrator for job data processing."""

    def __init__(self, config: PipelineConfig):
        """
        Initialize the job pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self._setup_logging()

        logger.info("🚀 Job Pipeline initialized")
        logger.info(f"📁 Output directory: {config.stage_1.output_dir}")
        logger.info(f"🤖 OpenAI model: {config.openai.model}")

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        # Remove default logger
        logger.remove()

        # Add console logging if enabled
        if self.config.logging.log_to_console:
            logger.add(
                sink=lambda msg: print(msg, end=""),
                level=self.config.logging.level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            )

        # Add file logging if enabled
        if self.config.logging.log_to_file:
            log_file = self.config.stage_1.output_dir / "pipeline.log"
            logger.add(
                sink=str(log_file),
                level=self.config.logging.level,
                rotation="10 MB",
                retention="7 days",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            )

    @classmethod
    def from_config_file(cls, config_path: Path) -> "JobPipeline":
        """
        Create pipeline from configuration file.

        Args:
            config_path: Path to configuration JSON file

        Returns:
            Initialized JobPipeline instance

        Raises:
            ConfigurationError: If configuration is invalid
            FileOperationError: If config file cannot be read
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                config_dict = json.load(f)

            config = PipelineConfig.from_dict(config_dict)
            return cls(config)

        except FileNotFoundError as e:
            raise FileOperationError(
                "read", str(config_path), "Configuration file not found"
            ) from e
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}") from e

    @classmethod
    def create_default_config(
        cls,
        output_dir: Path,
        openai_api_key: str | None = None,
        log_level: str = "INFO",
    ) -> "JobPipeline":
        """
        Create pipeline with default configuration.

        Args:
            output_dir: Output directory for pipeline results
            openai_api_key: OpenAI API key (if None, will use environment variable)
            log_level: Logging level

        Returns:
            Initialized JobPipeline instance
        """
        config = PipelineConfig(
            stage_1=StageConfig(output_dir=output_dir),
            openai=OpenAIConfig(api_key=openai_api_key),
            logging=LoggingConfig(level=log_level),
        )

        return cls(config)

    def load_companies_from_file(self, companies_file: Path) -> list[CompanyData]:
        """
        Load company data from JSON file.

        Args:
            companies_file: Path to companies JSON file

        Returns:
            List of CompanyData objects

        Raises:
            FileOperationError: If file cannot be read
            ConfigurationError: If company data is invalid
        """
        try:
            with open(companies_file, encoding="utf-8") as f:
                companies_json = json.load(f)

            companies = []
            for company_data in companies_json:
                try:
                    company = CompanyData(**company_data)
                    companies.append(company)
                except Exception as e:
                    logger.warning(f"Skipping invalid company data {company_data}: {e}")
                    continue

            logger.info(f"📋 Loaded {len(companies)} companies from {companies_file}")
            return companies

        except FileNotFoundError as e:
            raise FileOperationError(
                "read", str(companies_file), "Companies file not found"
            ) from e
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in companies file: {e}") from e
        except Exception as e:
            raise FileOperationError("read", str(companies_file), str(e)) from e

    async def run_stage_1(
        self, companies: list[CompanyData], prompt_template_path: Path
    ) -> list[ProcessingResult]:
        """
        Run Stage 1: Extract job listings from company career pages.

        Args:
            companies: List of companies to process
            prompt_template_path: Path to OpenAI prompt template

        Returns:
            List of processing results

        Raises:
            PipelineError: If stage processing fails
        """
        logger.info("🎯 Starting Stage 1: Job Listing Extraction")

        try:
            # Validate prompt template exists
            if not prompt_template_path.exists():
                raise FileOperationError(
                    "read", str(prompt_template_path), "Prompt template file not found"
                )

            # Initialize Stage 1 processor
            processor = Stage1Processor(self.config, str(prompt_template_path))

            # Process companies
            results = await processor.process_companies(companies)

            logger.success("✅ Stage 1 completed successfully")
            return results

        except Exception as e:
            logger.error(f"❌ Stage 1 failed: {e}")
            if isinstance(e, PipelineError):
                raise
            else:
                raise PipelineError(f"Stage 1 processing failed: {e}") from e

    async def run_full_pipeline(
        self, companies_file: Path, prompt_template_path: Path
    ) -> dict[str, Any]:
        """
        Run the complete pipeline (currently just Stage 1).

        Args:
            companies_file: Path to companies JSON file
            prompt_template_path: Path to OpenAI prompt template

        Returns:
            Dictionary with pipeline results and statistics
        """
        pipeline_start_time = datetime.now(UTC).astimezone()

        logger.info("🚀 Starting Job Pipeline")
        logger.info(f"📅 Start time: {pipeline_start_time.isoformat()}")

        try:
            # Load companies
            companies = self.load_companies_from_file(companies_file)

            if not companies:
                logger.warning("⚠️  No valid companies found to process")
                return {
                    "success": False,
                    "error": "No valid companies found",
                    "results": [],
                }

            # Run Stage 1
            stage_1_results = await self.run_stage_1(companies, prompt_template_path)

            # Calculate pipeline statistics
            pipeline_end_time = datetime.now(UTC).astimezone()
            total_time = (pipeline_end_time - pipeline_start_time).total_seconds()

            successful_companies = len([r for r in stage_1_results if r.success])
            failed_companies = len([r for r in stage_1_results if not r.success])
            total_jobs_found = sum(r.jobs_found for r in stage_1_results)
            total_jobs_saved = sum(r.jobs_saved for r in stage_1_results)

            # Create pipeline summary
            pipeline_summary = {
                "success": True,
                "pipeline_start_time": pipeline_start_time.isoformat(),
                "pipeline_end_time": pipeline_end_time.isoformat(),
                "total_processing_time": total_time,
                "companies_processed": len(companies),
                "companies_successful": successful_companies,
                "companies_failed": failed_companies,
                "total_jobs_found": total_jobs_found,
                "total_jobs_saved": total_jobs_saved,
                "stage_1_results": [
                    {
                        "company_name": r.company_name,
                        "success": r.success,
                        "jobs_found": r.jobs_found,
                        "jobs_saved": r.jobs_saved,
                        "processing_time": r.processing_time,
                        "error": r.error,
                        "output_path": str(r.output_path) if r.output_path else None,
                    }
                    for r in stage_1_results
                ],
            }

            # Save pipeline summary
            if self.config.stage_1.save_output:
                summary_path = self.config.stage_1.output_dir / "pipeline_summary.json"
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump(pipeline_summary, f, indent=2, ensure_ascii=False)
                logger.info(f"📊 Pipeline summary saved to: {summary_path}")

            # Log final results
            logger.info("=" * 80)
            logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"⏱️  Total time: {total_time:.2f}s")
            logger.info(f"🏢 Companies processed: {len(companies)}")
            logger.info(f"✅ Successful: {successful_companies}")
            logger.info(f"❌ Failed: {failed_companies}")
            logger.info(f"📋 Jobs found: {total_jobs_found}")
            logger.info(f"💾 Jobs saved: {total_jobs_saved}")
            logger.info("=" * 80)

            return pipeline_summary

        except Exception as e:
            pipeline_end_time = datetime.now(UTC).astimezone()
            total_time = (pipeline_end_time - pipeline_start_time).total_seconds()

            logger.error("=" * 80)
            logger.error("💥 PIPELINE FAILED")
            logger.error("=" * 80)
            logger.error(f"⏱️  Total time: {total_time:.2f}s")
            logger.error(f"❌ Error: {e}")
            logger.error("=" * 80)

            return {
                "success": False,
                "error": str(e),
                "pipeline_start_time": pipeline_start_time.isoformat(),
                "pipeline_end_time": pipeline_end_time.isoformat(),
                "total_processing_time": total_time,
                "results": [],
            }

    def get_config_summary(self) -> dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "stage_1": {
                "output_dir": str(self.config.stage_1.output_dir),
                "save_output": self.config.stage_1.save_output,
            },
            "openai": {
                "model": self.config.openai.model,
                "max_retries": self.config.openai.max_retries,
                "timeout": self.config.openai.timeout,
            },
            "logging": {
                "level": self.config.logging.level,
                "log_to_file": self.config.logging.log_to_file,
                "log_to_console": self.config.logging.log_to_console,
            },
        }
