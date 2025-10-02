from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.mappers import JobDetailsMapper
from pipeline.core.models import (
    Job,
    JobDetails,
    WebParserConfig,
)
from pipeline.services.file_service import FileService
from pipeline.services.openai_service import OpenAIRequest, OpenAIService
from pipeline.services.web_extraction_service import WebExtractionService
from pipeline.utils.exceptions import OpenAIProcessingError, WebExtractionError


class Stage2Processor:
    """Stage 2: Extract job eligibility and metadata from individual job postings."""

    def __init__(self, config: PipelineConfig, web_parser: WebParserConfig):
        """Initialize Stage 2 processor with required services."""
        logger = get_run_logger()

        self.config = config
        self.logger = logger
        self.web_parser = web_parser

        # Initialize services
        self.openai_service = OpenAIService(config.openai)
        self.file_service = FileService(config.paths)
        self.web_extraction_service = WebExtractionService(
            config.web_extraction, logger
        )

        # Initialize mapper
        self.job_details_mapper = JobDetailsMapper()

    async def process_jobs(self, jobs: list[Job], company_name: str) -> list[Job]:
        """
        Process multiple jobs for a company to extract eligibility and metadata.

        Args:
            jobs: List of Job objects to enrich with Stage 2 data
            company_name: Name of the company

        """
        self.logger.info(f"Processing {len(jobs)} jobs for {company_name}")

        try:
            eligible_jobs = []
            failed_jobs = []
            ineligible_jobs_count = 0

            for job in jobs:
                try:
                    # Process and enrich the job
                    enriched_job = await self.process_single_job(job)

                    if enriched_job.is_eligible:
                        eligible_jobs.append(enriched_job)
                        self.logger.info(
                            f"Job {job.title} is eligible and added to results"
                        )
                    else:
                        ineligible_jobs_count += 1
                        self.logger.info(
                            f"Job {job.title} did not meet eligibility criteria"
                        )

                except Exception as e:
                    failed_jobs.append((job, e))
                    self.logger.error(f"Failed to process {job.title}: {e}")

            # Save eligible jobs only
            if eligible_jobs:
                self.file_service.save_stage_results(
                    eligible_jobs, company_name, self.config.stage_2.tag
                )
                self.logger.info(
                    f"Saved {len(eligible_jobs)} eligible jobs for {company_name}. "
                    f"Filtered out {ineligible_jobs_count} ineligible jobs. "
                    f"Failed to process {len(failed_jobs)} jobs."
                )
            else:
                self.logger.warning(f"No eligible jobs found for {company_name}")

            return eligible_jobs

        except Exception as e:
            self.logger.error(f"Error processing jobs for {company_name}: {e!s}")
            return []  # Return empty list instead of None

    async def process_single_job(self, job: Job) -> Job:
        """
        Process a single job to extract job eligibility and metadata.

        Args:
            job: Job instance to enrich with Stage 2 data

        Returns:
            Job: Enriched job with Stage 2 details

        Raises:
            WebExtractionError: If HTML extraction fails
            OpenAIProcessingError: If AI processing fails
            ValueError: If job details mapping fails
        """
        self.logger.info(f"Processing job: {job.title}")

        # Step 1: Extract job posting page content
        html_content = await self._extract_job_details_content(job)

        # Step 2: Use OpenAI service to parse job posting
        job_details = await self._parse_job_details(html_content, job)

        # Step 3: Enrich job with details
        job.details = job_details

        return job

    async def _extract_job_details_content(self, job: Job) -> str:
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

    async def _parse_job_details(self, html_content: str, job: Job) -> JobDetails:
        """Parse job details from HTML content using the OpenAI service."""
        try:
            prompt_template = self.config.stage_2.prompt_template
            request = OpenAIRequest(
                system_message=self.config.stage_2.system_message,
                template_path=self.config.get_prompt_path(prompt_template),
                template_variables={
                    "html_content": html_content,
                },
                response_format=self.config.stage_2.response_format,
                context_name=job.company,
            )

            # Get raw response from OpenAI
            raw_response = await self.openai_service.process_with_template(request)

            # Process and validate job data using JobDetailsMapper
            job_details = self.job_details_mapper.map_from_openai_response(raw_response)

            return job_details

        except Exception as e:
            raise OpenAIProcessingError(
                message=f"Failed to parse job details for {job.title}: {e}",
                company_name=job.company,
            ) from e
