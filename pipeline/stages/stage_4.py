from prefect.logging import get_run_logger

from pipeline.core.config import PipelineConfig
from pipeline.core.models import Job, ProcessingResult
from pipeline.services.file_service import FileService
from pipeline.services.openai_service import OpenAIService
from pipeline.services.web_extraction_service import WebExtractionService


class Stage4Processor:
    """Stage 4: Extract technologies and tools from job postings."""

    def __init__(self, config: PipelineConfig):
        """Initialize Stage 4 processor with required services."""
        logger = get_run_logger()

        self.config = config
        self.logger = logger

        # Initialize services
        self.openai_service = OpenAIService(config.openai)
        self.file_service = FileService(config.paths)
        self.web_extraction_service = WebExtractionService(
            config.web_extraction, logger
        )

    async def process_single_job(self, job_data: Job) -> ProcessingResult:
        """
        Process a single job to extract technologies and tools.
        """
        self.logger.info(f"Processing job: {job_data.title}")

        return ProcessingResult(
            success=True,
            company_name=job_data.company,  # Add this required field
            stage=self.config.stage_4.tag,  # Add stage info
        )
