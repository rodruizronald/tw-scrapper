"""CLI entry point for the browser-use agent PoC."""

import argparse
import asyncio
import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.agent_poc.agent import extract_jobs
from tools.agent_poc.config import COMPANIES, DEFAULT_MAX_STEPS, DEFAULT_MODEL

OUTPUT_DIR = Path(__file__).parent / "output"


def slugify(name: str) -> str:
    """Convert company name to a filesystem-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def save_result(result: dict[str, Any], output_dir: Path) -> Path:
    """Save extraction result to a JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    slug = slugify(result["company"])
    filepath = output_dir / f"{slug}_{timestamp}.json"
    filepath.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return filepath


def print_summary(result: dict[str, Any]) -> None:
    """Print a human-readable extraction summary to console."""
    meta = result["metadata"]
    company = result["company"]
    jobs_count = meta["total_jobs_found"]
    elapsed = meta["extraction_time_seconds"]
    steps = meta["agent_steps"]
    error = meta["error"]

    print(f"\n{'=' * 60}")
    print(f"  Company:  {company}")
    print(f"  URL:      {result['url']}")
    print(f"  Jobs:     {jobs_count}")
    print(f"  Time:     {elapsed:.1f}s")
    print(f"  Steps:    {steps}")
    print(f"  Done:     {meta['agent_completed']}")
    print(f"  Errors:   {meta['agent_had_errors']}")

    if error:
        print(f"  Error:    {error}")

    if result["jobs"]:
        print(f"\n  {'Job URLs':}")
        print(f"  {'-' * 40}")
        for url in result["jobs"]:
            print(f"    - {url}")

    print(f"{'=' * 60}")


def find_company(name: str) -> dict[str, str] | None:
    """Find a company by name (case-insensitive partial match)."""
    name_lower = name.lower()
    for company in COMPANIES:
        if name_lower in company["name"].lower():
            return company
    return None


async def run_extraction(args: argparse.Namespace) -> None:
    """Run agent extraction for selected companies."""
    output_dir = Path(args.output_dir)

    if args.company:
        company = find_company(args.company)
        if not company:
            available = ", ".join(c["name"] for c in COMPANIES)
            print(f"Company '{args.company}' not found. Available: {available}")
            sys.exit(1)
        companies = [company]
    else:
        companies = COMPANIES

    print(f"\nAgent PoC - Extracting jobs from {len(companies)} company(ies)")
    print(
        f"Model: {args.model} | Max steps: {args.max_steps} | "
        f"Headless: {not args.headed}"
    )

    for company in companies:
        print(f"\nProcessing: {company['name']}...")
        result = await extract_jobs(
            company_name=company["name"],
            job_board_url=company["job_board_url"],
            sample_job_url=company["sample_job_url"],
            model=args.model,
            headless=not args.headed,
            max_steps=args.max_steps,
        )

        filepath = save_result(result, output_dir)
        print_summary(result)
        print(f"  Output:   {filepath}")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Browser-use agent PoC for job extraction",
    )
    parser.add_argument(
        "-c",
        "--company",
        type=str,
        default=None,
        help="Company name to extract (partial match). Defaults to all.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser in headed mode for debugging.",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=DEFAULT_MAX_STEPS,
        help=f"Max agent steps (default: {DEFAULT_MAX_STEPS}).",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help=f"Output directory for JSON results (default: {OUTPUT_DIR}).",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = parse_args()
    asyncio.run(run_extraction(args))


if __name__ == "__main__":
    main()
