import asyncio
import hashlib
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from loguru import logger

from parsers import ParserType
from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, JobData, ProcessingResult
from pipeline.services.file_service import FileService
from pipeline.services.html_service import HTMLExtractor
from pipeline.services.openai_service import OpenAIService
from pipeline.utils.exceptions import (
    CompanyProcessingError,
    FileOperationError,
    HTMLExtractionError,
    OpenAIProcessingError,
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
            "processing_start_time": None,  # Will store datetime
            "processing_end_time": None,  # Will store datetime
        }

    async def process_company(self, company_data: CompanyData) -> ProcessingResult:
        """
        Process a single company to extract job listings.

        Args:
            company_data: Company information and configuration

        Returns:
            Processing result with success status and metrics
        """
        start_time = time.time()
        company_name = company_data.name

        logger.info(f"🏢 Starting processing for company: {company_name}")

        try:
            # Validate company data
            self._validate_company_data(company_data)

            # Extract HTML content from career page
            html_content = await self._extract_career_page_content(company_data)

            # Parse job listings using OpenAI
            job_listings = await self._parse_job_listings(company_data, html_content)

            # Process and validate job data
            jobs = self._process_job_listings(company_data, job_listings)

            # Filter out duplicate jobs
            unique_jobs = await self._filter_duplicate_jobs(company_data, jobs)

            # Save jobs to file
            output_path = None
            if self.config.stage_1.save_output and unique_jobs:
                output_path = await self.file_service.save_jobs(
                    unique_jobs, company_name
                )

            # Update statistics
            self.stats["companies_successful"] += 1
            self.stats["total_jobs_found"] += len(jobs)
            self.stats["total_jobs_saved"] += len(unique_jobs)

            processing_time = time.time() - start_time

            result = ProcessingResult(
                success=True,
                company_name=company_name,
                jobs_found=len(jobs),
                jobs_saved=len(unique_jobs),
                output_path=output_path,
                processing_time=processing_time,
            )

            logger.success(
                f"✅ {company_name}: Found {len(jobs)} jobs, saved {len(unique_jobs)} unique jobs "
                f"in {processing_time:.2f}s"
            )

            return result

        except Exception as e:
            self.stats["companies_failed"] += 1
            processing_time = time.time() - start_time

            # Create error result
            result = ProcessingResult(
                success=False,
                company_name=company_name,
                error=str(e),
                processing_time=processing_time,
            )

            logger.error(f"❌ {company_name}: Processing failed - {e!s}")

            # Wrap in CompanyProcessingError if it's not already a pipeline error
            if not isinstance(
                e,
                CompanyProcessingError
                | HTMLExtractionError
                | OpenAIProcessingError
                | FileOperationError
                | ValidationError,
            ):
                raise CompanyProcessingError(company_name, e, "stage_1") from e

            return result

    async def process_companies(
        self, companies: list[CompanyData]
    ) -> list[ProcessingResult]:
        """
        Process multiple companies concurrently.

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

        # Process companies concurrently with semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent companies

        async def process_with_semaphore(company: CompanyData) -> ProcessingResult:
            async with semaphore:
                self.stats["companies_processed"] += 1
                return await self.process_company(company)

        # Execute all company processing tasks
        tasks = [process_with_semaphore(company) for company in enabled_companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions that weren't caught
        processed_results: list[ProcessingResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                company_name = enabled_companies[i].name
                logger.error(f"❌ Unhandled exception for {company_name}: {result}")
                processed_results.append(
                    ProcessingResult(
                        success=False,
                        company_name=company_name,
                        error=f"Unhandled exception: {result!s}",
                    )
                )
            elif isinstance(result, ProcessingResult):
                processed_results.append(result)

        self.stats["processing_end_time"] = datetime.now(UTC).astimezone()

        # Create processing summary
        if self.config.stage_1.save_output:
            summary_path = self.file_service.create_processing_summary(
                processed_results
            )
            logger.info(f"📊 Processing summary saved to: {summary_path}")

        # Log final statistics
        self._log_final_statistics(processed_results)

        return processed_results

    def _validate_company_data(self, company_data: CompanyData) -> None:
        """Validate company data before processing."""
        if not company_data.name:
            raise ValidationError("name", "", "Company name cannot be empty")

        if not company_data.career_url:
            raise ValidationError("career_url", "", "Career URL cannot be empty")

        if not company_data.job_board_selector:
            raise ValidationError(
                "job_board_selector", "[]", "Job board selector cannot be empty"
            )

        # Validate parser type
        try:
            ParserType[company_data.html_parser.upper()]
        except KeyError as e:
            raise ValidationError(
                "html_parser", company_data.html_parser, "Invalid parser type"
            ) from e

    async def _extract_career_page_content(self, company_data: CompanyData) -> str:
        """Extract HTML content from company career page."""
        parser_type = ParserType[company_data.html_parser.upper()]

        try:
            html_content = await self.html_extractor.extract_content(
                url=company_data.career_url,
                selectors=company_data.job_board_selector,
                parser_type=parser_type,
                company_name=company_data.name,
            )
            return html_content

        except HTMLExtractionError:
            raise  # Re-raise HTML extraction errors
        except Exception as e:
            raise HTMLExtractionError(
                company_data.career_url,
                f"Unexpected error during HTML extraction: {e!s}",
                company_data.name,
            ) from e

    async def _parse_job_listings(
        self, company_data: CompanyData, html_content: str
    ) -> dict[str, Any]:
        """Parse job listings from HTML content using OpenAI."""
        try:
            prompt_path = Path(self.prompt_template_path)

            job_listings = await self.openai_service.parse_job_listings(
                html_content=html_content,
                prompt_template_path=prompt_path,
                career_url=company_data.career_url,
                company_name=company_data.name,
            )

            # Validate response structure
            if not self.openai_service.validate_response_structure(job_listings):
                raise OpenAIProcessingError(
                    "Invalid response structure from OpenAI",
                    company_data.name,
                    str(job_listings),
                )

            return job_listings

        except OpenAIProcessingError:
            raise  # Re-raise OpenAI processing errors
        except Exception as e:
            raise OpenAIProcessingError(
                f"Unexpected error during OpenAI processing: {e!s}",
                company_data.name,
            ) from e

    def _process_job_listings(
        self, company_data: CompanyData, job_listings: dict[str, Any]
    ) -> list[JobData]:
        """Process and validate job listings data."""
        jobs = []
        current_timestamp = datetime.now(UTC).astimezone().isoformat()

        for job_data in job_listings.get("jobs", []):
            try:
                # Extract job information
                title = job_data.get("title", "").strip()
                url = job_data.get("url", "").strip()

                if not title or not url:
                    logger.warning(
                        f"[{company_data.name}] Skipping job with missing title or URL: {job_data}"
                    )
                    continue

                # Generate job signature for duplicate detection
                signature = self._generate_job_signature(url)

                # Create JobData object
                job = JobData(
                    title=title,
                    url=url,
                    signature=signature,
                    company=company_data.name,
                    timestamp=current_timestamp,
                )

                jobs.append(job)

            except Exception as e:
                logger.warning(
                    f"[{company_data.name}] Error processing job data {job_data}: {e}"
                )
                continue

        logger.info(f"[{company_data.name}] Processed {len(jobs)} valid jobs")
        return jobs

    def _generate_job_signature(self, url: str) -> str:
        """Generate a unique signature for a job based on its URL."""
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
            # Both are datetime objects, calculate the difference
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
