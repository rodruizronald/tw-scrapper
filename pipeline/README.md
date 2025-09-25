# Job Pipeline Module

A comprehensive, AI-powered pipeline for extracting and processing job listings from company career pages. This module provides a modular, scalable architecture that combines web scraping with intelligent content analysis using OpenAI and Prefect orchestration.

## 🎯 Overview

The Job Pipeline is designed to automate the extraction of job listings from company career websites. It uses a multi-stage approach where each stage processes and enriches the job data progressively. The pipeline now includes both traditional script-based execution and modern Prefect-orchestrated workflows for enhanced monitoring, error handling, and scalability.

### Key Features

- **🤖 AI-Powered Parsing**: Uses OpenAI GPT models to intelligently extract job information
- **⚡ Concurrent Processing**: Processes multiple companies simultaneously with configurable concurrency
- **🔄 Prefect Orchestration**: Modern workflow orchestration with monitoring, retries, and UI dashboard
- **🛡️ Robust Error Handling**: Comprehensive error handling with graceful failure recovery
- **📊 Rich Monitoring**: Detailed logging, statistics tracking, and processing metrics
- **🔍 Smart Duplicate Detection**: Historical signature-based duplicate filtering
- **📁 Organized Output**: Company-specific directories with structured JSON output
- **⚙️ Flexible Configuration**: Highly configurable for different use cases and environments
- **🔧 Modular Architecture**: Easy to extend with additional processing stages
- **🔄 Integration Ready**: Drop-in replacement for existing job processing scripts
- **🎛️ CLI Interface**: User-friendly command-line interface for easy execution

## 🏗️ Architecture

```
pipeline/
├── core/                      # Core pipeline components
│   ├── __init__.py           # Core module exports
│   ├── pipeline.py           # Main pipeline orchestrator (legacy)
│   ├── config.py             # Configuration management
│   └── models.py             # Data models and types
├── services/                  # Service layer
│   ├── __init__.py           # Service module exports
│   ├── html_service.py       # HTML extraction and parsing
│   ├── openai_service.py     # OpenAI API interactions
│   └── file_service.py       # File operations and data persistence
├── stages/                    # Pipeline stage processors
│   ├── __init__.py           # Stages module exports
│   └── stage_1.py            # Stage 1: Job listing extraction
├── flows/                     # Prefect flow orchestration
│   ├── __init__.py           # Flows module exports
│   ├── stage_1_flow.py       # Stage 1 Prefect flows
│   ├── main_pipeline_flow.py # Main pipeline orchestration
│   └── utils.py              # Flow utility functions
├── tasks/                     # Prefect task definitions
│   ├── __init__.py           # Tasks module exports
│   ├── company_processing.py # Company processing tasks
│   └── utils.py              # Task utility functions
├── utils/                     # Utility modules
│   ├── __init__.py           # Utils module exports
│   └── exceptions.py         # Custom exception classes
├── main.py                   # CLI entry point for Prefect flows
└── README.md                 # This documentation
```

### Design Principles

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Dependency Injection**: Services are injected into processors for testability
3. **Configuration-Driven**: Behavior controlled through configuration objects
4. **Error Isolation**: Errors in one company don't affect others
5. **Extensibility**: Easy to add new stages and services
6. **Observability**: Comprehensive logging and metrics collection
7. **Orchestration**: Prefect flows provide workflow management and monitoring

## 🚀 Quick Start

### Installation

The pipeline module is part of the job scraping project. Ensure you have the required dependencies:

```bash
pip install playwright openai loguru python-dotenv prefect
playwright install  # Install browser binaries
```

### Environment Setup

Create a `.env` file in your project root:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key-here

# Optional - Pipeline Configuration
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=30
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_TO_CONSOLE=true

# Optional - Prefect Configuration
PREFECT_MAX_CONCURRENT=3
PREFECT_FLOW_TIMEOUT=3600
PREFECT_TASK_TIMEOUT=300
PREFECT_DEFAULT_RETRIES=2
PREFECT_RETRY_DELAY=30
```

### Using the CLI Interface (Recommended)

The easiest way to run the pipeline is through the CLI interface:

#### 1. Full Pipeline Execution

```bash
# Run complete pipeline with default settings
python pipeline/main.py run

# Run with custom settings
python pipeline/main.py run \
  --companies-file input/companies.json \
  --prompt-template input/prompts/job_title_url_parser.md \
  --max-concurrent 5 \
  --stages stage_1

