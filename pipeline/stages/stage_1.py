import hashlib
from datetime import UTC, datetime
from typing import Any

from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import CompanyData, Job
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

    async def process_single_company(self, company_data: CompanyData) -> None:
        """
        Process a single company to extract job listings.

        This method is designed to be called by Prefect tasks and handles
        one company at a time with comprehensive error handling and timing.

        Args:
            company_data: Company information and configuration

        """
        company_name = company_data.name

        try:
            # Process the company
            jobs, unique_jobs = await self._execute_company_processing(company_data)

            self.logger.info(
                f"Found {len(jobs)} jobs, saved {len(unique_jobs)} unique jobs "
            )

        except ValidationError as e:
            # Non-retryable error - bad company data
            self.logger.error(f"Validation failed - {e}")

        except (WebExtractionError, OpenAIProcessingError) as e:
            # Potentially retryable errors - network/API issues
            self.logger.error(f"{type(e).__name__} - {e}")

        except FileOperationError as e:
            # File system errors - usually retryable
            self.logger.error(f"File operation failed - {e}")

        except Exception as e:
            # Unexpected errors
            self.logger.error(f"Unexpected error - {e}")

            # Still raise CompanyProcessingError for upstream handling if needed
            raise CompanyProcessingError(
                company_name, e, self.config.stage_1.tag
            ) from e

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
                message=f"Invalid company data: {e}",
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
                message=f"Failed to parse job listings: {e}",
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
                self.logger.warning(f"Skipping invalid job data: {e}")
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
    ) -> tuple[list[Job], list[Job]]:
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
        if unique_jobs:
            self.file_service.save_jobs(
                unique_jobs, company_name, self.config.stage_1.tag
            )

        return jobs, unique_jobs
