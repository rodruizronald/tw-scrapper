from pathlib import Path
from typing import Any

from loguru import logger

from pipeline.services.openai_service import OpenAIRequest, OpenAIService


class JobExtractionService:
    """Domain-specific service for job listing extraction using OpenAI."""

    def __init__(self, openai_service: OpenAIService):
        """
        Initialize job extraction service.

        Args:
            openai_service: Generic OpenAI service instance
        """
        self.openai_service = openai_service

    async def parse_job_listings(
        self,
        html_content: str,
        prompt_template_path: Path,
        career_url: str,
        company_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Parse job listings from HTML content using OpenAI.

        Args:
            html_content: HTML content to parse
            prompt_template_path: Path to the prompt template file
            career_url: Career page URL for context
            company_name: Company name for logging context

        Returns:
            Dictionary containing parsed job data

        Raises:
            OpenAIProcessingError: If OpenAI processing fails
            FileOperationError: If prompt template cannot be read
        """
        request = OpenAIRequest(
            system_message="You extract job href links from HTML content.",
            template_path=prompt_template_path,
            template_variables={
                "html_content": html_content,
                "career_url": career_url,
            },
            context_name=company_name,
            response_validator=self._validate_job_response,
        )

        return await self.openai_service.process_with_template(request)

    async def extract_job_details(
        self,
        job_html_content: str,
        prompt_template_path: Path,
        job_url: str,
        company_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Extract detailed job information from individual job page HTML.

        Args:
            job_html_content: HTML content of individual job page
            prompt_template_path: Path to the job details prompt template
            job_url: URL of the job posting
            company_name: Company name for logging context

        Returns:
            Dictionary containing detailed job information
        """
        request = OpenAIRequest(
            system_message="You extract job descriptions, eligibility information, and basic metadata from HTML content.",
            template_path=prompt_template_path,
            template_variables={
                "html_content": job_html_content,
                "job_url": job_url,
            },
            context_name=company_name,
            response_validator=self._validate_job_details_response,
        )

        return await self.openai_service.process_with_template(request)

    async def extract_skills_and_technologies(
        self,
        job_description: str,
        prompt_template_path: Path,
        company_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Extract skills and technologies from job description.

        Args:
            job_description: Job description text
            prompt_template_path: Path to the skills extraction prompt template
            company_name: Company name for logging context

        Returns:
            Dictionary containing extracted skills and technologies
        """
        request = OpenAIRequest(
            system_message="You extract skills, technologies, and requirements from job descriptions.",
            template_path=prompt_template_path,
            template_variables={
                "job_description": job_description,
            },
            context_name=company_name,
            response_validator=self._validate_skills_response,
        )

        return await self.openai_service.process_with_template(request)

    def _validate_job_response(self, response_data: dict[str, Any]) -> bool:
        """Validate job listing response structure."""
        required_fields = ["jobs"]

        for field in required_fields:
            if field not in response_data:
                logger.warning(
                    f"Missing required field in job listing response: {field}"
                )
                return False

        # Validate jobs structure
        jobs = response_data.get("jobs", [])
        if not isinstance(jobs, list):
            logger.warning("Jobs field is not a list")
            return False

        # Validate individual job structure
        for i, job in enumerate(jobs):
            if not isinstance(job, dict):
                logger.warning(f"Job {i} is not a dictionary")
                return False

            # Check for required job fields
            job_required_fields = ["title", "url"]
            for field in job_required_fields:
                if field not in job:
                    logger.warning(f"Job {i} missing required field: {field}")
                    return False

        return True

    def _validate_job_details_response(self, response_data: dict[str, Any]) -> bool:
        """Validate job details response structure."""
        required_fields = ["job"]

        for field in required_fields:
            if field not in response_data:
                logger.warning(
                    f"Missing required field in job details response: {field}"
                )
                return False

        job = response_data.get("job", {})
        if not isinstance(job, dict):
            logger.warning("Job field is not a dictionary")
            return False

        # Check for expected job detail fields (adjust based on your needs)
        expected_fields = ["title", "description", "requirements"]
        for field in expected_fields:
            if field not in job:
                logger.info(f"Job details missing optional field: {field}")

        return True

    def _validate_skills_response(self, response_data: dict[str, Any]) -> bool:
        """Validate skills extraction response structure."""
        required_fields = ["skills", "technologies"]

        for field in required_fields:
            if field not in response_data:
                logger.warning(f"Missing required field in skills response: {field}")
                return False

        # Validate that skills and technologies are lists
        for field in required_fields:
            if not isinstance(response_data[field], list):
                logger.warning(f"{field} field is not a list")
                return False

        return True
