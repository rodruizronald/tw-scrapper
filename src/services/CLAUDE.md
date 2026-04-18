# Services

## Responsibilities

Services are the integration layer with external systems. They own retry logic for transient errors and raise domain-specific exceptions. They do NOT log errors that will be logged by stage processors upstream.

## Service Inventory

- **OpenAIService** - Prompt-based LLM calls. Constructor takes `OpenAIConfig`. Manual retry loop with exponential backoff (rate limits get 3x backoff).
- **WebExtractionService** - Playwright browser automation. Constructor takes `WebExtractionConfig`. Retry loop with fixed delay. Uses parser factory for page-specific strategies.
- **JobDataService / TechDataService** - MongoDB operations via repository pattern. No-arg constructor, uses global repository singletons and `JobMapper`.
- **SupabaseService** - Supabase operations. No-arg constructor, composes 5 repositories. Resilience handled by decorators on repos (not in service itself).
- **JobMetricsService** - Metrics recording. Singleton (`job_metrics_service`). Internal `_retry_operation()` with exponential backoff. Catches all exceptions and continues gracefully (never stops pipeline).

## Exception Rules

- Raise domain exceptions: `OpenAIProcessingError`, `WebExtractionError`, `DatabaseOperationError`
- Always chain with `from e` to preserve traceback
- Don't re-wrap already-typed exceptions (check type first, then re-raise as-is)
- Include context (URL, company name, attempt count) in the exception at creation time

## Parser System (`parsers/`)

Factory pattern with template method:

- **Base**: `SelectorParser` with overridable hooks: `setup()`, `wait_for_content()`, `extract_element()`
- **Factory**: `ParserFactory.create_parser(parser_type, page, selectors)` - falls back to `DefaultParser`
- **Implementations**: `DefaultParser`, `GreenhouseParser`, `AngularParser`, `DynamicJSParser`, `IframeParser`
- **Models**: `ElementResult` (per-selector result), `ParseContext` (page/frame wrapper with `.target` property)

Each parser has different wait strategies (DOM ready, network idle, JS framework detection, iframe loading). The parser type comes from `companies.yaml` per-company config.

To add a new parser:
1. Create class in `parsers/instances.py` extending `SelectorParser`
2. Add `ParserType` enum value in `core/models/jobs.py`
3. Register in `ParserFactory._parsers` dict in `parsers/factory.py`

## Retry Strategies

| Service | Mechanism | Max Retries | Backoff |
|---------|-----------|-------------|---------|
| OpenAI | Manual loop | config.max_retries | Exponential (2^n), rate limits 3^n |
| Web Extraction | Manual loop | config.max_retries | Fixed (config.retry_delay) |
| Metrics | `_retry_operation()` | 2 | Exponential (1s * 2.0^n) |
| Supabase repos | tenacity via `@with_resilience` | Configured in SupabaseConfig | Exponential |

No external tenacity usage except in Supabase decorators. OpenAI and Web services use manual loops.