# Run multiple stages (when available)
python pipeline/main.py run --stages stage_1,stage_2,stage_3
```

#### 2. Quick Extraction (Stage 1 Only)

```bash
# Quick job extraction with optimized flow
python pipeline/main.py quick

# Quick extraction with custom concurrency
python pipeline/main.py quick --max-concurrent 5
```

#### 3. Execution Time Estimation

```bash
# Estimate how long the pipeline will take
python pipeline/main.py estimate

# Estimate with custom concurrency
python pipeline/main.py estimate --max-concurrent 10
```

#### 4. CLI Help

```bash
# General help
python pipeline/main.py --help

# Command-specific help
python pipeline/main.py run --help
python pipeline/main.py quick --help
python pipeline/main.py estimate --help
```

### CLI Output Examples

```bash
$ python pipeline/main.py run --max-concurrent 3

✅ Configuration loaded
✅ Loaded 5 companies
🎯 Stages to run: stage_1
✅ Input validation passed
⏱️ Estimated duration: 4.2 minutes
🚀 Starting pipeline execution...
🎉 Pipeline execution completed!

📊 PIPELINE EXECUTION SUMMARY
========================================
✅ Successful companies: 4/5 (80.0%)
❌ Failed companies: 1
📋 Total jobs found: 47
💾 Total jobs saved: 43
⏱️ Total processing time: 245.3s
📈 Average time per company: 49.1s

💾 Results saved to: data/20241201/pipeline_stage_1/stage_1_flow_results.json
```

## Programmatic Usage (Advanced)

For advanced use cases, you can use the pipeline programmatically:

### Using Prefect Flows Directly

```python
import asyncio
from pathlib import Path
from pipeline.flows import stage_1_flow
from pipeline.core.config import PipelineConfig
from pipeline.flows.utils import load_companies_from_file

async def main():
    # Load configuration
    config = PipelineConfig.load_from_env()

    # Load companies
    companies = load_companies_from_file(Path("input/companies.json"))

    # Run Stage 1 flow
    results = await stage_1_flow(
        companies=companies,
        config=config,
        prompt_template_path="input/prompts/job_title_url_parser.md",
        max_concurrent_companies=3,
    )

    print(f"✅ Processed {results['successful_companies']} companies")
    print(f"📋 Found {results['total_jobs_found']} jobs")

asyncio.run(main())
```

### Using Legacy Pipeline (Backward Compatibility)

```python
import asyncio
from pathlib import Path
from pipeline import create_pipeline

async def main():
    # Create pipeline with default settings
    pipeline = create_pipeline(
        output_dir="data/pipeline_output",
        openai_api_key="your-api-key-here",
        log_level="INFO"
    )

    # Run the complete pipeline
    results = await pipeline.run_full_pipeline(
        companies_file=Path("input/companies.json"),
        prompt_template_path=Path("input/prompts/job_title_url_parser.md")
    )

    # Check results
    if results["success"]:
        print(f"✅ Successfully processed {results['companies_processed']} companies")
        print(f"📋 Found {results['total_jobs_found']} jobs")
        print(f"💾 Saved {results['total_jobs_saved']} unique jobs")
    else:
        print(f"❌ Pipeline failed: {results['error']}")

