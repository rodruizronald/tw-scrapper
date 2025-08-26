# Job Pipeline Module

A comprehensive, AI-powered pipeline for extracting and processing job listings from company career pages. This module provides a modular, scalable architecture that combines web scraping with intelligent content analysis using OpenAI.

## 🎯 Overview

The Job Pipeline is designed to automate the extraction of job listings from company career websites. It uses a multi-stage approach where each stage processes and enriches the job data progressively. Currently, Stage 1 (Job Listing Extraction) is fully implemented, with the architecture ready for additional stages.

### Key Features

- **🤖 AI-Powered Parsing**: Uses OpenAI GPT models to intelligently extract job information
- **⚡ Concurrent Processing**: Processes multiple companies simultaneously with configurable concurrency
- **🛡️ Robust Error Handling**: Comprehensive error handling with graceful failure recovery
- **📊 Rich Monitoring**: Detailed logging, statistics tracking, and processing metrics
- **🔍 Smart Duplicate Detection**: Historical signature-based duplicate filtering
- **📁 Organized Output**: Company-specific directories with structured JSON output
- **⚙️ Flexible Configuration**: Highly configurable for different use cases and environments
- **🔧 Modular Architecture**: Easy to extend with additional processing stages
- **🔄 Integration Ready**: Drop-in replacement for existing job processing scripts

## 🏗️ Architecture

```
pipeline/
├── core/                      # Core pipeline components
│   ├── __init__.py           # Core module exports
│   ├── pipeline.py           # Main pipeline orchestrator
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
├── utils/                     # Utility modules
│   ├── __init__.py           # Utils module exports
│   └── exceptions.py         # Custom exception classes
└── README.md                 # This documentation
```

### Design Principles

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Dependency Injection**: Services are injected into processors for testability
3. **Configuration-Driven**: Behavior controlled through configuration objects
4. **Error Isolation**: Errors in one company don't affect others
5. **Extensibility**: Easy to add new stages and services
6. **Observability**: Comprehensive logging and metrics collection

## 🚀 Quick Start

### Installation

The pipeline module is part of the job scraping project. Ensure you have the required dependencies:

```bash
pip install playwright openai loguru python-dotenv
playwright install  # Install browser binaries
```

### Basic Usage

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

### Advanced Configuration

```python
from pipeline import JobPipeline, PipelineConfig, StageConfig, OpenAIConfig, LoggingConfig

# Create custom configuration
config = PipelineConfig(
    stage_1=StageConfig(
        output_dir=Path("data/custom_output"),
        save_output=True
    ),
    openai=OpenAIConfig(
        model="gpt-4",
        max_retries=5,
        timeout=60,
        api_key="your-api-key"
    ),
    logging=LoggingConfig(
        level="DEBUG",
        log_to_file=True,
        log_to_console=True
    )
)

# Initialize pipeline with custom config
pipeline = JobPipeline(config)

# Load companies and run
companies = pipeline.load_companies_from_file(Path("input/companies.json"))
results = await pipeline.run_stage_1(companies, Path("input/prompts/job_title_url_parser.md"))
```

## 📋 Configuration

The pipeline uses a hierarchical configuration system with the following components:

### StageConfig

Controls stage-specific behavior:

```python
@dataclass
class StageConfig:
    output_dir: Path          # Directory for stage output
    save_output: bool = True  # Whether to save results to files
```

### OpenAIConfig

Controls OpenAI API integration:

```python
@dataclass
class OpenAIConfig:
    model: str = "gpt-4o-mini"    # OpenAI model to use
    max_retries: int = 3          # Maximum API retry attempts
    timeout: int = 30             # Request timeout in seconds
    api_key: str | None = None    # API key (uses env var if None)
```

### LoggingConfig

Controls logging behavior:

```python
@dataclass
class LoggingConfig:
    level: str = "INFO"           # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_to_file: bool = True      # Enable file logging
    log_to_console: bool = True   # Enable console logging
```

### PipelineConfig

Main configuration container:

```python
@dataclass
class PipelineConfig:
    stage_1: StageConfig
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
```

### Configuration from File

You can load configuration from a JSON file:

