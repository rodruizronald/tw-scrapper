"""
Basic Pipeline Usage Examples

This file demonstrates the most common ways to use the job pipeline
for extracting job listings from company career pages.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Import the pipeline
from pipeline import (
    CompanyData,
    ConfigurationError,
    FileOperationError,
    JobPipeline,
    LoggingConfig,
    OpenAIConfig,
    PipelineConfig,
    PipelineError,
    Stage1Processor,
    StageConfig,
    create_pipeline,
)

# Load environment variables
load_dotenv()


async def basic_example():
    """
    Basic example: Create pipeline with default settings and run it.
    """
    print("🚀 Basic Pipeline Example")
    print("=" * 50)

    # Create pipeline with default configuration
    pipeline = create_pipeline(
        output_dir="data/basic_example",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        log_level="INFO",
    )

    # Define input files
    companies_file = Path("input/companies.json")
    prompt_template = Path("input/prompts/job_title_url_parser.md")

    # Run the pipeline
    results = await pipeline.run_full_pipeline(
        companies_file=companies_file, prompt_template_path=prompt_template
    )

    # Print results summary
    if results["success"]:
        print("✅ Pipeline completed successfully!")
        print(f"📊 Companies processed: {results['companies_processed']}")
        print(f"✅ Successful: {results['companies_successful']}")
        print(f"❌ Failed: {results['companies_failed']}")
        print(f"📋 Jobs found: {results['total_jobs_found']}")
        print(f"💾 Jobs saved: {results['total_jobs_saved']}")
        print(f"⏱️  Total time: {results['total_processing_time']:.2f}s")
    else:
        print(f"❌ Pipeline failed: {results['error']}")

    return results


async def advanced_example():
    """
    Advanced example: Custom configuration and error handling.
    """
    print("\n🔧 Advanced Pipeline Example")
    print("=" * 50)

    # Create custom configuration
    config = PipelineConfig(
        stage_1=StageConfig(output_dir=Path("data/advanced_example"), save_output=True),
        openai=OpenAIConfig(
            model="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=5,
            timeout=60,
        ),
        logging=LoggingConfig(level="DEBUG", log_to_file=True, log_to_console=True),
    )

    # Initialize pipeline with custom config
    pipeline = JobPipeline(config)

    # Print configuration summary
    config_summary = pipeline.get_config_summary()
    print("📋 Configuration Summary:")
    for section, settings in config_summary.items():
        print(f"  {section}:")
        for key, value in settings.items():
            print(f"    {key}: {value}")

    try:
        # Load companies
        companies_file = Path("input/companies.json")
        companies = pipeline.load_companies_from_file(companies_file)
        print(f"📋 Loaded {len(companies)} companies")

        # Run just Stage 1
        prompt_template = Path("input/prompts/job_title_url_parser.md")
        stage_1_results = await pipeline.run_stage_1(companies, prompt_template)

        # Analyze results
        successful = [r for r in stage_1_results if r.success]
        failed = [r for r in stage_1_results if not r.success]

        print("\n📊 Stage 1 Results:")
        print(f"✅ Successful companies: {len(successful)}")
        print(f"❌ Failed companies: {len(failed)}")

        if failed:
            print("\n❌ Failed Companies:")
            for result in failed:
                print(f"  - {result.company_name}: {result.error}")

        if successful:
            print("\n✅ Successful Companies:")
            for result in successful:
                print(
                    f"  - {result.company_name}: {result.jobs_found} jobs found, "
                    f"{result.jobs_saved} saved ({result.processing_time:.2f}s)"
                )

        return stage_1_results

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return None


async def single_company_example():
    """
    Example: Process a single company with detailed monitoring.
    """
    print("\n🏢 Single Company Example")
    print("=" * 50)

    # Create a single company data object
    company = CompanyData(
        name="Example Tech Company",
        career_url="https://example-tech.com/careers",
        job_board_selector=[
            "[data-testid='job-listing']",
            ".job-item",
            ".career-opportunity",
        ],
        html_parser="default",
        enabled=True,
    )

    # Create configuration
    config = PipelineConfig(
        stage_1=StageConfig(output_dir=Path("data/single_company")),
        openai=OpenAIConfig(api_key=os.getenv("OPENAI_API_KEY")),
    )

    # Initialize Stage 1 processor
    processor = Stage1Processor(config, "input/prompts/job_title_url_parser.md")

    # Process the company
    print(f"🔄 Processing: {company.name}")
    result = await processor.process_company(company)

    # Print detailed results
    if result.success:
        print("✅ Success!")
        print(f"📋 Jobs found: {result.jobs_found}")
        print(f"💾 Jobs saved: {result.jobs_saved}")
        print(f"⏱️  Processing time: {result.processing_time:.2f}s")
        if result.output_path:
            print(f"📁 Output saved to: {result.output_path}")
    else:
        print(f"❌ Failed: {result.error}")

    return result


async def batch_processing_example():
    """
    Example: Process companies in batches with custom error handling.
    """
    print("\n📦 Batch Processing Example")
    print("=" * 50)

    # Create multiple companies
    companies = [
        CompanyData(
            name="Tech Company A",
            career_url="https://company-a.com/careers",
            job_board_selector=[".job-listing"],
            html_parser="default",
            enabled=True,
        ),
        CompanyData(
            name="Tech Company B",
            career_url="https://company-b.com/jobs",
            job_board_selector=[".career-item"],
            html_parser="angular",
            enabled=True,
        ),
        CompanyData(
            name="Disabled Company",
            career_url="https://disabled.com/careers",
            job_board_selector=[".job"],
            html_parser="default",
            enabled=False,  # This will be skipped
        ),
    ]

    # Create configuration
    config = PipelineConfig(
        stage_1=StageConfig(output_dir=Path("data/batch_processing"))
    )

    # Initialize processor
    processor = Stage1Processor(config, "input/prompts/job_title_url_parser.md")

    # Process companies
    print(f"🔄 Processing {len(companies)} companies...")
    results = await processor.process_companies(companies)

    # Analyze batch results
    enabled_companies = [c for c in companies if c.enabled]
    print("📊 Batch Results:")
    print(f"📋 Total companies: {len(companies)}")
    print(f"✅ Enabled companies: {len(enabled_companies)}")
    print(f"🔄 Processed companies: {len(results)}")

    for result in results:
        status = "✅" if result.success else "❌"
        print(
            f"  {status} {result.company_name}: "
            f"{result.jobs_found if result.success else result.error}"
        )

    return results


async def error_handling_example():
    """
    Example: Demonstrate error handling and recovery.
    """
    print("\n🛡️  Error Handling Example")
    print("=" * 50)

    try:
        # Try to load pipeline from non-existent config
        pipeline = JobPipeline.from_config_file(Path("non_existent_config.json"))
    except FileOperationError as e:
        print(f"📁 File error caught: {e}")
    except ConfigurationError as e:
        print(f"⚙️  Configuration error caught: {e}")

    try:
        # Try to load companies from non-existent file
        pipeline = create_pipeline("data/error_example")
        companies = pipeline.load_companies_from_file(
            Path("non_existent_companies.json")
        )
    except FileOperationError as e:
        print(f"📁 Companies file error caught: {e}")

    try:
        # Try to run pipeline with invalid prompt template
        pipeline = create_pipeline("data/error_example")
        companies = []  # Empty companies list
        await pipeline.run_stage_1(companies, Path("non_existent_prompt.md"))
    except PipelineError as e:
        print(f"🔧 Pipeline error caught: {e}")

    print("✅ Error handling demonstration complete")


async def main():
    """Run all examples."""
    print("🎯 Job Pipeline Usage Examples")
    print("=" * 80)

    # Run examples
    await basic_example()
    await advanced_example()
    await single_company_example()
    await batch_processing_example()
    await error_handling_example()

    print("\n🎉 All examples completed!")


if __name__ == "__main__":
    # Ensure required files exist
    required_files = ["input/companies.json", "input/prompts/job_title_url_parser.md"]

    missing_files = [f for f in required_files if not Path(f).exists()]
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease create these files before running the examples.")
    else:
        asyncio.run(main())
