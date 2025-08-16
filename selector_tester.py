"""
Selector tester utility for testing CSS selectors on web pages.

This utility uses the parsers module to test selectors with different
parsing strategies (default, greenhouse, angular).
"""

import asyncio
import sys
from typing import List, Optional
from loguru import logger
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

# Import from the parsers module
from web_parser import ParserFactory, ParserType, ElementResult

# Configure logger for console output
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


def format_result_output(result: ElementResult) -> str:
    """Format a single result for console output."""
    output = []
    output.append(f"SELECTOR: {result.selector}")
    output.append("-" * 60)

    if result.found:
        output.append(f"✅ FOUND ELEMENT in {result.context}")

        if result.text_content:
            text_preview = result.text_content[:500]
            if len(result.text_content) > 500:
                text_preview += "..."
            output.append(f"📝 TEXT CONTENT ({len(result.text_content)} chars):")
            output.append(text_preview)

        if result.html_content:
            html_preview = result.html_content[:300]
            if len(result.html_content) > 300:
                html_preview += "..."
            output.append(f"\n🏷️  HTML CONTENT ({len(result.html_content)} chars):")
            output.append(html_preview)
    else:
        output.append(f"❌ ELEMENT NOT FOUND")
        output.append(f"Error: {result.error_message}")

    return "\n".join(output)


async def test_html_selectors(
    url: str,
    selectors: List[str],
    parser: ParserType = ParserType.DEFAULT,
    headless: bool = True,
    viewport: Optional[dict] = None,
    user_agent: Optional[str] = None,
) -> List[ElementResult]:
    """
    Test HTML selectors on a webpage using the specified parser.

    Args:
        url: The URL to test selectors on
        selectors: List of CSS selectors to test
        parser: Parser type to use (DEFAULT, GREENHOUSE, or ANGULAR)
        headless: Whether to run browser in headless mode
        viewport: Optional viewport settings (dict with 'width' and 'height')
        user_agent: Optional custom user agent string

    Returns:
        List of ElementResult objects containing extraction results
    """
    results = []
    browser = None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)

            # Configure browser context
            context_options = {}
            if viewport:
                context_options["viewport"] = viewport
            if user_agent:
                context_options["user_agent"] = user_agent

            context = (
                await browser.new_context(**context_options)
                if context_options
                else browser
            )
            page = await (context.new_page() if context_options else browser.new_page())

            # Navigate to URL with different strategies based on parser type
            logger.info(f"Navigating to {url}")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                logger.info("Initial page load complete (domcontentloaded)")

            except PlaywrightTimeoutError:
                logger.warning(
                    f"Page load timeout for {url} - proceeding with partial content"
                )
                # Don't re-raise - the page might still be usable

            except Exception as e:
                logger.error(f"Failed to navigate to {url}: {e}")
                # Return empty results with error messages
                for selector in selectors:
                    results.append(
                        ElementResult(
                            selector=selector,
                            found=False,
                            error_message=f"Navigation failed: {str(e)}",
                            context="error",
                        )
                    )
                return results

            # Create appropriate parser using the factory
            parser_instance = ParserFactory.create_parser(parser, page, selectors)

            # Print header
            print(f"\n{'='*80}")
            print(f"TESTING SELECTORS ON: {url}")
            print(f"📋 PARSER: {parser.value}")
            print(f"📊 SELECTORS TO TEST: {len(selectors)}")
            print(f"{'='*80}\n")

            # Parse and collect results
            results = await parser_instance.parse()

            # Print results
            for i, result in enumerate(results, 1):
                print(f"\n[{i}/{len(results)}] {format_result_output(result)}")
                print(f"\n{'='*80}")

    except Exception as e:
        logger.error(f"Unexpected error testing selectors: {str(e)}")
        # Ensure we return results even on error
        if not results:
            for selector in selectors:
                results.append(
                    ElementResult(
                        selector=selector,
                        found=False,
                        error_message=f"Unexpected error: {str(e)}",
                        context="error",
                    )
                )
    finally:
        if browser:
            await browser.close()

    return results


async def main():
    """Example usage demonstrating different parser types."""

    url = "https://careers.wearegap.com/jobs?country=Costa+Rica&query="
    selectors = ["#jobs_list_container"]
    results = await test_html_selectors(
        url=url,
        selectors=selectors,
        parser=ParserType.DEFAULT,
    )

    # Print summary
    successful = sum(1 for r in results if r.found)
    print(f"\n📊 SUMMARY: {successful}/{len(results)} selectors found successfully")


if __name__ == "__main__":
    asyncio.run(main())
