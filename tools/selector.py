"""
CSS Selector Testing Tool

A development utility for testing and validating CSS selectors on web pages
with different parsing strategies (default, greenhouse, angular).

Usage:
    python -m tools.selector_tester [--url URL] [--selectors SELECTOR1 SELECTOR2] [--parser TYPE]

    or

    python tools/selector_tester.py

Examples:
    # Test with default configuration
    python -m tools.selector_tester

    # Test specific URL with selectors
    python -m tools.selector_tester --url "https://example.com" --selectors "h1" ".content"

    # Test with Angular parser
    python -m tools.selector_tester --url "https://angular-app.com" --parser angular
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from src.core.config import BrowserConfig, WebExtractionConfig
from src.services.parsers import ElementResult, ParserType
from src.services.web_extraction_service import (
    WebExtractionService,
)

logger = logging.getLogger(__name__)


class SelectorTester:
    """Main class for selector testing functionality."""

    # ANSI color codes for terminal output
    COLORS: ClassVar[dict[str, str]] = {
        "GREEN": "\033[92m",
        "RED": "\033[91m",
        "YELLOW": "\033[93m",
        "BLUE": "\033[94m",
        "CYAN": "\033[96m",
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
    }

    def __init__(
        self,
        save_results: bool = False,
        output_format: str = "console",
        headless: bool = True,
        browser_config: BrowserConfig | None = None,
    ):
        """
        Initialize the selector tester.

        Args:
            save_results: Whether to save results to file
            output_format: Output format ('console', 'json', 'markdown')
            headless: Whether to run browser in headless mode
            browser_config: Optional browser configuration override
        """
        self.save_results = save_results
        self.output_format = output_format
        self.results_dir = Path(__file__).parent / "results"

        # Create browser and extraction configs
        self.browser_config = browser_config or BrowserConfig(
            headless=headless, timeout=30000, wait_until="domcontentloaded"
        )

        if save_results:
            self.results_dir.mkdir(exist_ok=True)

    def _colorize(self, text: str, color: str) -> str:
        """Add color to text for terminal output."""
        if self.output_format != "console":
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['RESET']}"

    def format_result_console(self, result: ElementResult) -> str:
        """Format a single result for console output."""
        output = []
        output.append(f"{self._colorize('SELECTOR:', 'CYAN')} {result.selector}")
        output.append("-" * 60)

        if result.found:
            output.append(
                f"{self._colorize('✅ FOUND ELEMENT', 'GREEN')} in {result.context}"
            )

            if result.text_content:
                text_preview = result.text_content[:500]
                if len(result.text_content) > 500:
                    text_preview += "..."
                output.append(
                    f"\n{self._colorize('📝 TEXT CONTENT', 'BLUE')} ({len(result.text_content)} chars):"
                )
                output.append(text_preview)

            if result.html_content:
                html_preview = result.html_content[:300]
                if len(result.html_content) > 300:
                    html_preview += "..."
                output.append(
                    f"\n{self._colorize('🏷️  HTML CONTENT', 'BLUE')} ({len(result.html_content)} chars):"
                )
                output.append(html_preview)
        else:
            output.append(f"{self._colorize('❌ ELEMENT NOT FOUND', 'RED')}")
            output.append(f"Error: {result.error_message}")

        return "\n".join(output)

    def format_result_json(self, results: list[ElementResult]) -> str:
        """Format results as JSON."""
        data = []
        for result in results:
            data.append(
                {
                    "selector": result.selector,
                    "found": result.found,
                    "context": result.context,
                    "text_content": result.text_content,
                    "html_content": result.html_content,
                    "error_message": result.error_message,
                }
            )
        return json.dumps(data, indent=2)

    def format_result_markdown(self, url: str, results: list[ElementResult]) -> str:
        """Format results as Markdown."""
        output = ["# Selector Test Results\n"]
        output.append(f"**URL:** `{url}`\n")
        output.append(f"**Timestamp:** {datetime.now(UTC).astimezone().isoformat()}\n")
        output.append(f"**Total Selectors:** {len(results)}\n")
        output.append(
            f"**Found:** {sum(1 for r in results if r.found)}/{len(results)}\n"
        )
        output.append("\n## Results\n")

        for i, result in enumerate(results, 1):
            output.append(f"### {i}. Selector: `{result.selector}`\n")
            if result.found:
                output.append("- **Status:** ✅ Found\n")
                output.append(f"- **Context:** {result.context}\n")
                if result.text_content:
                    text_preview = result.text_content[:200]
                    if len(result.text_content) > 200:
                        text_preview += "..."
                    output.append(f"- **Text Content:** {text_preview}\n")
            else:
                output.append("- **Status:** ❌ Not Found\n")
                output.append(f"- **Error:** {result.error_message}\n")
            output.append("")

        return "\n".join(output)

    def _create_extraction_service(
        self, parser_type: ParserType
    ) -> WebExtractionService:
        """Create extraction service with specified parser type."""
        config = WebExtractionConfig(
            browser_config=self.browser_config,
            parser_type=parser_type,
            max_retries=2,
            retry_delay=1.0,
        )
        return WebExtractionService(config)

    async def test_selectors(
        self,
        url: str,
        selectors: list[str],
        parser_type: ParserType = ParserType.DEFAULT,
    ) -> list[ElementResult]:
        """
        Test HTML selectors on a webpage.

        Args:
            url: The URL to test
            selectors: List of CSS selectors
            parser_type: Parser type to use

        Returns:
            List of ElementResult objects
        """
        # Print header for console output
        if self.output_format == "console":
            print(f"\n{'=' * 80}")
            print(f"{self._colorize('TESTING SELECTORS ON:', 'BOLD')} {url}")
            print(f"{self._colorize('📋 PARSER:', 'CYAN')} {parser_type.value}")
            print(f"{self._colorize('📊 SELECTORS TO TEST:', 'CYAN')} {len(selectors)}")
            print(f"{'=' * 80}\n")

        # Create extraction service with specified parser type
        service = self._create_extraction_service(parser_type)

        try:
            # Extract elements using the service
            results = await service.extract_elements(
                url=url, selectors=selectors, parser_type=parser_type
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            # Create error results for all selectors
            results = [
                ElementResult(
                    selector=selector,
                    found=False,
                    error_message=f"Service error: {e!s}",
                    context="error",
                )
                for selector in selectors
            ]

        # Format and display results
        if self.output_format == "console":
            for i, result in enumerate(results, 1):
                print(
                    f"\n{self._colorize(f'[{i}/{len(results)}]', 'YELLOW')} {self.format_result_console(result)}"
                )
                print(f"\n{'=' * 80}")

            # Print summary
            successful = sum(1 for r in results if r.found)
            print(
                f"\n{self._colorize('📊 SUMMARY:', 'BOLD')} {successful}/{len(results)} selectors found successfully"
            )

        elif self.output_format == "json":
            print(self.format_result_json(results))

        elif self.output_format == "markdown":
            print(self.format_result_markdown(url, results))

        # Save results if requested
        if self.save_results:
            self._save_results(url, results)

        return results

    def _save_results(self, url: str, results: list[ElementResult]):
        """Save results to file."""
        timestamp = datetime.now(UTC).astimezone().strftime("%Y%m%d_%H%M%S")
        domain = url.split("/")[2].replace(".", "_")

        if self.output_format == "json":
            filename = f"{domain}_{timestamp}.json"
            filepath = self.results_dir / filename
            filepath.write_text(self.format_result_json(results))
        else:
            filename = f"{domain}_{timestamp}.md"
            filepath = self.results_dir / filename
            filepath.write_text(self.format_result_markdown(url, results))

        logger.info(f"Results saved to: {filepath}")


def load_test_config(config_file: str) -> dict[str, Any] | None:
    """Load test configuration from JSON file."""
    config_path = Path(config_file)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_file}")
        return None

    try:
        with open(config_path) as f:
            config: dict[str, Any] = json.load(f)
            return config
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Error loading config file: {e}")
        return None


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Test CSS selectors on web pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url "https://example.com" --selectors "h1" ".content"
  %(prog)s --config test_config.json
  %(prog)s --url "https://angular-app.com" --parser angular --save
        """,
    )

    parser.add_argument("--url", type=str, help="URL to test selectors on")

    parser.add_argument("--selectors", nargs="+", help="CSS selectors to test")

    parser.add_argument(
        "--parser",
        type=str,
        choices=["default", "greenhouse", "angular"],
        default="default",
        help="Parser type to use (default: default)",
    )

    parser.add_argument(
        "--config", type=str, help="Load test configuration from JSON file"
    )

    parser.add_argument("--save", action="store_true", help="Save results to file")

    parser.add_argument(
        "--format",
        type=str,
        choices=["console", "json", "markdown"],
        default="console",
        help="Output format (default: console)",
    )

    return parser


async def main():
    """Main entry point for the selector tester tool."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Load configuration
    if args.config:
        config = load_test_config(args.config)
        if not config:
            sys.exit(1)
        url = config.get("url")
        selectors = config.get("selectors", [])
        parser_type = ParserType[config.get("parser", "DEFAULT").upper()]
    elif args.url and args.selectors:
        url = args.url
        selectors = args.selectors
        parser_type = ParserType[args.parser.upper()]
    else:
        # Default test configuration
        logger.info("Using default test configuration")
        url = "https://example.com"
        selectors = ["h1", "p", ".content"]
        parser_type = ParserType.DEFAULT

    # Create tester and run tests
    tester = SelectorTester(save_results=args.save, output_format=args.format)

    try:
        results = await tester.test_selectors(url, selectors, parser_type)

        # Exit with appropriate code
        if all(r.found for r in results):
            sys.exit(0)  # All selectors found
        elif any(r.found for r in results):
            sys.exit(1)  # Some selectors found
        else:
            sys.exit(2)  # No selectors found

    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())
