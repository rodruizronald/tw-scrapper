import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
from dotenv import load_dotenv
from loguru import logger

from parsers import ParserType
from services import extract_by_selectors

# Get the root directory and add it to Python path
root_dir = Path(__file__).parent.parent

# Load environment variables from .env file
load_dotenv(root_dir / ".env")

# Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = "gpt-5-mini"  # OpenAI model to use

# Define input directory path and input file name
INPUT_DIR = Path("input")
PROMPT_FILE = (
    INPUT_DIR / "prompts/job_eligibility_basic_metadata.md"
)  # File containing the prompt template

# Define global output directory path
OUTPUT_DIR = Path("data")
timestamp = datetime.now().strftime("%Y%m%d")
PIPELINE_INPUT_DIR = OUTPUT_DIR / timestamp / "pipeline_stage_1"
PIPELINE_OUTPUT_DIR = OUTPUT_DIR / timestamp / "pipeline_stage_2"
PIPELINE_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

INPUT_FILE = "jobs_stage_1.json"  # JSON file with company career URLs
OUTPUT_FILE = "jobs_stage_2.json"  # JSON file with job eligibility data

# Configure logger
LOG_LEVEL = "DEBUG"  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logger.remove()  # Remove default handler
logger.add(sys.stderr, level=LOG_LEVEL)  # Add stderr handler with desired log level
logger.add(
    f"{PIPELINE_OUTPUT_DIR}/logs.log",
    rotation="10 MB",
    level=LOG_LEVEL,
)  # Add file handler

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)


async def extract_html_content(
    url: str,
    selectors: Optional[List[str]] = None,
    parser: ParserType = ParserType.DEFAULT,
) -> Optional[str]:
    """
    Extract HTML content from specified selectors on a webpage.

    Args:
        url: The URL to extract content from
        selectors: List of CSS selectors to extract content from
        parser: Parser type to use for extraction

    Returns:
        Concatenated HTML content from all selectors, or None if extraction fails
    """
    try:
        results = await extract_by_selectors(
            url=url, selectors=selectors or [], parser_type=parser
        )

        # Collect HTML content from all successful results
        html_contents = []
        for result in results:
            if result.found and result.html_content:
                html_contents.append(result.html_content)
                logger.debug(f"Extracted content from selector: {result.selector}")
            else:
                logger.warning(f"No content found for selector: {result.selector}")

        # Concatenate all HTML content with newlines
        if html_contents:
            concatenated_html = "\n".join(html_contents)
            logger.info(
                f"Successfully extracted HTML content from {len(html_contents)} selectors"
            )
            return concatenated_html
        else:
            logger.warning("No HTML content extracted from any selectors")
            return None

    except Exception as e:
        logger.error(f"Error extracting HTML content from {url}: {e!s}")
        return None


def read_prompt_template() -> str:
    """Read the prompt template from a file."""
    try:
        with open(PROMPT_FILE) as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Error: Prompt template file '{PROMPT_FILE}' not found.")
        exit(1)
    except Exception as e:
        logger.error(f"Error reading prompt template: {e!s}")
        exit(1)


