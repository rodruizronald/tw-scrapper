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

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import ParserType, ElementResult
from services import extract_elements_by_selectors
from loguru import logger

# Configure logger for this tool
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
)


class SelectorTester:
    """Main class for selector testing functionality."""

    # ANSI color codes for terminal output
    COLORS = {
        "GREEN": "\033[92m",
        "RED": "\033[91m",
        "YELLOW": "\033[93m",
        "BLUE": "\033[94m",
        "CYAN": "\033[96m",
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
    }

    def __init__(self, save_results: bool = False, output_format: str = "console"):
        """
        Initialize the selector tester.

        Args:
            save_results: Whether to save results to file
            output_format: Output format ('console', 'json', 'markdown')
        """
        self.save_results = save_results
        self.output_format = output_format
        self.results_dir = Path(__file__).parent / "results"

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

    def format_result_json(self, results: List[ElementResult]) -> str:
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

    def format_result_markdown(self, url: str, results: List[ElementResult]) -> str:
        """Format results as Markdown."""
        output = [f"# Selector Test Results\n"]
        output.append(f"**URL:** `{url}`\n")
        output.append(f"**Timestamp:** {datetime.now().isoformat()}\n")
        output.append(f"**Total Selectors:** {len(results)}\n")
        output.append(
            f"**Found:** {sum(1 for r in results if r.found)}/{len(results)}\n"
        )
        output.append("\n## Results\n")

        for i, result in enumerate(results, 1):
            output.append(f"### {i}. Selector: `{result.selector}`\n")
            if result.found:
                output.append(f"- **Status:** ✅ Found\n")
                output.append(f"- **Context:** {result.context}\n")
                if result.text_content:
                    text_preview = result.text_content[:200]
                    if len(result.text_content) > 200:
                        text_preview += "..."
                    output.append(f"- **Text Content:** {text_preview}\n")
            else:
                output.append(f"- **Status:** ❌ Not Found\n")
                output.append(f"- **Error:** {result.error_message}\n")
            output.append("")

        return "\n".join(output)

    async def test_selectors(
        self,
        url: str,
        selectors: List[str],
        parser_type: ParserType = ParserType.DEFAULT,
    ) -> List[ElementResult]:
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
            print(f"\n{'='*80}")
            print(f"{self._colorize('TESTING SELECTORS ON:', 'BOLD')} {url}")
            print(f"{self._colorize('📋 PARSER:', 'CYAN')} {parser_type.value}")
            print(f"{self._colorize('📊 SELECTORS TO TEST:', 'CYAN')} {len(selectors)}")
            print(f"{'='*80}\n")

        # Extract elements
        results = await extract_elements_by_selectors(
            url=url, selectors=selectors, parser_type=parser_type
        )

        # Format and display results
        if self.output_format == "console":
            for i, result in enumerate(results, 1):
                print(
                    f"\n{self._colorize(f'[{i}/{len(results)}]', 'YELLOW')} {self.format_result_console(result)}"
                )
                print(f"\n{'='*80}")

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

    def _save_results(self, url: str, results: List[ElementResult]):
        """Save results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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


def load_test_config(config_file: str) -> Dict[str, Any]:
    """Load test configuration from JSON file."""
    config_path = Path(config_file)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_file}")
        return None

    with open(config_path) as f:
        return json.load(f)


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
