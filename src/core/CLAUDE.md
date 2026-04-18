# Core

## Models (`models/`)

**Job model** evolves through pipeline stages with optional stage-specific data:
- Stage 1: `title`, `url`, `signature` (SHA256 of URL), `company`
- Stage 2: adds `details: JobDetails | None` (location, work_mode, employment_type, etc.)
- Stage 3: adds `requirements: JobRequirements | None` (responsibilities, skills, benefits)
- Stage 4: adds `technologies: JobTechnologies | None` (technology list with required flag)

Properties `is_stage_X_processed` and `is_eligible` check completion status.

**Enums** (all `StrEnum`): `Location` (Costa Rican provinces), `WorkMode`, `EmploymentType`, `ExperienceLevel`, `JobFunction`, `ParserType`.

**TaskResult[T]** - Generic result container with `ok()` / `fail()` factory methods. Used by pipeline flows to distinguish "no results" from "failure".

**Metrics models**: `StageMetricsInput` and `CompanySummaryInput` with `__post_init__` validation (non-negative counts, positive execution time).

## Config (`config/`)

- **DatabaseConfig** - Loads MongoDB settings from env vars with defaults
- **SupabaseConfig** - Loads Supabase URL/key from env, includes retry and circuit breaker settings with validation
- **IntegrationsConfig** - Contains `OpenAIConfig` and `WebExtractionConfig` (which contains `BrowserConfig`)
- **WebParserConfig** - Per-company parser configuration, requires both `job_board` and `job_card` selector groups

All config classes use `@dataclass` with `__post_init__` validation. Environment variables loaded via `python-dotenv`.

## Mappers (`mappers/`)

Convert OpenAI JSON responses to typed models. Pattern: `map_from_openai_response(response: dict) -> Model`

- **JobMapper** - Extracts jobs list, validates URLs (http/https), generates SHA256 signatures
- **JobDetailsMapper** - Extracts enum fields with per-field `_extract_*()` validators
- **JobRequirementsMapper** - Extracts string lists, strips whitespace, filters empties
- **JobTechnologiesMapper** - Extracts technology objects (name + required bool)

All mappers skip invalid items with warnings rather than failing the whole batch.
