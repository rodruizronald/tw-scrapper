from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import JobData, ProcessingResult
from pipeline.services.file_service import FileService
from pipeline.services.openai_service import OpenAIService
from pipeline.services.web_extraction_service import WebExtractionService


class Stage2Processor:
    """Stage 2: Extract job eligibility and metadata from individual job postings."""

    def __init__(self, config: PipelineConfig):
        """Initialize Stage 2 processor with required services."""
        logger = get_run_logger()

        self.config = config
        self.logger = logger

        # Initialize services
        self.openai_service = OpenAIService(config.openai)
        self.file_service = FileService(config.paths)
        self.web_extraction_service = WebExtractionService(
            config.web_extraction, logger
        )

    async def process_single_job(self, job_data: JobData) -> ProcessingResult:
        """
        Process a single job to extract job eligibility and metadata.

        Args:
            job_data (JobData): Job data containing job details.
        """
        self.logger.info(f"Processing job: {job_data.title}")

        return ProcessingResult(
            success=True,
            company_name=job_data.company,  # Add this required field
            stage=self.config.stage_2.tag,  # Add stage info
        )
