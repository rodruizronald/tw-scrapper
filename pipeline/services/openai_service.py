import asyncio
import json
from pathlib import Path
from typing import Any

import openai
from loguru import logger

from pipeline.core.config import OpenAIConfig
from pipeline.utils.exceptions import FileOperationError, OpenAIProcessingError


class OpenAIService:
    """Service for processing content with OpenAI API."""

    def __init__(self, config: OpenAIConfig):
        """
        Initialize OpenAI service.

        Args:
            config: OpenAI configuration
        """
        self.config = config
        self.client = openai.OpenAI(api_key=config.api_key)
        self._rate_limit_delay = 1.0  # Base delay between requests

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
        company_context = f"[{company_name}] " if company_name else ""

        # Read prompt template
        prompt_template = self._read_prompt_template(prompt_template_path, company_name)

        # Prepare the prompt
        filled_prompt = self._prepare_prompt(prompt_template, html_content, career_url)

        # Process with OpenAI with retries
        for attempt in range(self.config.max_retries + 1):
            try:
                result = await self._attempt_openai_request(
                    filled_prompt, attempt, company_context
                )
                if result is not None:
                    return result

            except (
                openai.RateLimitError,
                openai.APITimeoutError,
                openai.APIError,
            ) as e:
                if not await self._handle_openai_error(
                    e, attempt, company_context, company_name
                ):
                    raise

            except Exception as e:
                if not self._handle_unexpected_error(
                    e, attempt, company_context, company_name
                ):
                    raise

        # This should never be reached
        raise OpenAIProcessingError("Maximum retries exceeded", company_name)

    async def _attempt_openai_request(
        self,
        filled_prompt: str,
        attempt: int,
        company_context: str,
    ) -> dict[str, Any] | None:
        """Attempt a single OpenAI request."""
        logger.info(
            f"{company_context}Sending content to OpenAI (attempt {attempt + 1})..."
        )

        # Add rate limiting delay
        if attempt > 0:
            delay = self._rate_limit_delay * (2 ** (attempt - 1))  # Exponential backoff
            logger.info(f"{company_context}Waiting {delay}s before retry...")
            await asyncio.sleep(delay)

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": "You extract job href links from HTML content.",
                },
                {"role": "user", "content": filled_prompt},
            ],
            response_format={"type": "json_object"},
            timeout=self.config.timeout,
        )

        return self._parse_openai_response(response, company_context)

    def _parse_openai_response(
        self,
        response: openai.types.chat.ChatCompletion,
        company_context: str,
    ) -> dict[str, Any] | None:
        """Parse and validate OpenAI response."""
        response_text = response.choices[0].message.content
        if response_text is None:
            error_msg = "Empty response from OpenAI"
            logger.error(f"{company_context}{error_msg}")
            return None

        try:
            job_data: dict[str, Any] = json.loads(response_text)
            logger.success(f"{company_context}Successfully parsed response from OpenAI")
            return job_data

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response from OpenAI: {e}"
            logger.error(f"{company_context}{error_msg}")
            return None

    async def _handle_openai_error(
        self,
        error: Exception,
        attempt: int,
        company_context: str,
        company_name: str | None,
    ) -> bool:
        """Handle OpenAI-specific errors. Returns True if should continue retrying."""
        if isinstance(error, openai.RateLimitError):
            error_msg = f"OpenAI rate limit exceeded: {error}"
            logger.warning(f"{company_context}{error_msg}")

            if attempt < self.config.max_retries:
                delay = self._rate_limit_delay * (3**attempt)
                logger.info(f"{company_context}Rate limited, waiting {delay}s...")
                await asyncio.sleep(delay)
                return True
            else:
                raise OpenAIProcessingError(error_msg, company_name) from error

        elif isinstance(error, openai.APITimeoutError):
            error_msg = f"OpenAI API timeout: {error}"
            logger.warning(f"{company_context}{error_msg}")

            if attempt < self.config.max_retries:
                return True
            else:
                raise OpenAIProcessingError(error_msg, company_name) from error

        elif isinstance(error, openai.APIError):
            error_msg = f"OpenAI API error: {error}"
            logger.error(f"{company_context}{error_msg}")

            if attempt < self.config.max_retries:
                return True
            else:
                raise OpenAIProcessingError(error_msg, company_name) from error

        return False

    def _handle_unexpected_error(
        self,
        error: Exception,
        attempt: int,
        company_context: str,
        company_name: str | None,
    ) -> bool:
        """Handle unexpected errors. Returns True if should continue retrying."""
        error_msg = f"Unexpected error during OpenAI processing: {error}"
        logger.error(f"{company_context}{error_msg}")

        if attempt < self.config.max_retries:
            return True
        else:
            raise OpenAIProcessingError(error_msg, company_name) from error

    def _read_prompt_template(
        self, template_path: Path, company_name: str | None = None
    ) -> str:
        """Read prompt template from file."""
        try:
            with open(template_path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise FileOperationError(
                "read", str(template_path), "File not found", company_name
            ) from e
        except Exception as e:
            raise FileOperationError(
                "read", str(template_path), str(e), company_name
            ) from e

    def _prepare_prompt(self, template: str, html_content: str, career_url: str) -> str:
        """Prepare the prompt by filling in template variables."""
        # Escape any curly braces in the HTML content to prevent format string issues
        escaped_html = html_content.replace("{", "{{").replace("}", "}}")

        # Replace template variables
        filled_prompt = template.replace("{html_content}", escaped_html)
        filled_prompt = filled_prompt.replace("{career_url}", career_url)

        return filled_prompt

    def validate_response_structure(self, response_data: dict[str, Any]) -> bool:
        """
        Validate that the OpenAI response has the expected structure.

        Args:
            response_data: Response data from OpenAI

        Returns:
            True if structure is valid, False otherwise
        """
        required_fields = ["jobs"]

        for field in required_fields:
            if field not in response_data:
                logger.warning(f"Missing required field in OpenAI response: {field}")
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

            # Check for required job fields (adjust based on your needs)
            job_required_fields = ["title", "url"]
            for field in job_required_fields:
                if field not in job:
                    logger.warning(f"Job {i} missing required field: {field}")
                    return False

        return True
