from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.mappers import JobRequirementsMapper
from pipeline.core.models import (
    Job,
    JobRequirements,
    WebParserConfig,
)
from pipeline.services.database_service import DatabaseService
from pipeline.services.openai_service import OpenAIRequest, OpenAIService
from pipeline.services.web_extraction_service import WebExtractionService
from pipeline.utils.exceptions import (
    DatabaseOperationError,
    OpenAIProcessingError,
    WebExtractionError,
)


class Stage3Processor:
    """Stage 3: Extract skills and responsibilities from job postings."""

    def __init__(self, config: PipelineConfig, web_parser: WebParserConfig):
        """Initialize Stage 3 processor with required services."""
        logger = get_run_logger()

        self.config = config
        self.logger = logger
        self.web_parser = web_parser

        # Initialize services
        self.openai_service = OpenAIService(config.openai)
        self.database_service = DatabaseService()
        self.web_extraction_service = WebExtractionService(
            config.web_extraction, logger
        )

        # Initialize mapper
        self.job_requirments_mapper = JobRequirementsMapper()

    async def process_jobs(self, jobs: list[Job], company_name: str) -> list[Job]:
        """
        Process multiple jobs for a company to extract skills and responsibilities.

        Args:
            jobs: List of Job objects to enrich with Stage 3 data
            company_name: Name of the company

        """
        self.logger.info(f"Processing {len(jobs)} jobs for {company_name}")

        try:
            processed_jobs = []
            failed_jobs = []

            for job in jobs:
                try:
                    # Process and enrich the job
                    enriched_job = await self.process_single_job(job)
                    processed_jobs.append(enriched_job)
                    self.logger.info(
                        f"Job {job.title} successfully processed and added to results"
                    )

                except Exception as e:
                    failed_jobs.append((job, e))
                    self.logger.error(f"Failed to process {job.title}: {e}")

            # Save all processed jobs to database
            if processed_jobs:
                try:
                    saved_count = self.database_service.save_stage_results(
                        processed_jobs, company_name, self.config.stage_3.tag
                    )
                    self.logger.info(
                        f"Saved {saved_count} processed jobs for {company_name}. "
                        f"Failed to process {len(failed_jobs)} jobs."
                    )
                except Exception as e:
                    raise DatabaseOperationError(
                        operation="save_stage_results",
                        message=str(e),
                        company_name=company_name,
                        stage=self.config.stage_3.tag,
                    ) from e
            else:
                self.logger.warning(f"No jobs to save for {company_name}")

            return processed_jobs

        except DatabaseOperationError:
            # Re-raise database errors for retry mechanism
            raise

        except Exception as e:
            self.logger.error(f"Error processing jobs for {company_name}: {e!s}")
            return []  # Return empty list instead of None

    async def process_single_job(self, job: Job) -> Job:
        """
        Process a single job to extract skills and responsibilities.

        Args:
            job: Job instance to enrich with Stage 3 data

        Returns:
            Job: Enriched job with Stage 3 skills data

        Raises:
            WebExtractionError: If HTML extraction fails
            OpenAIProcessingError: If AI processing fails
            ValueError: If job skills mapping fails
        """
        self.logger.info(f"Processing job: {job.title}")

        # Step 1: Extract job posting page content
        html_content = await self._extract_job_skills_content(job)

        # Step 2: Use OpenAI service to parse job skills
        job_requirements = await self._parse_job_skills(html_content, job)

        # Step 3: Enrich job with skills
        job.requirements = job_requirements

        return job

    async def _extract_job_skills_content(self, job: Job) -> str:
        """Extract HTML content from job posting page."""
        try:
            content = await self.web_extraction_service.extract_html_content(
                url=job.url,
                selectors=self.web_parser.job_card_selectors,
                parser_type=self.web_parser.parser_type,
                company_name=job.company,
            )
            if not content:
                raise WebExtractionError(
                    url=job.url,
                    original_error=Exception(f"No content extracted from {job.url}"),
                    company_name=job.company,
                )
            return content
        except Exception as e:
            raise WebExtractionError(
                url=job.url,
                original_error=e,
                company_name=job.company,
            ) from e

    async def _parse_job_skills(self, html_content: str, job: Job) -> JobRequirements:
        """Parse job skills from HTML content using the OpenAI service."""
        try:
            prompt_template = self.config.stage_3.prompt_template
            request = OpenAIRequest(
                system_message=self.config.stage_3.system_message,
                template_path=self.config.get_prompt_path(prompt_template),
                template_variables={
                    "html_content": html_content,
                },
                response_format=self.config.stage_3.response_format,
                context_name=job.company,
            )

            # Get raw response from OpenAI
            raw_response = await self.openai_service.process_with_template(request)

            # Process and validate job data using JobRequirementsMapper
            job_requirements = self.job_requirments_mapper.map_from_openai_response(
                raw_response
            )

            return job_requirements

        except Exception as e:
            raise OpenAIProcessingError(
                message=f"Failed to parse job skills for {job.title}: {e}",
                company_name=job.company,
            ) from e
