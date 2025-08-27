
"""
Example script showing how to run the Stage 1 Prefect flow.

This script demonstrates:
1. Loading configuration and companies
2. Validating inputs
3. Running the flow
4. Handling results
"""

import asyncio
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.core.config import PipelineConfig
from pipeline.flows import (
    stage_1_flow,
    stage_1_single_company_flow,
    load_companies_from_file,
    validate_flow_inputs,
    estimate_flow_duration,
    create_flow_summary_report,
)


async def run_full_pipeline():
    """Run the full Stage 1 pipeline with all companies."""
    
    # Configuration
    companies_file = project_root / "input" / "companies.json"
    prompt_template_path = str(project_root / "input" / "prompts" / "job_title_url_parser.md")
    max_concurrent_companies = 3
    
    print("🚀 Starting Stage 1 Pipeline")
    print("=" * 50)
    
    try:
        # Load configuration
        config = PipelineConfig.load_from_env()
        print(f"✅ Configuration loaded")
        
        # Load companies
        companies = load_companies_from_file(companies_file)
        print(f"✅ Loaded {len(companies)} companies from {companies_file}")
        
        # Validate inputs
        validate_flow_inputs(companies, config, prompt_template_path)
        print(f"✅ Input validation passed")
        
        # Estimate duration
        duration_estimate = estimate_flow_duration(companies, max_concurrent_companies)
        print(f"⏱️ Estimated duration: {duration_estimate['estimated_duration_minutes']:.1f} minutes")
        print(f"📊 Will process {duration_estimate['total_companies']} companies in {duration_estimate['batches']} batches")
        
        # Run the flow
        print("\n🏭 Starting flow execution...")
        results = await stage_1_flow(
            companies=companies,
            config=config,
            prompt_template_path=prompt_template_path,
            max_concurrent_companies=max_concurrent_companies,
        )
        
        # Display results
        print("\n" + create_flow_summary_report(results))
        
        return results
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        raise


async def run_single_company_test():
    """Run a test with a single company."""
    
    # Configuration
    companies_file = project_root / "input" / "companies.json"
    prompt_template_path = str(project_root / "input" / "prompts" / "job_title_url_parser.md")
    
    print("🧪 Testing Single Company Processing")
    print("=" * 50)
    
    try:
        # Load configuration
        config = PipelineConfig.load_from_env()
        
        # Load companies and pick the first enabled one
        companies = load_companies_from_file(companies_file)
        enabled_companies = [c for c in companies if c.enabled]
        
        if not enabled_companies:
            print("❌ No enabled companies found for testing")
            return
        
        test_company = enabled_companies[0]
        print(f"🏢 Testing with company: {test_company.name}")
        
        # Run single company flow
        result = await stage_1_single_company_flow(
            company=test_company,
            config=config,
            prompt_template_path=prompt_template_path,
        )
        
        # Display result
        print(f"\n📊 Test Result:")
        print(f"✅ Success: {result.get('success', False)}")
        print(f"📋 Jobs found: {result.get('jobs_found', 0)}")
        print(f"💾 Jobs saved: {result.get('jobs_saved', 0)}")
        print(f"⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
        
        if not result.get('success', False):
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


async def main():
    """Main function to choose between full pipeline or single company test."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        await run_single_company_test()
    else:
        await run_full_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