# Run the pipeline
asyncio.run(main())
```

## 🎛️ CLI Interface Details

The `pipeline/main.py` file provides a comprehensive command-line interface for the pipeline:

### Main Commands

| Command    | Description                   | Use Case                         |
| ---------- | ----------------------------- | -------------------------------- |
| `run`      | Execute the complete pipeline | Production runs, multiple stages |
| `quick`    | Quick Stage 1 extraction only | Fast job extraction, testing     |
| `estimate` | Estimate execution time       | Planning, resource allocation    |

### Global Options

| Option        | Default | Description                                     |
| ------------- | ------- | ----------------------------------------------- |
| `--log-level` | `INFO`  | Set logging level (DEBUG, INFO, WARNING, ERROR) |

### Run Command Options

| Option                  | Default                                 | Description                   |
| ----------------------- | --------------------------------------- | ----------------------------- |
| `--companies-file, -c`  | `input/companies.json`                  | Path to companies JSON file   |
| `--prompt-template, -p` | `input/prompts/job_title_url_parser.md` | Path to prompt template       |
| `--max-concurrent, -m`  | `3`                                     | Maximum concurrent companies  |
| `--stages`              | `stage_1`                               | Comma-separated stages to run |

### Quick Command Options

| Option                  | Default                                 | Description                  |
| ----------------------- | --------------------------------------- | ---------------------------- |
| `--companies-file, -c`  | `input/companies.json`                  | Path to companies JSON file  |
| `--prompt-template, -p` | `input/prompts/job_title_url_parser.md` | Path to prompt template      |
| `--max-concurrent, -m`  | `3`                                     | Maximum concurrent companies |

### CLI Features

- **Path Resolution**: Automatically resolves relative paths from project root
- **Input Validation**: Validates files and configuration before execution
- **Progress Indicators**: Shows progress with emojis and clear messages
- **Error Handling**: Graceful error handling with helpful error messages
- **Results Summary**: Detailed execution summary with statistics
- **Estimation**: Pre-execution time and resource estimation

## 🔄 Prefect Integration

The pipeline now includes full Prefect integration for workflow orchestration:

### Benefits of Prefect Integration

- **🎛️ Web UI**: Monitor pipeline execution through Prefect's web dashboard
- **🔄 Automatic Retries**: Configurable retry logic for failed tasks
- **⚡ Concurrency Control**: Intelligent task scheduling and resource management
- **📊 Metrics & Logging**: Enhanced monitoring and observability
- **🔍 Task Isolation**: Individual task failure doesn't crash entire pipeline
- **📈 Performance Tracking**: Detailed execution metrics and timing
- **🚨 Alerting**: Built-in alerting for failures and issues

### Prefect Flows Available

1. `stage_1_flow`: Optimized flow for Stage 1 job extraction
2. `main_pipeline_flow`: Multi-stage pipeline orchestration

### Running with Prefect UI

To use the Prefect UI for monitoring:

```bash
# Start Prefect server (in separate terminal)
prefect server start

# Run pipeline (will appear in UI)
python pipeline/main.py run --max-concurrent 5
```

Then visit http://localhost:4200 to see the Prefect dashboard with real-time pipeline monitoring.

### Prefect Task Structure

The pipeline uses the following task hierarchy:

```
stage_1_flow
├── validate_company_data_task (parallel for each company)
├── process_job_listings_task (parallel with concurrency control)
└── aggregate_results_task (final aggregation)
```

Each task includes:

- Automatic retry logic
- Timeout protection
- Detailed logging
- Error isolation
- Progress tracking

## 📋 Configuration

The pipeline uses a hierarchical configuration system with enhanced Prefect support:

### PrefectConfig (New)

Controls Prefect-specific behavior:

```python
@dataclass
class PrefectConfig:
    max_concurrent_companies: int = 3      # Max concurrent company processing
    flow_timeout_seconds: int = 3600       # Flow timeout (1 hour)
    task_timeout_seconds: int = 300        # Task timeout (5 minutes)
    default_retries: int = 2               # Default retry attempts
    retry_delay_seconds: int = 30          # Delay between retries
    log_level: str = "INFO"                # Prefect logging level
```

### Enhanced PipelineConfig

The main configuration now includes Prefect settings:

```python
@dataclass
class PipelineConfig:
    stage_1: StageConfig
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    prefect: PrefectConfig = field(default_factory=PrefectConfig)  # New

    # Project paths for Prefect integration
    project_root: Path = field(default_factory=lambda: Path.cwd())
    input_dir: Path = field(default_factory=lambda: Path("input"))
    output_dir: Path = field(default_factory=lambda: Path("data"))
```

### Environment Variables

All configuration can be controlled via environment variables:

```bash
# Existing variables (unchanged)
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=30
STAGE_1_SAVE_OUTPUT=true
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_TO_CONSOLE=true

# New Prefect variables
PREFECT_MAX_CONCURRENT=3
PREFECT_FLOW_TIMEOUT=3600
PREFECT_TASK_TIMEOUT=300
PREFECT_DEFAULT_RETRIES=2
PREFECT_RETRY_DELAY=30
PREFECT_LOG_LEVEL=INFO
```

### Configuration Loading

```python
# Load from environment (recommended)
config = PipelineConfig.load_from_env()

# Load from specific .env file
config = PipelineConfig.load_from_env(Path(".env.production"))

