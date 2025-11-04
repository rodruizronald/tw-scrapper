"""Base parser class for selector extraction."""

import logging

from playwright.async_api import Page

from core.models.parsers import ParserType
from services.parsers.models import ElementResult, ParseContext

logger = logging.getLogger(__name__)


class SelectorParser:
    """Base class for different parser implementations."""

    def __init__(self, page: Page, selectors: list[str]):
        self.page = page
        self.selectors = selectors
        self.results: list[ElementResult] = []
        self.parser_type = ParserType.DEFAULT  # Override in subclasses

    async def setup(self) -> ParseContext:
        """Setup parsing context. Override in subclasses for specific setup."""
        return ParseContext(page=self.page, parser_type=self.parser_type)

    async def wait_for_content(self, context: ParseContext) -> None:
        """Wait for content to load. Override in subclasses for specific wait logic."""
        pass

    async def extract_element(
        self, context: ParseContext, selector: str, timeout: int = 5000
    ) -> ElementResult:
        """Extract content from a single element."""
        try:
            element = await context.target.wait_for_selector(selector, timeout=timeout)

            if element:
                text_content = await element.inner_text()
                html_content = await element.inner_html()

                return ElementResult(
                    selector=selector,
                    found=True,
                    text_content=text_content,
                    html_content=html_content,
                    context=self._get_context_name(context),
                )
            else:
                return ElementResult(
                    selector=selector,
                    found=False,
                    error_message="Element not found",
                    context=self._get_context_name(context),
                )

        except Exception as e:
            return ElementResult(
                selector=selector,
                found=False,
                error_message=str(e),
                context=self._get_context_name(context),
            )

    def _get_context_name(self, context: ParseContext) -> str:
        """Get human-readable context name."""
        if context.frame:
            return f"{context.parser_type.value}_frame"
        return context.parser_type.value

    async def parse(self) -> list[ElementResult]:
        """Main parsing method."""
        try:
            context = await self.setup()
            await self.wait_for_content(context)

            for selector in self.selectors:
                result = await self.extract_element(context, selector)
                self.results.append(result)
                self._log_result(result)

        except Exception as e:
            logger.error(f"Error during parsing: {e}")
            # Add error result for remaining selectors
            for selector in self.selectors:
                if not any(r.selector == selector for r in self.results):
                    self.results.append(
                        ElementResult(
                            selector=selector,
                            found=False,
                            error_message=f"Parser error: {e!s}",
                            context=self.parser_type.value,
                        )
                    )

        return self.results

    def _log_result(self, result: ElementResult) -> None:
        """Log the result of element extraction."""
        if result.found:
            logger.info(f"Found element with selector: {result.selector}")
        else:
            logger.warning(
                f"Failed to find element: {result.selector} - {result.error_message}"
            )