```json
{
  "stage_1": {
    "output_dir": "data/pipeline_output",
    "save_output": true
  },
  "openai": {
    "model": "gpt-4o-mini",
    "max_retries": 3,
    "timeout": 30
  },
  "logging": {
    "level": "INFO",
    "log_to_file": true,
    "log_to_console": true
  }
}
```

```python
pipeline = JobPipeline.from_config_file(Path("config/pipeline_config.json"))
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

The pipeline creates a structured output directory:

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
└── pipeline.log # Detailed processing logs

````

### Job Output Format

Each company's `jobs_stage_1.json` contains:

```json
{
  "company": "Tech Company A",
  "jobs": [
    {
      "title": "Senior Software Engineer",
      "url": "https://company-a.com/jobs/senior-engineer-123",
      "signature": "a1b2c3d4e5f6...",
      "company": "Tech Company A",
      "timestamp": "2024-12-01T10:30:00-08:00"
    }
  ],
  "total_jobs": 1,
  "processing_time": 2.45,
  "timestamp": "2024-12-01T10:30:00-08:00"
}
````

### Processing Summary Format

The `processing_summary.json` contains overall statistics:

```json
{
  "success": true,
  "pipeline_start_time": "2024-12-01T10:25:00-08:00",
  "pipeline_end_time": "2024-12-01T10:35:00-08:00",
  "total_processing_time": 600.0,
  "companies_processed": 5,
  "companies_successful": 4,
  "companies_failed": 1,
  "total_jobs_found": 25,
  "total_jobs_saved": 23,
  "stage_1_results": [...]
}
```

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
```

**Features:**

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

**Features:**

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

**Features:**

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

### Usage

```python
from pipeline.stages import Stage1Processor

processor = Stage1Processor(config, "path/to/prompt_template.md")

# Process single company
result = await processor.process_company(company_data)

# Process multiple companies
results = await processor.process_companies(companies_list)
```

### Error Handling

Stage 1 includes comprehensive error handling:

- **Company-level errors**: Isolated to individual companies
- **HTML extraction errors**: Retry logic and fallback strategies
- **OpenAI API errors**: Automatic retries with exponential backoff
- **File operation errors**: Graceful handling with detailed error messages

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

### Error Recovery

- **Company-level isolation**: Errors in one company don't affect others
- **Automatic retries**: Configurable retry logic for transient failures
- **Graceful degradation**: Pipeline continues processing even with partial failures
- **Detailed error reporting**: Comprehensive error messages with context

## 📈 Performance and Monitoring

### Performance Features

- **Concurrent Processing**: Processes multiple companies simultaneously
- **Configurable Concurrency**: Control the number of concurrent operations
- **Rate Limiting**: Respects API rate limits and website politeness
- **Memory Efficiency**: Streams processing for large datasets
- **Caching**: Intelligent caching of results and signatures

### Monitoring and Metrics

The pipeline provides comprehensive monitoring:

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

### Log Output Examples

```
2024-12-01 10:30:15 | INFO     | Starting Stage 1: Job Listing Extraction
2024-12-01 10:30:16 | INFO     | 🏢 Starting processing for company: Tech Company A
2024-12-01 10:30:18 | DEBUG    | Extracted 1,234 characters of HTML content
2024-12-01 10:30:20 | INFO     | 🤖 Parsing job listings with OpenAI (gpt-4o-mini)
2024-12-01 10:30:22 | INFO     | ✅ Tech Company A: Found 5 jobs, saved 4 unique jobs in 6.45s
2024-12-01 10:30:22 | WARNING  | Filtered 1 duplicate job for Tech Company A
```

### Performance Tuning

```python
# Optimize for speed
config = PipelineConfig(
    openai=OpenAIConfig(
        model="gpt-4o-mini",  # Faster model
        timeout=15,           # Shorter timeout
        max_retries=2         # Fewer retries
    )
)

# Optimize for accuracy
config = PipelineConfig(
    openai=OpenAIConfig(
        model="gpt-4",        # More accurate model
        timeout=60,           # Longer timeout
        max_retries=5         # More retries
    )
)
```

---

For more information, examples, and advanced usage patterns, please refer to the individual module documentation and example scripts in the repository.