# Load from dictionary
config = PipelineConfig.from_dict({
    "stage_1": {"output_dir": "data/output"},
    "prefect": {"max_concurrent_companies": 5}
})
```

## 📊 Data Models

### CompanyData

Represents a company to be processed:

```python
@dataclass
class CompanyData:
    name: str                           # Company name
    career_url: str                     # URL to company's career page
    job_board_selector: List[str]       # CSS selectors for job listings
    html_parser: str = "default"        # Parser type (default, angular, greenhouse)
    enabled: bool = True                # Whether to process this company
```

### JobData

Represents an extracted job listing:

```python
@dataclass
class JobData:
    title: str          # Job title
    url: str           # Job posting URL
    signature: str     # Unique signature for duplicate detection
    company: str       # Company name
    timestamp: str     # Processing timestamp
```

### ProcessingResult

Represents the result of processing a company:

```python
@dataclass
class ProcessingResult:
    success: bool                    # Whether processing succeeded
    company_name: str               # Company name
    jobs_found: int = 0             # Number of jobs found
    jobs_saved: int = 0             # Number of unique jobs saved
    processing_time: float = 0.0    # Processing time in seconds
    output_path: Optional[str] = None  # Path to output file
    error: Optional[str] = None     # Error message if failed
    error_type: Optional[str] = None # Error type for categorization
    retryable: bool = True          # Whether error is retryable
    stage: str = "unknown"          # Processing stage
    start_time: Optional[datetime] = None  # Start timestamp
    end_time: Optional[datetime] = None    # End timestamp
```

## 📁 Input/Output Formats

### Companies Input Format

The companies file should be a JSON array of company objects:

```json
[
  {
    "name": "Tech Company A",
    "career_url": "https://company-a.com/careers",
    "job_board_selector": [
      "[data-testid='job-listing']",
      ".job-item",
      ".career-opportunity"
    ],
    "html_parser": "default",
    "enabled": true
  },
  {
    "name": "Tech Company B",
    "career_url": "https://company-b.com/jobs",
    "job_board_selector": [".career-item", ".job-posting"],
    "html_parser": "angular",
    "enabled": true
  }
]
```

### Prompt Template Format

The prompt template should be a Markdown file with placeholders:

````markdown
# Job Listing Extraction Prompt

You are an AI assistant that extracts job listings from HTML content.

## Instructions

1. Extract all job listings from the provided HTML
2. For each job, extract the title and URL
3. Return the results in the specified JSON format

## HTML Content

{html_content}

## Expected Output Format

```json
{
  "jobs": [
    {
      "title": "Software Engineer",
      "url": "https://company.com/jobs/123"
    }
  ]
}
```
````

```

### Output Structure

The pipeline creates a structured output directory with timestamp-based organization:

```

data/
└── 20241201/ # Date-based directory (YYYYMMDD)
└── pipeline_stage_1/ # Stage-specific output
├── tech_company_a/ # Company-specific directory
│ ├── jobs_stage_1.json # Extracted jobs
│ └── historical_jobs.json # Historical signatures
├── tech_company_b/
│ ├── jobs_stage_1.json
│ └── historical_jobs.json
├── processing_summary.json # Overall processing summary
├── stage_1_flow_results.json # Prefect flow results
└── pipeline.log # Detailed processing logs

````

### Enhanced Output with Prefect

When using Prefect flows, additional output files are created:

- `stage_1_flow_results.json`: Detailed Prefect flow execution results
- Enhanced logging: Prefect-specific logs with task execution details
- Metrics tracking: Performance metrics for each task and flow

## 🔧 Services

### HTMLExtractor Service

Handles web scraping and HTML extraction:

```python
from pipeline.services import HTMLExtractor

extractor = HTMLExtractor()
html_content = await extractor.extract_html(
    url="https://company.com/careers",
    selectors=[".job-listing", ".career-item"],
    parser_type=ParserType.DEFAULT
)
````

Features:

- Multiple parser support (Default, Angular, Greenhouse)
- Configurable CSS selectors
- Error handling and retries
- Browser automation with Playwright

### OpenAIService

Manages OpenAI API interactions:

```python
from pipeline.services import OpenAIService

service = OpenAIService(config.openai)
result = await service.parse_job_listings(
    html_content="<html>...</html>",
    prompt_template="Extract jobs from this HTML...",
    company_name="Tech Company"
)
```

Features:

- Configurable models and parameters
- Automatic retry logic
- Rate limiting
- Error handling and logging

### FileService

Handles file operations and data persistence:

