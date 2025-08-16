"""
Selector tester utility for testing CSS selectors on web pages.

This utility uses the parsers module to test selectors with different
parsing strategies (default, greenhouse, angular).
"""

import asyncio
from typing import List
from parsers import ParserType, ElementResult
from services import extract_by_selectors


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
    # Print header
    print(f"\n{'='*80}")
    print(f"TESTING SELECTORS ON: {url}")
    print(f"📋 PARSER: {parser.value}")
    print(f"📊 SELECTORS TO TEST: {len(selectors)}")
    print(f"{'='*80}\n")

    results = await extract_by_selectors(
        url=url, selectors=selectors, parser_type=parser
    )

    # Print results
    for i, result in enumerate(results, 1):
        print(f"\n[{i}/{len(results)}] {format_result_output(result)}")
        print(f"\n{'='*80}")

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
