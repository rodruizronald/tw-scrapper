import asyncio

from loguru import logger

from parsers import ParserType
from pipeline.services.extraction_service import extract_by_selectors
from pipeline.utils.exceptions import HTMLExtractionError


class HTMLExtractor:
    """Service for extracting HTML content from web pages."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize HTML extractor.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def extract_content(
        self,
        url: str,
        selectors: list[str],
        parser_type: ParserType,
        company_name: str | None = None,
    ) -> str:
        """
        Extract HTML content from specified selectors on a webpage.

        Args:
            url: The URL to extract content from
            selectors: List of CSS selectors to extract content from
            parser_type: Parser type to use for extraction
            company_name: Company name for logging context

        Returns:
            Concatenated HTML content from all selectors

        Raises:
            HTMLExtractionError: If extraction fails after all retries
        """
        company_context = f"[{company_name}] " if company_name else ""

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"{company_context}Extracting HTML content from {url} (attempt {attempt + 1})"
                )

                # Use existing extract_by_selectors function
                results = await extract_by_selectors(
                    url=url, selectors=selectors, parser_type=parser_type
                )

                # Collect HTML content from all successful results
                html_contents = []
                successful_selectors = []

                for result in results:
                    if result.found and result.html_content:
                        html_contents.append(result.html_content)
                        successful_selectors.append(result.selector)
                        logger.debug(
                            f"{company_context}Extracted content from selector: {result.selector}"
                        )
                    else:
                        logger.warning(
                            f"{company_context}No content found for selector: {result.selector}"
                        )

                # Check if we got any content
                if not html_contents:
                    error_msg = (
                        f"No HTML content extracted from any selectors: {selectors}"
                    )
                    logger.warning(f"{company_context}{error_msg}")

                    if attempt < self.max_retries:
                        logger.info(
                            f"{company_context}Retrying in {self.retry_delay} seconds..."
                        )
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        raise HTMLExtractionError(url, error_msg, company_name)

                # Concatenate all HTML content with newlines
                concatenated_html = "\n".join(html_contents)

                logger.success(
                    f"{company_context}Successfully extracted HTML content from "
                    f"{len(successful_selectors)} selectors: {successful_selectors}"
                )

                return concatenated_html

            except HTMLExtractionError:
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                error_msg = f"Unexpected error during HTML extraction: {e!s}"
                logger.error(f"{company_context}{error_msg}")

                if attempt < self.max_retries:
                    logger.info(
                        f"{company_context}Retrying in {self.retry_delay} seconds..."
                    )
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise HTMLExtractionError(url, error_msg, company_name) from e

        # This should never be reached, but just in case
        raise HTMLExtractionError(url, "Maximum retries exceeded", company_name)

    async def validate_url_accessibility(
        self, url: str, company_name: str | None = None
    ) -> bool:
        """
        Validate that a URL is accessible before attempting extraction.

        Args:
            url: URL to validate
            company_name: Company name for logging context

        Returns:
            True if URL is accessible, False otherwise
        """
        company_context = f"[{company_name}] " if company_name else ""

        try:
            # Simple validation using a basic selector
            results = await extract_by_selectors(
                url=url, selectors=["html"], parser_type=ParserType.DEFAULT
            )

            is_accessible = any(result.found for result in results)

            if is_accessible:
                logger.debug(f"{company_context}URL is accessible: {url}")
            else:
                logger.warning(f"{company_context}URL is not accessible: {url}")

            return is_accessible

        except Exception as e:
            logger.error(f"{company_context}Error validating URL accessibility: {e}")
            return False
