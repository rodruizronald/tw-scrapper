import hashlib
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, Job, ProcessingResult
from pipeline.services.file_service import FileService
from pipeline.services.openai_service import OpenAIRequest, OpenAIService
from pipeline.services.web_extraction_service import WebExtractionService
from pipeline.utils.exceptions import (
    CompanyProcessingError,
    FileOperationError,
    OpenAIProcessingError,
    ValidationError,
    WebExtractionError,
)


class Stage1Processor:
    """Stage 1: Extract job listings from company career pages."""

    def __init__(self, config: PipelineConfig):
        """
        Initialize Stage 1 processor.

        Args:
            config: Pipeline configuration
            prompt_template_path: Path to the OpenAI prompt template
        """
        logger = get_run_logger()

        self.config = config
        self.logger = logger

        # Initialize services
        self.openai_service = OpenAIService(config.openai)
        self.file_service = FileService(config.paths)
        self.web_extraction_service = WebExtractionService(
            config.web_extraction, logger
        )

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

        # Initialize result with basic information
        result = ProcessingResult(
            success=False,
            company_name=company_name,
            start_time=start_datetime,
            stage=self.config.stage_1.tag,
        )

        try:
            # Process the company
            jobs, unique_jobs, output_path = await self._execute_company_processing(
                company_data
            )

            # Build successful result
            processing_time = time.time() - start_time
            result = self._build_success_result(
                result, jobs, unique_jobs, output_path, processing_time
            )

            self.logger.info(
                f"{company_name}: Found {len(jobs)} jobs, saved {len(unique_jobs)} unique jobs "
                f"in {processing_time:.2f}s"
            )

            return result

        except Exception as e:
            # Handle all errors and build error result
            return self._build_error_result(result, e, start_time, company_name)

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
                field="company_data",
                value=str(company_data.name),
                message=f"Invalid company data for {company_data.name}: {e}",
            ) from e

    async def _extract_career_page_content(self, company_data: CompanyData) -> str:
        """Extract HTML content from company career page."""
        try:
            content = await self.web_extraction_service.extract_html_content(
                url=company_data.career_url,
                selectors=company_data.job_board_selectors,
                parser_type=company_data.parser_type,
                company_name=company_data.name,
            )
            if not content:
                raise WebExtractionError(
                    url=company_data.career_url,
                    original_error=Exception(
                        f"No content extracted from {company_data.career_url}"
                    ),
                    company_name=company_data.name,
                )
            return content
        except Exception as e:
            raise WebExtractionError(
                url=company_data.career_url,
                original_error=e,
                company_name=company_data.name,
            ) from e

    async def _parse_job_listings(
        self, company_data: CompanyData, html_content: str
    ) -> dict[str, Any]:
        """Parse job listings from HTML content using the job extraction service."""
        try:
            prompt_template = self.config.stage_1.prompt_template
            request = OpenAIRequest(
                system_message=self.config.stage_1.system_message,
                template_path=self.config.get_prompt_path(prompt_template),
                template_variables={
                    "html_content": html_content,
                    "career_url": company_data.career_url,
                },
                response_format=self.config.stage_1.response_format,
                context_name=company_data.name,
            )

            return await self.openai_service.process_with_template(request)
        except Exception as e:
            raise OpenAIProcessingError(
                message=f"Failed to parse job listings for {company_data.name}: {e}",
                company_name=company_data.name,
            ) from e

    def _process_job_listings(
        self, company_data: CompanyData, job_listings: dict[str, Any]
    ) -> list[Job]:
        """Process and validate job listings data."""
        jobs = []
        job_data = job_listings.get("jobs", [])

        for job_info in job_data:
            try:
                job = Job(
                    title=job_info.get("title", ""),
                    url=job_info.get("url", ""),
                    company=company_data.name,
                    signature=self._generate_job_signature(job_info.get("url", "")),
                    timestamp=datetime.now(UTC).isoformat(),
                    details=None,  # Stage 1 doesn't populate details
                )
                jobs.append(job)
            except Exception as e:
                self.logger.warning(
                    f"Skipping invalid job data for {company_data.name}: {e}"
                )
                continue

        return jobs

    def _generate_job_signature(self, url: str) -> str:
        """Generate a unique signature for a job URL."""
        return hashlib.sha256(url.encode()).hexdigest()

    async def _filter_duplicate_jobs(
        self, company_data: CompanyData, jobs: list[Job]
    ) -> list[Job]:
        """Filter out duplicate jobs based on historical data."""
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
            self.logger.info(
                f"Filtered out {len(duplicate_signatures)} duplicate jobs. "
                f"Keeping {len(unique_jobs)} unique jobs."
            )

        # Save current signatures for future duplicate detection
        self.file_service.save_signatures(
            current_signatures, company_data.name, "unfiltered_signatures.json"
        )

        return unique_jobs

    async def _execute_company_processing(
        self, company_data: CompanyData
    ) -> tuple[list[Job], list[Job], Path | None]:
        """Execute the main processing logic for a company."""
        company_name = company_data.name

        # Validate company data
        self._validate_company_data(company_data)
        self.logger.info("Company data validation passed")

        # Extract HTML content from career page
        html_content = await self._extract_career_page_content(company_data)

        # Parse job listings using OpenAI
        job_listings = await self._parse_job_listings(company_data, html_content)

        # Process and validate job data
        jobs = self._process_job_listings(company_data, job_listings)
        self.logger.info(f"Job data processed: {len(jobs)} jobs found")

        # Filter out duplicate jobs
        unique_jobs = await self._filter_duplicate_jobs(company_data, jobs)
        self.logger.info(
            f"Duplicate filtering complete: {len(unique_jobs)} unique jobs"
        )

        # Save jobs to file
        output_path: Path | None = None
        if unique_jobs:
            file_path: Path | None = self.file_service.save_jobs(
                unique_jobs, company_name, self.config.stage_1.tag
            )
            output_path = file_path  # Keep as Path, don't convert to str

        return jobs, unique_jobs, output_path

    def _build_success_result(
        self,
        result: ProcessingResult,
        jobs: list[Job],
        unique_jobs: list[Job],
        output_path: Path | None,
        processing_time: float,
    ) -> ProcessingResult:
        """Build a successful processing result."""
        end_datetime = datetime.now(UTC).astimezone()

        result.success = True
        result.jobs_found = len(jobs)
        result.jobs_saved = len(unique_jobs)
        result.output_path = output_path
        result.end_time = end_datetime
        result.processing_time = processing_time

        return result

    def _build_error_result(
        self,
        result: ProcessingResult,
        error: Exception,
        start_time: float,
        company_name: str,
    ) -> ProcessingResult:
        """Build an error processing result based on exception type."""
        end_datetime = datetime.now(UTC).astimezone()
        processing_time = time.time() - start_time

        result.end_time = end_datetime
        result.processing_time = processing_time

        if isinstance(error, ValidationError):
            # Non-retryable error - bad company data
            result.error = f"Validation error: {error}"
            result.error_type = "ValidationError"
            result.retryable = False
            self.logger.error(f"{company_name}: Validation failed - {error}")

        elif isinstance(error, WebExtractionError | OpenAIProcessingError):
            # Potentially retryable errors - network/API issues
            result.error = str(error)
            result.error_type = type(error).__name__
            result.retryable = True
            self.logger.error(f"{company_name}: {type(error).__name__} - {error}")

        elif isinstance(error, FileOperationError):
            # File system errors - usually retryable
            result.error = str(error)
            result.error_type = "FileOperationError"
            result.retryable = True
            self.logger.error(f"{company_name}: File operation failed - {error}")

        else:
            # Unexpected errors - mark as non-retryable by default
            result.error = f"Unexpected error: {error}"
            result.error_type = "UnexpectedError"
            result.retryable = False
            self.logger.error(f"{company_name}: Unexpected error - {error}")

            # Still raise CompanyProcessingError for upstream handling if needed
            raise CompanyProcessingError(company_name, error, "stage_1") from error

        return result
