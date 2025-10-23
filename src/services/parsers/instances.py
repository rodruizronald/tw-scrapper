"""Concrete parser implementations for different content types."""

import logging

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .base import SelectorParser
from .models import ElementResult, ParseContext, ParserType

logger = logging.getLogger(__name__)


class DefaultParser(SelectorParser):
    """Parser for standard HTML pages."""

    def __init__(self, page, selectors):
        super().__init__(page, selectors)
        self.parser_type = ParserType.DEFAULT

    async def setup(self) -> ParseContext:
        """Setup for default parsing - no special handling needed."""
        logger.debug("Using default parser for standard HTML")
        return ParseContext(page=self.page, parser_type=ParserType.DEFAULT)

    async def wait_for_content(self, context: ParseContext) -> None:
        """Wait for standard page load."""
        try:
            await context.page.wait_for_load_state("domcontentloaded", timeout=30000)
            logger.debug("Page reached network idle state")
        except PlaywrightTimeoutError:
            logger.warning("Network idle timeout - proceeding with available content")
            # Continue anyway - content might still be available


class GreenhouseParser(SelectorParser):
    """Parser for Greenhouse iframe-based job boards."""

    def __init__(self, page, selectors):
        super().__init__(page, selectors)
        self.parser_type = ParserType.GREENHOUSE

    async def setup(self) -> ParseContext:
        """Setup Greenhouse iframe context."""
        logger.debug("Using Greenhouse parser - looking for iframe")

        try:
            # Look for Greenhouse iframe
            greenhouse_iframe = await self.page.wait_for_selector(
                "#grnhse_iframe", timeout=5000
            )

            if greenhouse_iframe:
                frame = await greenhouse_iframe.content_frame()
                if frame:
                    logger.debug("Successfully accessed Greenhouse iframe")
                    return ParseContext(
                        page=self.page, frame=frame, parser_type=ParserType.GREENHOUSE
                    )
                else:
                    logger.warning(
                        "Could not access iframe content, falling back to main page"
                    )
        except Exception as e:
            logger.warning(f"Greenhouse iframe not found: {e}, using main page")

        return ParseContext(page=self.page, parser_type=ParserType.GREENHOUSE)

    async def wait_for_content(self, context: ParseContext) -> None:
        """Wait for iframe content to load."""
        try:
            if context.frame:
                await context.frame.wait_for_load_state(
                    "domcontentloaded", timeout=30000
                )
                logger.debug("Iframe content loaded")
            else:
                await context.page.wait_for_load_state(
                    "domcontentloaded", timeout=30000
                )
        except PlaywrightTimeoutError:
            logger.warning("Load state timeout - proceeding with available content")

    async def extract_element(
        self, context: ParseContext, selector: str, timeout: int = 5000
    ) -> ElementResult:
        """Try iframe first, then fall back to main page if needed."""
        # Try iframe first if available
        if context.frame:
            result = await super().extract_element(context, selector, timeout)
            if result.found:
                return result

            # Fallback to main page
            logger.info(f"Selector not found in iframe, trying main page: {selector}")
            main_context = ParseContext(
                page=context.page, parser_type=context.parser_type
            )
            return await super().extract_element(main_context, selector, timeout=2000)

        # No iframe, use main page
        return await super().extract_element(context, selector, timeout)


class AngularParser(SelectorParser):
    """Parser for Angular applications with dynamic content."""

    def __init__(self, page, selectors):
        super().__init__(page, selectors)
        self.parser_type = ParserType.ANGULAR

    async def setup(self) -> ParseContext:
        """Setup for Angular parsing."""
        logger.debug("Using Angular parser for dynamic content")
        return ParseContext(page=self.page, parser_type=ParserType.ANGULAR)

    async def wait_for_content(self, context: ParseContext) -> None:
        """Wait for Angular to render dynamic content."""
        try:
            # For Angular, use 'domcontentloaded' or 'commit' instead of 'networkidle'
            # as Angular apps often never reach networkidle state
            await context.page.wait_for_load_state("domcontentloaded", timeout=30000)
            logger.debug("DOM content loaded")

            # Wait a bit for initial Angular bootstrapping
            await context.page.wait_for_timeout(2000)

            # Try to wait for Angular-specific indicators with a shorter timeout
            try:
                await context.page.wait_for_function(
                    """
                    () => {
                        // Check for any Angular indicators
                        const hasAngularElements =
                            document.querySelector('[ng-version]') !== null ||
                            document.querySelector('app-root') !== null ||
                            document.querySelectorAll('[_ngcontent-ng-c]').length > 0 ||
                            document.querySelectorAll('.ng-star-inserted').length > 0;

                        // Also check if there's actual content (not just Angular shell)
                        const hasContent = document.body.innerText.trim().length > 100;

                        return hasAngularElements || hasContent;
                    }
                    """,
                    timeout=10000,
                )
                logger.debug("Angular content detected")

            except PlaywrightTimeoutError:
                logger.warning("Angular indicators not found, but proceeding anyway")

            # Give Angular components time to render
            await context.page.wait_for_timeout(3000)

        except PlaywrightTimeoutError as e:
            logger.warning(f"Angular content wait timeout: {e}")
            # Don't re-raise - continue with what we have
        except Exception as e:
            logger.error(f"Unexpected error waiting for Angular content: {e}")
            # Don't re-raise - continue with what we have

    async def extract_element(
        self,
        context: ParseContext,
        selector: str,
        timeout: int = 10000,  # Longer timeout for Angular
    ) -> ElementResult:
        """Extract element with extended timeout for Angular."""
        return await super().extract_element(context, selector, timeout)
