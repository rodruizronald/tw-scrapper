"""
Web extraction service for scraping elements from web pages.

This module provides high-level functions for extracting elements from web pages
using different parsing strategies. It handles browser management, navigation,
and error handling, delegating the actual parsing to the parsers module.
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from loguru import logger
from playwright.async_api import Browser, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from parsers import ElementResult, ParserFactory, ParserType


@dataclass
class BrowserConfig:
    """Configuration for browser instances."""

    headless: bool = True
    viewport: dict[str, int] | None = None
    user_agent: str | None = None
    timeout: int = 30000
    wait_until: str = "domcontentloaded"
    extra_headers: dict[str, str] | None = None


@dataclass
class ExtractionConfig:
    """Configuration for extraction operations."""

    browser_config: BrowserConfig = field(default_factory=BrowserConfig)
    parser_type: ParserType = ParserType.DEFAULT
    retry_on_failure: bool = False
    max_retries: int = 3


class WebExtractionService:
    """
    Service for extracting elements from web pages.

    This service manages browser lifecycle and coordinates with parsers
    to extract elements from web pages.
    """

    def __init__(self, config: ExtractionConfig | None = None):
        """
        Initialize the extraction service.

        Args:
            config: Optional configuration for extraction operations
        """
        self.config = config or ExtractionConfig()
        self._browser: Browser | None = None
        self._playwright = None

    @asynccontextmanager
    async def _browser_context(self):
        """Context manager for browser lifecycle."""
        browser = None
        playwright = None
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=self.config.browser_config.headless
            )
            yield browser
        finally:
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()

    @asynccontextmanager
    async def _page_context(self, browser: Browser):
        """Context manager for page lifecycle with configuration."""
        context_options: dict[str, Any] = {}

        if self.config.browser_config.viewport:
            context_options["viewport"] = self.config.browser_config.viewport
        if self.config.browser_config.user_agent:
            context_options["user_agent"] = self.config.browser_config.user_agent
        if self.config.browser_config.extra_headers:
            context_options["extra_http_headers"] = (
                self.config.browser_config.extra_headers
            )

        context = (
            await browser.new_context(**context_options) if context_options else None
        )
        page = await (context.new_page() if context else browser.new_page())

        try:
            yield page
        finally:
            await page.close()
            if context:
                await context.close()

    async def extract_elements(
        self,
        url: str,
        selectors: list[str],
        parser_type: ParserType | None = None,
    ) -> list[ElementResult]:
        """
        Extract elements from a web page using specified selectors.

        Args:
            url: The URL to extract elements from
            selectors: List of CSS selectors to extract
            parser_type: Optional parser type override (uses config default if not specified)

        Returns:
            List of ElementResult objects containing extraction results
        """
        parser_type = parser_type or self.config.parser_type
        results = []

        async with (
            self._browser_context() as browser,
            self._page_context(browser) as page,
        ):
            try:
                # Navigate to URL
                logger.info(f"Navigating to {url}")
                await page.goto(
                    url,
                    wait_until=self.config.browser_config.wait_until,
                    timeout=self.config.browser_config.timeout,
                )
                logger.info("Initial page load complete")

                # Create and run parser
                parser = ParserFactory.create_parser(parser_type, page, selectors)
                results = await parser.parse()

            except PlaywrightTimeoutError:
                logger.warning(
                    f"Page load timeout for {url} - proceeding with partial content"
                )
                # Try to parse what we have
                try:
                    parser = ParserFactory.create_parser(parser_type, page, selectors)
                    results = await parser.parse()
                except Exception as parse_error:
                    logger.error(f"Failed to parse after timeout: {parse_error}")
                    results = self._create_error_results(
                        selectors,
                        f"Page timeout and parse failed: {parse_error!s}",
                    )

            except Exception as e:
                logger.error(f"Failed to navigate to {url}: {e}")
                results = self._create_error_results(
                    selectors, f"Navigation failed: {e!s}"
                )

        return results

    async def extract_from_multiple_urls(
        self, url_configs: list[dict[str, Any]]
    ) -> dict[str, list[ElementResult]]:
        """
        Extract elements from multiple URLs.

        Args:
            url_configs: List of dictionaries with 'url', 'selectors', and optional 'parser_type'

        Returns:
            Dictionary mapping URLs to their extraction results
        """
        results = {}

        for config in url_configs:
            url = config["url"]
            selectors = config["selectors"]
            parser_type = config.get("parser_type", self.config.parser_type)

            results[url] = await self.extract_elements(url, selectors, parser_type)

        return results

    async def extract_with_retry(
        self,
        url: str,
        selectors: list[str],
        parser_type: ParserType | None = None,
        max_retries: int | None = None,
    ) -> list[ElementResult]:
        """
        Extract elements with retry logic on failure.

        Args:
            url: The URL to extract elements from
            selectors: List of CSS selectors to extract
            parser_type: Optional parser type override
            max_retries: Optional max retries override

        Returns:
            List of ElementResult objects containing extraction results
        """
        max_retries = max_retries or self.config.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                results = await self.extract_elements(url, selectors, parser_type)

                # Check if we got any successful results
                if any(r.found for r in results):
                    return results

                logger.warning(f"Attempt {attempt + 1} found no elements, retrying...")

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    await asyncio.sleep(2**attempt)

        # All retries failed
        logger.error(f"All {max_retries} attempts failed")
        return self._create_error_results(
            selectors, f"All retries failed. Last error: {last_error!s}"
        )

    @staticmethod
    def _create_error_results(
        selectors: list[str], error_message: str
    ) -> list[ElementResult]:
        """Create error results for all selectors."""
        return [
            ElementResult(
                selector=selector,
                found=False,
                error_message=error_message,
                context="error",
            )
            for selector in selectors
        ]


# Convenience functions for simple use cases
async def extract_by_selectors(
    url: str,
    selectors: list[str],
    parser_type: ParserType = ParserType.DEFAULT,
    headless: bool = True,
) -> list[ElementResult]:
    """
    Convenience function for simple element extraction.

    This function provides a simple interface for one-off extractions
    without needing to instantiate the service class.

    Args:
        url: The URL to extract elements from
        selectors: List of CSS selectors to extract
        parser_type: Parser type to use
        headless: Whether to run browser in headless mode

    Returns:
        List of ElementResult objects containing extraction results
    """
    config = ExtractionConfig(
        browser_config=BrowserConfig(headless=headless), parser_type=parser_type
    )
    service = WebExtractionService(config)
    return await service.extract_elements(url, selectors, parser_type)


async def extract_from_urls_batch(
    url_configs: list[dict[str, Any]],
    headless: bool = True,
) -> dict[str, list[ElementResult]]:
    """
    Convenience function for batch extraction from multiple URLs.

    Args:
        url_configs: List of dictionaries with 'url', 'selectors', and optional 'parser_type'
        headless: Whether to run browser in headless mode

    Returns:
        Dictionary mapping URLs to their extraction results
    """
    config = ExtractionConfig(browser_config=BrowserConfig(headless=headless))
    service = WebExtractionService(config)
    return await service.extract_from_multiple_urls(url_configs)


# For backward compatibility and simple imports
__all__ = [
    "BrowserConfig",
    "ExtractionConfig",
    "WebExtractionService",
    "extract_by_selectors",
    "extract_from_urls_batch",
]


# Example usage
if __name__ == "__main__":
    import asyncio

    async def example():
        # Simple usage
        results = await extract_by_selectors(
            url="https://example.com",
            selectors=["h1", "p"],
            parser_type=ParserType.DEFAULT,
        )

        # Advanced usage with service
        config = ExtractionConfig(
            browser_config=BrowserConfig(
                headless=False, viewport={"width": 1920, "height": 1080}
            ),
            parser_type=ParserType.ANGULAR,
            retry_on_failure=True,
            max_retries=3,
        )

        service = WebExtractionService(config)
        results = await service.extract_with_retry(
            url="https://example.com", selectors=["h1", "p"]
        )

        return results

    asyncio.run(example())
