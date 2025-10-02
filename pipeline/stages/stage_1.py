from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.mappers import JobMapper
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
        # Initialize mapper
        self.job_mapper = JobMapper()

    async def process_single_company(self, company: CompanyData) -> list[Job]:
        """
        Process a single company to extract job listings.

        This method is designed to be called by Prefect tasks and handles
        one company at a time with comprehensive error handling and timing.

        Args:
            company: Company information and configuration

        """
        company_name = company.name

        try:
            # Process the company
            jobs, unique_jobs = await self._execute_company_processing(company)

            self.logger.info(
                f"Found {len(jobs)} jobs, saved {len(unique_jobs)} unique jobs "
            )

            return unique_jobs

        except ValidationError as e:
            # Non-retryable error - bad company data
            self.logger.error(f"Validation failed - {e}")
            return []  # Return empty list instead of None

        except (WebExtractionError, OpenAIProcessingError) as e:
            # Potentially retryable errors - network/API issues
            self.logger.error(f"{type(e).__name__} - {e}")
            # Re-raise these for Prefect retry mechanism
            raise

        except FileOperationError as e:
            # File system errors - usually retryable
            self.logger.error(f"File operation failed - {e}")
            # Re-raise these for Prefect retry mechanism
            raise

        except Exception as e:
            # Unexpected errors
            self.logger.error(f"Unexpected error - {e}")

            # Still raise CompanyProcessingError for upstream handling if needed
            raise CompanyProcessingError(
                company_name, e, self.config.stage_1.tag
            ) from e

    async def _execute_company_processing(
        self, company: CompanyData
    ) -> tuple[list[Job], list[Job]]:
        """Execute the main processing logic for a company."""
        # Extract HTML content from career page
        html_content = await self._extract_career_page_content(company)

        # Parse job listings using OpenAI
        jobs = await self._parse_job_listings(company, html_content)
        self.logger.info(f"Job data processed: {len(jobs)} jobs found")

        # Filter out duplicate jobs
        unique_jobs = await self._filter_duplicate_jobs(company, jobs)
        self.logger.info(
            f"Duplicate filtering complete: {len(unique_jobs)} unique jobs"
        )

        # Save jobs to file
        if unique_jobs:
            self.file_service.save_stage_results(
                unique_jobs, company.name, self.config.stage_1.tag
            )

        return jobs, unique_jobs

    async def _extract_career_page_content(self, company: CompanyData) -> str:
        """Extract HTML content from company career page."""
        try:
            content = await self.web_extraction_service.extract_html_content(
                url=company.career_url,
                selectors=company.job_board_selectors,
                parser_type=company.parser_type,
                company_name=company.name,
            )
            if not content:
                raise WebExtractionError(
                    url=company.career_url,
                    original_error=Exception(
                        f"No content extracted from {company.career_url}"
                    ),
                    company_name=company.name,
                )
            return content
        except Exception as e:
            raise WebExtractionError(
                url=company.career_url,
                original_error=e,
                company_name=company.name,
            ) from e

    async def _parse_job_listings(
        self, company: CompanyData, html_content: str
    ) -> list[Job]:
        """Parse job listings from HTML content using the job extraction service."""
        try:
            prompt_template = self.config.stage_1.prompt_template
            request = OpenAIRequest(
                system_message=self.config.stage_1.system_message,
                template_path=self.config.get_prompt_path(prompt_template),
                template_variables={
                    "html_content": html_content,
                    "career_url": company.career_url,
                },
                response_format=self.config.stage_1.response_format,
                context_name=company.name,
            )

            # Get raw response from OpenAI
            job_listings = await self.openai_service.process_with_template(request)

            # Process and validate job data using JobMapper
            jobs = self.job_mapper.map_from_openai_response(job_listings, company.name)

            return jobs
        except Exception as e:
            raise OpenAIProcessingError(
                message=f"Failed to parse job listings: {e}",
                company_name=company.name,
            ) from e

    async def _filter_duplicate_jobs(
        self, company: CompanyData, jobs: list[Job]
    ) -> list[Job]:
        """Filter out duplicate jobs based on historical data."""
        if not jobs:
            return jobs

        # Load historical signatures
        historical_signatures = self.file_service.load_previous_day_signatures(
            company.name
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
            current_signatures, company.name, "unfiltered_signatures.json"
        )

        return unique_jobs
