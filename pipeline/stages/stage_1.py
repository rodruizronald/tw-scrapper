import hashlib
from pipeline.core.models import CompanyData, JobData, ProcessingResult
from typing import Any, TypedDict
from loguru import logger
from pipeline.core.config import PipelineConfig
from pipeline.services.openai_service import OpenAIService
from pipeline.services.html_service import HTMLExtractor
from pipeline.services.file_service import FileService
from datetime import UTC, datetime
import time
from pipeline.utils.exceptions import (
    CompanyProcessingError,
    HTMLExtractionError,
    OpenAIProcessingError,
    FileOperationError,
    ValidationError,
)


class ProcessingStats(TypedDict):
    """Type definition for processing statistics."""

    companies_processed: int
    companies_successful: int
    companies_failed: int
    total_jobs_found: int
    total_jobs_saved: int
    processing_start_time: datetime | None
    processing_end_time: datetime | None


class Stage1Processor:
    """Stage 1: Extract job listings from company career pages."""

    def __init__(self, config: PipelineConfig, prompt_template_path: str):
        """
        Initialize Stage 1 processor.

        Args:
            config: Pipeline configuration
            prompt_template_path: Path to the OpenAI prompt template
        """
        self.config = config
        self.prompt_template_path = prompt_template_path

        # Initialize services
        self.html_extractor = HTMLExtractor(max_retries=3, retry_delay=1.0)
        self.openai_service = OpenAIService(config.openai)
        self.file_service = FileService(config.stage_1.output_dir)

        # Processing statistics - properly typed
        self.stats: ProcessingStats = {
            "companies_processed": 0,
            "companies_successful": 0,
            "companies_failed": 0,
            "total_jobs_found": 0,
            "total_jobs_saved": 0,
            "processing_start_time": None,
            "processing_end_time": None,
        }

    async def process_single_company(
        self, company_data: CompanyData
    ) -> ProcessingResult:
        """
        Process a single company to extract job listings.

        This method is designed to be called by Prefect tasks and handles
        one company at a time with comprehensive error handling and timing.

        Args:
            company_data: Company information and configuration

        Returns:
            ProcessingResult with success status, metrics, and detailed information
        """
        start_time = time.time()
        start_datetime = datetime.now(UTC).astimezone()
        company_name = company_data.name

        logger.info(f"🏢 Starting processing for company: {company_name}")

        # Initialize result with basic information
        result = ProcessingResult(
            success=False,
            company_name=company_name,
            start_time=start_datetime,
            stage="stage_1",
        )

        try:
            # Validate company data
            self._validate_company_data(company_data)
            logger.debug(f"✅ Company data validation passed for {company_name}")

            # Extract HTML content from career page
            html_content = await self._extract_career_page_content(company_data)
            logger.debug(f"✅ HTML content extracted for {company_name}")

            # Parse job listings using OpenAI
            job_listings = await self._parse_job_listings(company_data, html_content)
            logger.debug(f"✅ Job listings parsed for {company_name}")

            # Process and validate job data
            jobs = self._process_job_listings(company_data, job_listings)
            logger.debug(
                f"✅ Job data processed for {company_name}: {len(jobs)} jobs found"
            )

            # Filter out duplicate jobs
            unique_jobs = await self._filter_duplicate_jobs(company_data, jobs)
            logger.debug(
                f"✅ Duplicate filtering complete for {company_name}: {len(unique_jobs)} unique jobs"
            )

            # Save jobs to file
            output_path = None
            if self.config.stage_1.save_output and unique_jobs:
                output_path = await self.file_service.save_jobs(
                    unique_jobs, company_name
                )
                logger.debug(f"✅ Jobs saved for {company_name}: {output_path}")

            # Calculate timing
            end_datetime = datetime.now(UTC).astimezone()
            processing_time = time.time() - start_time

            # Update result with success information
            result.success = True
            result.jobs_found = len(jobs)
            result.jobs_saved = len(unique_jobs)
            result.output_path = output_path
            result.end_time = end_datetime
            result.processing_time = processing_time

            logger.success(
                f"✅ {company_name}: Found {len(jobs)} jobs, saved {len(unique_jobs)} unique jobs "
                f"in {processing_time:.2f}s"
            )

            return result

        except ValidationError as e:
            # Non-retryable error - bad company data
            result.error = f"Validation error: {e}"
            result.error_type = "ValidationError"
            result.retryable = False
            result.end_time = datetime.now(UTC).astimezone()
            result.processing_time = time.time() - start_time

            logger.error(f"❌ {company_name}: Validation failed - {e}")
            return result

        except (HTMLExtractionError, OpenAIProcessingError) as e:
            # Potentially retryable errors - network/API issues
            result.error = str(e)
            result.error_type = type(e).__name__
            result.retryable = True
            result.end_time = datetime.now(UTC).astimezone()
            result.processing_time = time.time() - start_time

            logger.error(f"❌ {company_name}: {type(e).__name__} - {e}")
            return result

        except FileOperationError as e:
            # File system errors - usually retryable
            result.error = str(e)
            result.error_type = "FileOperationError"
            result.retryable = True
            result.end_time = datetime.now(UTC).astimezone()
            result.processing_time = time.time() - start_time

            logger.error(f"❌ {company_name}: File operation failed - {e}")
            return result

        except Exception as e:
            # Unexpected errors - mark as non-retryable by default
            result.error = f"Unexpected error: {e}"
            result.error_type = "UnexpectedError"
            result.retryable = False
            result.end_time = datetime.now(UTC).astimezone()
            result.processing_time = time.time() - start_time

            logger.error(f"❌ {company_name}: Unexpected error - {e}")

            # Still raise CompanyProcessingError for upstream handling if needed
            raise CompanyProcessingError(company_name, e, "stage_1") from e

    # Keep the original process_companies method for backward compatibility
    async def process_companies(
        self, companies: list[CompanyData]
    ) -> list[ProcessingResult]:
        """
        Process multiple companies sequentially.

        This method is kept for backward compatibility with existing code.
        For Prefect flows, use process_single_company() instead.

        Args:
            companies: List of company data to process

        Returns:
            List of processing results
        """
        self.stats["processing_start_time"] = datetime.now(UTC).astimezone()

        logger.info(f"🚀 Starting Stage 1 processing for {len(companies)} companies")

        # Filter enabled companies
        enabled_companies = [c for c in companies if c.enabled]
        disabled_count = len(companies) - len(enabled_companies)

        if disabled_count > 0:
            logger.info(f"⏭️  Skipping {disabled_count} disabled companies")

        # Process companies sequentially (for backward compatibility)
        results = []
        for company in enabled_companies:
            self.stats["companies_processed"] += 1
            result = await self.process_single_company(company)
            results.append(result)

            # Update stats
            if result.success:
                self.stats["companies_successful"] += 1
                self.stats["total_jobs_found"] += result.jobs_found
                self.stats["total_jobs_saved"] += result.jobs_saved
            else:
                self.stats["companies_failed"] += 1

        self.stats["processing_end_time"] = datetime.now(UTC).astimezone()

        # Create processing summary
        if self.config.stage_1.save_output:
            summary_path = self.file_service.create_processing_summary(results)
            logger.info(f"📊 Processing summary saved to: {summary_path}")

        # Log final statistics
        self._log_final_statistics(results)

        return results

    # All existing private methods remain unchanged
    def _validate_company_data(self, company_data: CompanyData) -> None:
        """Validate company data before processing."""
        try:
            if not company_data.name:
                raise ValueError("Company name is required")
            if not company_data.career_url:
                raise ValueError("Career URL is required")
            if not company_data.enabled:
                raise ValueError("Company is disabled")
        except Exception as e:
            raise ValidationError(
                f"Invalid company data for {company_data.name}: {e}"
            ) from e

    async def _extract_career_page_content(self, company_data: CompanyData) -> str:
        """Extract HTML content from company career page."""
        try:
            content = await self.html_extractor.extract_content(
                url=company_data.career_url,
                selectors=company_data.selectors,
                parser_type=company_data.parser_type,
            )
            if not content:
                raise HTMLExtractionError(
                    f"No content extracted from {company_data.career_url}"
                )
            return content
        except Exception as e:
            raise HTMLExtractionError(
                f"Failed to extract content from {company_data.career_url}: {e}"
            ) from e

    async def _parse_job_listings(
        self, company_data: CompanyData, html_content: str
    ) -> dict[str, Any]:
        """Parse job listings from HTML content using OpenAI."""
        try:
            result = await self.openai_service.parse_job_listings(
                html_content=html_content,
                company_name=company_data.name,
                prompt_template_path=self.prompt_template_path,
            )
            return result
        except Exception as e:
            raise OpenAIProcessingError(
                f"Failed to parse job listings for {company_data.name}: {e}"
            ) from e

    def _process_job_listings(
        self, company_data: CompanyData, job_listings: dict[str, Any]
    ) -> list[JobData]:
        """Process and validate job listings data."""
        jobs = []
        job_data = job_listings.get("jobs", [])

        for job_info in job_data:
            try:
                job = JobData(
                    title=job_info.get("title", ""),
                    url=job_info.get("url", ""),
                    company_name=company_data.name,
                    signature=self._generate_job_signature(job_info.get("url", "")),
                )
                jobs.append(job)
            except Exception as e:
                logger.warning(
                    f"Skipping invalid job data for {company_data.name}: {e}"
                )
                continue

        return jobs

    def _generate_job_signature(self, url: str) -> str:
        """Generate a unique signature for a job URL."""
        return hashlib.sha256(url.encode()).hexdigest()

    async def _filter_duplicate_jobs(
        self, company_data: CompanyData, jobs: list[JobData]
    ) -> list[JobData]:
        """Filter out duplicate jobs based on historical signatures."""
        if not jobs:
            return jobs

        # Load historical signatures
        historical_signatures = self.file_service.load_historical_signatures(
            company_data.name
        )

        # Filter out duplicates
        current_signatures = {job.signature for job in jobs}
        duplicate_signatures = current_signatures.intersection(historical_signatures)
        unique_jobs = [job for job in jobs if job.signature not in duplicate_signatures]

        if duplicate_signatures:
            logger.info(
                f"[{company_data.name}] Filtered out {len(duplicate_signatures)} duplicate jobs. "
                f"Keeping {len(unique_jobs)} unique jobs."
            )

        # Save current signatures for future duplicate detection
        if self.config.stage_1.save_output:
            await self.file_service.save_historical_signatures(
                current_signatures, company_data.name
            )

        return unique_jobs

    def _log_final_statistics(self, results: list[ProcessingResult]) -> None:
        """Log final processing statistics."""
        successful = len([r for r in results if r.success])
        failed = len([r for r in results if not r.success])
        total_time = 0.0

        # Calculate total time if both timestamps are set
        start_time = self.stats.get("processing_start_time")
        end_time = self.stats.get("processing_end_time")

        if isinstance(start_time, datetime) and isinstance(end_time, datetime):
            total_time = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info("📊 STAGE 1 PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successful companies: {successful}")
        logger.info(f"❌ Failed companies: {failed}")
        logger.info(f"📋 Total jobs found: {self.stats['total_jobs_found']}")
        logger.info(f"💾 Total jobs saved: {self.stats['total_jobs_saved']}")
        logger.info(f"⏱️  Total processing time: {total_time:.2f}s")

        if failed > 0:
            logger.warning("Failed companies:")
            for result in results:
                if not result.success:
                    logger.warning(f"  - {result.company_name}: {result.error}")

        logger.info("=" * 60)