```python
from pipeline.services import FileService

service = FileService(config.stage_1)
await service.save_jobs(jobs, "Tech Company")
historical_signatures = await service.load_historical_signatures("Tech Company")
```

Features:

- Company-specific file organization
- Historical signature management
- JSON serialization
- Directory management

## 🎯 Stage 1: Job Listing Extraction

Stage 1 is the core job extraction stage that processes company career pages and extracts job listings.

### Process Flow

1. **Company Validation**: Validates company data and checks if enabled
2. **HTML Extraction**: Extracts HTML content from career page using appropriate parser
3. **AI Parsing**: Uses OpenAI to parse job listings from HTML content
4. **Data Processing**: Validates and structures job data
5. **Duplicate Filtering**: Filters out duplicate jobs using historical signatures
6. **File Persistence**: Saves results to company-specific files

### Usage Options

#### Option 1: CLI (Recommended)

```bash
# Single stage execution
python pipeline/main.py run --stages stage_1

# Quick extraction
python pipeline/main.py quick
```

#### Option 2: Prefect Flow

```python
from pipeline.flows import stage_1_flow

results = await stage_1_flow(
    companies=companies,
    config=config,
    prompt_template_path="input/prompts/job_title_url_parser.md",
    max_concurrent_companies=3,
)
```

#### Option 3: Direct Stage Processor

```python
from pipeline.stages import Stage1Processor

processor = Stage1Processor(config, "path/to/prompt_template.md")

# Process single company
result = await processor.process_single_company(company_data)

# Process multiple companies (legacy)
results = await processor.process_companies(companies_list)
```

### Error Handling

Stage 1 includes comprehensive error handling:

- **Company-level errors**: Isolated to individual companies
- **HTML extraction errors**: Retry logic and fallback strategies
- **OpenAI API errors**: Automatic retries with exponential backoff
- **File operation errors**: Graceful handling with detailed error messages
- **Prefect task isolation**: Failed companies don't affect others

## 🛡️ Error Handling

The pipeline includes a comprehensive error handling system with custom exception types:

### Exception Hierarchy

```
PipelineError                    # Base pipeline exception
├── CompanyProcessingError       # Company-specific processing errors
├── HTMLExtractionError         # Web scraping and HTML extraction errors
├── OpenAIProcessingError        # OpenAI API interaction errors
├── FileOperationError          # File system operation errors
├── ValidationError             # Data validation errors
└── ConfigurationError          # Configuration-related errors
```

### Error Handling Examples

```python
from pipeline import (
    PipelineError,
    CompanyProcessingError,
    HTMLExtractionError,
    OpenAIProcessingError
)

try:
    results = await pipeline.run_full_pipeline(...)
except CompanyProcessingError as e:
    print(f"Company processing failed: {e.company_name} - {e}")
except HTMLExtractionError as e:
    print(f"HTML extraction failed: {e}")
except OpenAIProcessingError as e:
    print(f"OpenAI API error: {e}")
except PipelineError as e:
    print(f"General pipeline error: {e}")
```

### Error Recovery with Prefect

Prefect enhances error handling with:

- **Automatic Retries**: Configurable retry logic for transient failures
- **Task Isolation**: Errors in one task don't affect others
- **Error Categorization**: Retryable vs non-retryable errors
- **Detailed Error Tracking**: Full error context in Prefect UI
- **Graceful Degradation**: Pipeline continues with partial failures

## 📈 Performance and Monitoring

### Performance Features

- **Concurrent Processing**: Processes multiple companies simultaneously
- **Configurable Concurrency**: Control the number of concurrent operations
- **Rate Limiting**: Respects API rate limits and website politeness
- **Memory Efficiency**: Streams processing for large datasets
- **Caching**: Intelligent caching of results and signatures
- **Prefect Optimization**: Task-level parallelization and resource management

### Monitoring and Metrics

The pipeline provides comprehensive monitoring through multiple channels:

#### 1. Application Logging (Loguru)

**Processing Statistics:**

- Companies processed/successful/failed
- Jobs found/saved/duplicates filtered
- Processing times per company and overall
- Success rates and error frequencies

**Logging Levels:**

- `DEBUG`: Detailed debugging information including API calls
- `INFO`: General progress information and statistics
- `WARNING`: Non-critical issues and warnings
- `ERROR`: Error conditions and failures
- `CRITICAL`: Critical system errors

#### 2. Prefect Monitoring

**Flow-Level Metrics:**

- Flow execution time and status
- Task success/failure rates
- Resource utilization
- Retry attempts and patterns