async def process_job(
    job_url: str,
    selectors: List[str],
    company_name: str,
    parser_type: ParserType = ParserType.DEFAULT,
) -> Dict[str, Any]:
    """Process a single job URL to extract eligibility and basic metadata."""
    logger.info(f"Processing job at {job_url} for {company_name}...")

    # Extract HTML content
    html_content = await extract_html_content(job_url, selectors, parser_type)
    if not html_content:
        logger.warning(f"Could not fetch content for job at {job_url}")
        return {
            "job": {},
            "error": "Failed to fetch HTML content",
        }

    # Read prompt template and fill it with HTML content
    prompt_template = read_prompt_template()
    # Escape any curly braces in the HTML content
    escaped_html = html_content.replace("{", "{{").replace("}", "}}")
    filled_prompt = prompt_template.replace("{html_content}", escaped_html)

    # Send to OpenAI
    try:
        logger.info(f"Sending content to OpenAI for job at {job_url}...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You extract job descriptions, eligibility information, and basic metadata from HTML content.",
                },
                {"role": "user", "content": filled_prompt},
            ],
            response_format={"type": "json_object"},
        )

        # Parse response
        response_text = response.choices[0].message.content
        if response_text is None:
            logger.error(f"Empty response from OpenAI for job at {job_url}")
            return {
                "job": {},
                "error": "Empty response from OpenAI",
            }

        job_data = json.loads(response_text)

        # Add metadata
        result = {
            "job": job_data.get("job", {}),
            "timestamp": datetime.now().isoformat(),
        }

        logger.success(f"Successfully processed job at {job_url}")
        return result

    except Exception as e:
        logger.error(f"Error processing job at {job_url} with OpenAI: {e!s}")
        return {
            "job": {},
            "error": str(e),
        }


async def main() -> None:
    """Main function to process all jobs."""
    # Check if prompt template file exists
    if not Path(PROMPT_FILE).exists():
        logger.error(f"Prompt template file '{PROMPT_FILE}' not found")
        return

    # Check if input directory exists
    input_file_path = PIPELINE_INPUT_DIR / INPUT_FILE
    if not input_file_path.exists():
        logger.error(f"Input file {input_file_path} does not exist")
        return

    # Read input file with jobs data
    try:
        with open(input_file_path) as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading input file: {e!s}")
        return

    # Process each company's jobs
    processed_jobs: List[Dict[str, Any]] = []
    total_jobs_processed = 0
    ineligible_jobs_count = 0

    for company_data in data["companies"]:
        company_name: str = company_data["company"]
        html_parser = ParserType[company_data.get("html_parser", "DEFAULT").upper()]
        job_eligibility_selector: List[str] = company_data.get(
            "job_eligibility_selector", []
        )
        job_description_selector: List[str] = company_data.get(
            "job_description_selector", []
        )

        for job in company_data.get("jobs", []):
            job_url: str = job.get("url", "")
            job_title: str = job.get("title", "")
            job_signature: str = job.get("signature", "")

            if not job_url:
                logger.warning(f"Job missing URL, skipping: {job_title}")
                continue

            logger.info(f"Processing new job: {job_title} at {job_url}")
            result = await process_job(
                job_url, job_eligibility_selector, company_name, html_parser
            )

            # Check if there was an error
            if "error" in result:
                logger.error(f"Error processing job {job_title}: {result['error']}")
                continue

            if result and result["job"]:
                total_jobs_processed += 1

                # Only add the job to processed_jobs if it's eligible
                if result["job"].get("eligible", False):
                    result["job"]["html_parser"] = html_parser.value
                    result["job"]["title"] = job_title
                    result["job"]["company"] = company_name
                    result["job"]["application_url"] = job_url
                    result["job"]["signature"] = job_signature
                    result["job"]["job_description_selector"] = job_description_selector
                    processed_jobs.append(result["job"])
                    logger.info(f"Job {job_title} is eligible and added to results")
                else:
                    ineligible_jobs_count += 1
                    logger.info(f"Job {job_title} did not meet eligibility criteria")

            # Delay to avoid rate limiting
            await asyncio.sleep(1)

    # Save results
    output_file = PIPELINE_OUTPUT_DIR / OUTPUT_FILE
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {"jobs": processed_jobs},
            f,
            indent=2,
            ensure_ascii=False,  # This will prevent Unicode escaping
        )

    logger.info(f"Processing complete. Results saved to {output_file}")
    logger.info(f"Processed {len(processed_jobs)} eligible jobs")
    if ineligible_jobs_count > 0:
        logger.warning(f"Ineligible jobs: {ineligible_jobs_count}")


if __name__ == "__main__":
    # Check for API key
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable is not set")
        exit(1)

    logger.info("Starting job eligibility and basic metadata extraction process")
    # Run the async main function
    asyncio.run(main())
    logger.info("Process completed")
