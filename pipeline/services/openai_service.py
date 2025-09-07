import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import openai
from openai.types.shared_params import ResponseFormatJSONSchema
from prefect import get_run_logger

from pipeline.core.config import OpenAIConfig
from pipeline.utils.exceptions import FileOperationError, OpenAIProcessingError

if TYPE_CHECKING:
    from openai.types.shared_params.response_format_json_schema_param import JSONSchema


@dataclass
class OpenAIRequest:
    """Configuration for an OpenAI request."""

    system_message: str
    template_path: Path
    template_variables: dict[str, str]
    response_format: dict[str, Any]
    context_name: str | None = None


class OpenAIService:
    """Generic service for processing content with OpenAI API."""

    def __init__(self, config: OpenAIConfig):
        """
        Initialize OpenAI service.

        Args:
            config: OpenAI configuration
        """
        self.logger = get_run_logger()
        self.config = config
        self.client = openai.OpenAI(api_key=config.api_key)
        self._rate_limit_delay = 1.0  # Base delay between requests

    async def process_with_template(
        self,
        request: OpenAIRequest,
    ) -> dict[str, Any]:
        """
        Process content using OpenAI with a template-based approach.

        Args:
            request: OpenAI request configuration

        Returns:
            Dictionary containing parsed response data

        Raises:
            OpenAIProcessingError: If OpenAI processing fails
            FileOperationError: If prompt template cannot be read
        """
        context = f"[{request.context_name}] " if request.context_name else ""

        # Read prompt template
        prompt_template = self._read_prompt_template(
            request.template_path, request.context_name
        )

        # Prepare the prompt
        filled_prompt = self._prepare_prompt(
            prompt_template, request.template_variables
        )

        # Process with OpenAI with retries
        for attempt in range(self.config.max_retries + 1):
            try:
                result = await self._attempt_openai_request(
                    filled_prompt,
                    request.system_message,
                    request.response_format,
                    attempt,
                    context,
                )

                if result is not None:
                    self.logger.info(
                        f"{context}OpenAI request completed successfully on attempt {attempt + 1}"
                    )
                    return result

                self.logger.warning(
                    f"{context}OpenAI request returned no result on attempt {attempt + 1}, retrying..."
                )

            except (
                openai.RateLimitError,
                openai.APITimeoutError,
                openai.APIError,
            ) as e:
                if not await self._handle_openai_error(
                    e, attempt, context, request.context_name
                ):
                    raise

            except Exception as e:
                if not self._handle_unexpected_error(
                    e, attempt, context, request.context_name
                ):
                    raise

        # This should never be reached
        raise OpenAIProcessingError("Maximum retries exceeded", request.context_name)

    async def _attempt_openai_request(
        self,
        filled_prompt: str,
        system_message: str,
        response_format: dict[str, Any],
        attempt: int,
        context: str,
    ) -> dict[str, Any] | None:
        """Attempt a single OpenAI request.

        Note: response_format should be a dict with 'name', 'schema', and optionally 'strict' keys
        as per OpenAI's Structured Outputs format.
        """
        self.logger.info(
            f"{context}Sending content to OpenAI (attempt {attempt + 1})..."
        )

        # Add rate limiting delay
        if attempt > 0:
            delay = self._rate_limit_delay * (2 ** (attempt - 1))  # Exponential backoff
            self.logger.info(f"{context}Waiting {delay}s before retry...")
            await asyncio.sleep(delay)

        # Cast the response_format dict to JSONSchema type for type checking
        # The response_format should already contain 'name', 'schema', and optionally 'strict'
        json_schema = cast("JSONSchema", response_format)

        # Create the proper ResponseFormatJSONSchema object
        response_format_obj = ResponseFormatJSONSchema(
            type="json_schema", json_schema=json_schema
        )

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": system_message,
                },
                {"role": "user", "content": filled_prompt},
            ],
            response_format=response_format_obj,
            timeout=self.config.timeout,
        )

        return self._parse_openai_response(response, context)

    def _parse_openai_response(
        self,
        response: openai.types.chat.ChatCompletion,
        context: str,
    ) -> dict[str, Any] | None:
        """Parse and validate OpenAI response."""

        response_text = response.choices[0].message.content
        if response_text is None:
            error_msg = "Empty response from OpenAI"
            self.logger.error(f"{context}{error_msg}")
            return None

        try:
            response_data: dict[str, Any] = json.loads(response_text)
            self.logger.info(f"{context}Successfully parsed response from OpenAI")
            return response_data

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response from OpenAI: {e}"
            self.logger.error(f"{context}{error_msg}")
            return None

    async def _handle_openai_error(
        self,
        error: Exception,
        attempt: int,
        context: str,
        context_name: str | None,
    ) -> bool:
        """Handle OpenAI-specific errors. Returns True if should continue retrying."""

        if isinstance(error, openai.RateLimitError):
            error_msg = f"OpenAI rate limit exceeded: {error}"
            self.logger.warning(f"{context}{error_msg}")

            if attempt < self.config.max_retries:
                delay = self._rate_limit_delay * (3**attempt)
                self.logger.info(f"{context}Rate limited, waiting {delay}s...")
                await asyncio.sleep(delay)
                return True
            else:
                raise OpenAIProcessingError(error_msg, context_name) from error

        elif isinstance(error, openai.APITimeoutError):
            error_msg = f"OpenAI API timeout: {error}"
            self.logger.warning(f"{context}{error_msg}")

            if attempt < self.config.max_retries:
                return True
            else:
                raise OpenAIProcessingError(error_msg, context_name) from error

        elif isinstance(error, openai.APIError):
            error_msg = f"OpenAI API error: {error}"
            self.logger.error(f"{context}{error_msg}")

            if attempt < self.config.max_retries:
                return True
            else:
                raise OpenAIProcessingError(error_msg, context_name) from error

        return False

    def _handle_unexpected_error(
        self,
        error: Exception,
        attempt: int,
        context: str,
        context_name: str | None,
    ) -> bool:
        """Handle unexpected errors. Returns True if should continue retrying."""
        error_msg = f"Unexpected error during OpenAI processing: {error}"
        self.logger.error(f"{context}{error_msg}")

        if attempt < self.config.max_retries:
            return True
        else:
            raise OpenAIProcessingError(error_msg, context_name) from error

    def _read_prompt_template(
        self, template_path: Path, context_name: str | None = None
    ) -> str:
        """Read prompt template from file."""
        try:
            with open(template_path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise FileOperationError(
                "read", str(template_path), "File not found", context_name
            ) from e
        except Exception as e:
            raise FileOperationError(
                "read", str(template_path), str(e), context_name
            ) from e

    def _prepare_prompt(self, template: str, variables: dict[str, str]) -> str:
        """Prepare prompt by replacing template variables."""
        filled_prompt = template

        for key, value in variables.items():
            # Escape curly braces in values to prevent format string issues
            escaped_value = value.replace("{", "{{").replace("}", "}}")
            filled_prompt = filled_prompt.replace(f"{{{key}}}", escaped_value)

        return filled_prompt