**Task-Level Metrics:**

- Individual task execution times
- Task state transitions
- Error details and stack traces
- Input/output data sizes

#### 3. CLI Progress Indicators

Real-time progress updates with:

- Company processing status
- Job extraction progress
- Error summaries
- Final execution statistics

### Log Output Examples

#### Application Logs (Loguru)

```
2024-12-01 10:30:15 | INFO     | Starting Stage 1: Job Listing Extraction
2024-12-01 10:30:16 | INFO     | 🏢 Starting processing for company: Tech Company A
2024-12-01 10:30:18 | DEBUG    | Extracted 1,234 characters of HTML content
2024-12-01 10:30:20 | INFO     | 🤖 Parsing job listings with OpenAI (gpt-4o-mini)
2024-12-01 10:30:22 | INFO     | ✅ Tech Company A: Found 5 jobs, saved 4 unique jobs in 6.45s
2024-12-01 10:30:22 | WARNING  | Filtered 1 duplicate job for Tech Company A
```

#### Prefect Logs

```
10:30:15.123 | INFO    | Flow run 'stage-1-20241201-103015' - Starting flow execution
10:30:16.456 | INFO    | Task run 'validate_company_data_task-1' - Task started
10:30:16.789 | INFO    | Task run 'validate_company_data_task-1' - Task completed successfully
10:30:17.012 | INFO    | Task run 'process_job_listings_task-1' - Task started
10:30:23.456 | INFO    | Task run 'process_job_listings_task-1' - Task completed successfully
```

### Performance Tuning

#### Speed Optimization

```python
config = PipelineConfig(
    openai=OpenAIConfig(
        model="gpt-4o-mini",  # Faster model
        timeout=15,           # Shorter timeout
        max_retries=2         # Fewer retries
    ),
    prefect=PrefectConfig(
        max_concurrent_companies=5,  # Higher concurrency
        task_timeout_seconds=180,    # Shorter task timeout
        default_retries=1            # Fewer retries
    )
)
```

#### Accuracy Optimization

```python
config = PipelineConfig(
    openai=OpenAIConfig(
        model="gpt-4",        # More accurate model
        timeout=60,           # Longer timeout
        max_retries=5         # More retries
    ),
    prefect=PrefectConfig(
        max_concurrent_companies=2,  # Lower concurrency for stability
        task_timeout_seconds=600,    # Longer task timeout
        default_retries=3            # More retries
    )
)
```

## 🔄 Migration Guide

### From Legacy Scripts to Pipeline

If you're migrating from the original script-based approach:

#### Before (Legacy Scripts)

```bash
python scripts/job_stage_1.py
```

#### After (Pipeline CLI)

```bash
python pipeline/main.py run --stages stage_1
```

### Benefits of Migration

- **Better Error Handling**: Individual company failures don't crash entire pipeline
- **Concurrency**: Process multiple companies simultaneously
- **Monitoring**: Real-time progress and detailed metrics
- **Retries**: Automatic retry logic for transient failures
- **Scalability**: Easy to scale up processing

### Backward Compatibility

The pipeline maintains backward compatibility:

```python
# Legacy approach still works
from pipeline import JobPipeline, PipelineConfig

config = PipelineConfig.load_from_env()
pipeline = JobPipeline(config)
results = await pipeline.run_full_pipeline(...)

# New Prefect approach (recommended)
from pipeline.flows import stage_1_flow

results = await stage_1_flow(...)
```

## 🚀 Best Practices

### 1. Configuration Management

- Use environment variables for sensitive data (API keys)
- Create environment-specific `.env` files
- Validate configuration before execution

### 2. Error Handling

- Monitor Prefect UI for task failures
- Set up appropriate retry policies
- Use error categorization for better debugging

### 3. Performance Optimization

- Start with lower concurrency and increase gradually
- Monitor API rate limits
- Use quick mode for testing

### 4. Monitoring

- Use both application logs and Prefect UI
- Set up log rotation for file logs
- Monitor execution times and success rates

### 5. Development Workflow

```bash
# 1. Test with single company first
python pipeline/main.py quick --companies-file input/test_companies.json

# 2. Estimate full execution
python pipeline/main.py estimate

# 3. Run full pipeline
python pipeline/main.py run --max-concurrent 3
```

---

For more information, examples, and advanced usage patterns, please refer to the individual module documentation and example scripts in the repository.
