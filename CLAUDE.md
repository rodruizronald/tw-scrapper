# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered job listing extraction and analysis pipeline. Scrapes company career pages with Playwright, processes content with OpenAI, stores results in MongoDB, and optionally syncs to Supabase. Orchestrated by Prefect with a Streamlit dashboard for monitoring.

## Common Commands

### Setup
```bash
make install              # Install all dev deps + Playwright browsers
make pre-commit-install   # Install git hooks (Ruff, Mypy, Yamllint)
```

### Code Quality
```bash
make check-all            # Run all checks: format, imports, lint, types
make fix-all              # Auto-fix all: format + lint + imports
make format               # Auto-format with Ruff
make lint                 # Lint with Ruff
make type-check           # Type check with Mypy
```

### Docker Services
```bash
make up                   # Start all (MongoDB, Prefect, Pipeline, Dashboard)
make down                 # Stop all
make logs-pipeline        # Follow pipeline logs
make status               # Health checks
make rebuild-pipeline     # Rebuild + restart pipeline container
```

### Running Locally
```bash
PYTHONPATH=src python -m pipeline.main    # Run pipeline (needs Prefect + MongoDB running)
make dashboard                            # Streamlit on localhost:8501
make prefect-server                       # Prefect UI on localhost:4200
```

### Database
```bash
make shell-db             # Open MongoDB shell
make backup               # Backup MongoDB to ./backups/
make restore              # Restore from backup
```

## Architecture

### Pipeline Stages (sequential)
1. **Stage 1** - Extract job URLs from career pages (Playwright + OpenAI)
2. **Stage 2** - Extract job details (description, location, salary)
3. **Stage 3** - Extract skills and responsibilities
4. **Stage 4** - Extract technologies (matched against `technologies.json` taxonomy)
5. **Stage 5** - Sync to Supabase (optional)
6. **Stage 6** - Record metrics and aggregates

### Layer Structure
```
Prefect Flows (orchestration, concurrency) -> Prefect Tasks (retry decisions)
  -> Stage Processors (business logic) -> Services (external integrations)
```

### Source Layout (`src/`)
- **`core/`** - Config loaders, data models (Pydantic/dataclass), mappers
- **`pipeline/`** - Prefect flows (`flows/`), tasks (`tasks/`), stage processors (`stages/`), config loaders (`config/`)
- **`services/`** - OpenAI, Playwright web extraction, MongoDB data, Supabase, metrics; HTML parsers in `parsers/`
- **`data/`** - Repository pattern: `mongo/` and `supabase/` each have `repositories/`, `models/`, and exceptions
- **`dashboard/`** - Streamlit app with `components/` and `pages/`
- **`utils/`** - Custom exception hierarchy, timezone utilities

### Key Config Files
- **`pipeline.yaml`** - Stage definitions, OpenAI model/prompt mappings
- **`companies.yaml`** - Company career URLs and web parser selectors (CSS/XPath, parser strategy)
- **`technologies.json`** - Technology taxonomy for matching
- **`.env`** - API keys, DB credentials, ports (copy from `.env.example`)

## Code Conventions

### Python Style
- Python 3.12+, Ruff for formatting (line-length 88, double quotes), Mypy for types
- First-party imports: `core`, `data`, `services`, `pipeline`, `utils` (configured in Ruff isort)
- `PYTHONPATH=src` for module resolution (set in Docker and Makefile)
- Source dirs for linting: `src/` and `tools/`

### Pre-commit Hooks
Ruff (format + check), Mypy, Yamllint, plus standard checks (trailing whitespace, large files, merge conflicts, debug statements).

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR to main: format-check, import-check, lint, yaml-check, type-check. No test suite exists.

Docker pipeline CI in `.github/workflows/docker-pipeline-dev.yml`. Docker Compose config in `docker/` with multi-stage Dockerfiles for pipeline (Playwright base image) and dashboard (Streamlit).

## Subdirectory Guides

Each `src/` subdirectory has its own `CLAUDE.md` with layer-specific patterns (auto-loaded when working in that directory):
- `src/pipeline/CLAUDE.md` - Flow/task/stage hierarchy, concurrency, exception handling by layer, retry config
- `src/services/CLAUDE.md` - Service inventory, retry strategies, parser system, exception rules
- `src/data/CLAUDE.md` - MongoDB vs Supabase patterns, repository base classes, circuit breaker, exception hierarchy
- `src/core/CLAUDE.md` - Model evolution through stages, config loading, mapper patterns
- `src/dashboard/CLAUDE.md` - Streamlit page structure, session state, data sources
