# Updated Project Structure

```
├── parsers/                    # Low-level parsing logic
│   ├── __init__.py
│   ├── models.py              # Data models
│   ├── base.py                # Base parser class
│   ├── implementations.py     # Concrete parsers
│   └── factory.py             # Parser factory
│
├── services/                   # High-level orchestration services
│   ├── __init__.py
│   └── extraction.py          # Web extraction service
│
├── input/
│   ├── companies.json
│   └── prompts/
│
├── job_stage_1.py
├── job_stage_2.py
├── job_stage_3.py
├── job_stage_4.py
├── README.md
└── selector_tester.py

```

## Architecture Rationale

### Why a Separate Services Layer?

1. **Separation of Concerns**:

   - **Parsers**: Focus on HOW to extract (parsing strategies)
   - **Services**: Focus on ORCHESTRATION (browser management, error handling, retries)

2. **Single Responsibility Principle**:

   - Parsers don't manage browsers
   - Services don't know parsing details

3. **Dependency Direction**:

   - Services depend on Parsers (not vice versa)
   - Clean dependency hierarchy

4. **Reusability**:
   - Different services can use the same parsers
   - Parsers can be used without the service layer

## Usage Examples

### Simple Usage in Your Scripts

```python
# job_stage_1.py
from services import extract_elements_by_selectors
from parsers import ParserType

async def extract_job_listings():
    results = await extract_elements_by_selectors(
        url="https://example.com/jobs",
        selectors=[".job-title", ".job-description"],
        parser_type=ParserType.DEFAULT
    )
    return results
```

### Advanced Usage with Configuration

```python
# job_stage_2.py
from services import WebExtractionService, ExtractionConfig, BrowserConfig
from parsers import ParserType

async def extract_with_custom_config():
    # Configure extraction behavior
    config = ExtractionConfig(
        browser_config=BrowserConfig(
            headless=False,
            viewport={'width': 1920, 'height': 1080},
            user_agent="Custom User Agent",
            timeout=60000
        ),
        parser_type=ParserType.ANGULAR,
        retry_on_failure=True,
        max_retries=3
    )

    # Create service instance
    service = WebExtractionService(config)

    # Extract with retry logic
    results = await service.extract_with_retry(
        url="https://complex-site.com",
        selectors=["#dynamic-content", ".lazy-loaded"]
    )

    return results
```

### Batch Processing

```python
# job_stage_3.py
from services import extract_from_urls_batch
from parsers import ParserType

async def process_multiple_companies():
    url_configs = [
        {
            'url': 'https://company1.com/careers',
            'selectors': ['.job-post'],
            'parser_type': ParserType.DEFAULT
        },
        {
            'url': 'https://company2.greenhouse.io',
            'selectors': ['.opening'],
            'parser_type': ParserType.GREENHOUSE
        },
        {
            'url': 'https://angular-app.com/jobs',
            'selectors': ['app-job-listing'],
            'parser_type': ParserType.ANGULAR
        }
    ]

    results = await extract_from_urls_batch(url_configs)

    for url, elements in results.items():
        print(f"Results for {url}:")
        for element in elements:
            if element.found:
                print(f"  ✓ {element.selector}")
```

## Benefits of This Architecture

1. **DRY Principle**: No code duplication across job_stage files
2. **Testability**: Each layer can be tested independently
3. **Flexibility**: Easy to add new features (caching, rate limiting, etc.)
4. **Maintainability**: Clear boundaries between components
5. **Scalability**: Easy to add new parsers or services

## Migration Path

1. Create the `services/` directory
2. Add the `extraction.py` and `__init__.py` files
3. Update your scripts to import from `services` instead of duplicating code
4. Gradually refactor existing code to use the service layer

This architecture follows Python best practices and clean code principles while maintaining flexibility for future enhancements.
