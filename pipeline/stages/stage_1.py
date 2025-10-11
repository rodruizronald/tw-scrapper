from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.mappers import JobMapper
from pipeline.core.models import CompanyData, Job
from pipeline.services.database_service import DatabaseService
from pipeline.services.openai_service import OpenAIRequest, OpenAIService
from pipeline.services.web_extraction_service import WebExtractionService
from pipeline.utils.exceptions import (
    CompanyProcessingError,
    DatabaseOperationError,
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
        self.database_service = DatabaseService()
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
            new_jobs = await self._execute_company_processing(company)

            return new_jobs

        except ValidationError as e:
            # Non-retryable error - bad company data
            self.logger.error(f"Validation failed - {e}")
            return []  # Return empty list instead of None

        except (WebExtractionError, OpenAIProcessingError) as e:
            # Potentially retryable errors - network/API issues
            self.logger.error(f"{type(e).__name__} - {e}")
            # Re-raise these for Prefect retry mechanism
            raise

        except DatabaseOperationError as e:
            # Database errors - usually retryable
            self.logger.error(f"Database operation failed - {e}")
            # Re-raise these for Prefect retry mechanism
            raise

        except Exception as e:
            # Unexpected errors
            self.logger.error(f"Unexpected error - {e}")

            # Still raise CompanyProcessingError for upstream handling if needed
            raise CompanyProcessingError(
                company_name, e, self.config.stage_1.tag
            ) from e

    async def _execute_company_processing(self, company: CompanyData) -> list[Job]:
        """Execute the main processing logic for a company."""
        # Extract HTML content from career page
        html_content = await self._extract_career_page_content(company)

        # Parse job listings using OpenAI
        found_jobs = await self._parse_job_listings(company, html_content)
        self.logger.info(f"Job data processed: {len(found_jobs)} jobs found")

        # Deactivate jobs that are no longer on the career page
        self._deactivate_missing_jobs(company, found_jobs)

        # Filter out existing jobs
        new_jobs = self._filter_existing_jobs(company, found_jobs)

        # Save jobs to database
        if new_jobs:
            try:
                saved_count = self.database_service.save_stage_results(
                    new_jobs, company.name, self.config.stage_1.tag
                )
                self.logger.info(f"Saved {saved_count} new jobs to database")
            except Exception as e:
                raise DatabaseOperationError(
                    operation="save_stage_results",
                    message=str(e),
                    company_name=company.name,
                    stage=self.config.stage_1.tag,
                ) from e

        return new_jobs

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

    def _filter_existing_jobs(self, company: CompanyData, jobs: list[Job]) -> list[Job]:
        """Filter out existing jobs and return only new ones."""
        if not jobs:
            return jobs

        try:
            # Load existing signatures from database
            existing_job_signatures = self.database_service.get_existing_signatures(
                company.name
            )
        except Exception as e:
            raise DatabaseOperationError(
                operation="get_existing_signatures",
                message=str(e),
                company_name=company.name,
                stage=self.config.stage_1.tag,
            ) from e

        # Filter out existing jobs
        current_signatures = {job.signature for job in jobs}
        duplicate_signatures = current_signatures.intersection(existing_job_signatures)
        new_jobs = [job for job in jobs if job.signature not in duplicate_signatures]

        if duplicate_signatures:
            self.logger.info(
                f"Filtered out {len(duplicate_signatures)} existing jobs. "
                f"Found {len(new_jobs)} new jobs."
            )

        return new_jobs

    def _deactivate_missing_jobs(self, company: CompanyData, jobs: list[Job]) -> None:
        """Deactivate jobs that are no longer on the career page."""
        current_signatures = {job.signature for job in jobs}
        try:
            deactivated_count = self.database_service.deactivate_missing_jobs(
                company.name, current_signatures
            )
            if deactivated_count > 0:
                self.logger.info(
                    f"Deactivated {deactivated_count} jobs no longer on career page"
                )
        except Exception as e:
            raise DatabaseOperationError(
                operation="deactivate_missing_jobs",
                message=str(e),
                company_name=company.name,
                stage=self.config.stage_1.tag,
            ) from e
