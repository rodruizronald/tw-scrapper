# Development Tools

This directory contains utility tools for development, testing, and debugging.

## Available Tools

### selector_tester.py

A CSS selector testing utility for validating selectors on web pages with different parsing strategies.

#### Features

- Test CSS selectors on any webpage
- Support for multiple parser types (Default, Greenhouse, Angular)
- Multiple output formats (Console, JSON, Markdown)
- Save results to file
- Command-line interface
- Configuration file support

#### Usage

##### Basic Usage

```bash
# Test with default configuration
python -m tools.selector_tester

# Test specific URL with selectors
python -m tools.selector_tester --url "https://example.com" --selectors "h1" ".content"

# Use Angular parser
python -m tools.selector_tester --url "https://angular-app.com" --parser angular

# Save results to file
python -m tools.selector_tester --url "https://example.com" --selectors "h1" --save

# Output as JSON
python -m tools.selector_tester --url "https://example.com" --selectors "h1" --format json
```

##### Using Configuration File

Create a `test_config.json` file:

```json
{
  "url": "https://example.com/jobs",
  "selectors": [".job-title", ".job-description", "#apply-button"],
  "parser": "angular"
}
```

Then run:

```bash
python -m tools.selector_tester --config test_config.json
```

##### Direct Script Execution

```bash
cd tools
python selector_tester.py --url "https://example.com" --selectors "h1"
```

#### Exit Codes

- `0`: All selectors found successfully
- `1`: Some selectors found
- `2`: No selectors found
- `3`: Test execution failed

#### Output Formats

- **Console** (default): Colored, human-readable output
- **JSON**: Machine-readable JSON format
- **Markdown**: Documentation-friendly Markdown format

#### Saved Results

Results are saved in `tools/results/` with the naming convention:

- `{domain}_{timestamp}.json` for JSON format
- `{domain}_{timestamp}.md` for Markdown format

## Adding New Tools

When adding new tools to this directory:

1. Follow the existing naming convention (snake_case)
2. Include a docstring with usage examples
3. Support command-line arguments where appropriate
4. Update this README with documentation
5. Add appropriate error handling and logging

## Tool Development Guidelines

1. **Imports**: Use relative imports from parent directories
2. **Logging**: Use loguru for consistent logging
3. **CLI**: Use argparse for command-line interfaces
4. **Documentation**: Include comprehensive docstrings
5. **Testing**: Tools should be independently testable

## Examples

### Testing Job Board Selectors

```bash
# Test Greenhouse job board
python -m tools.selector_tester \
  --url "https://boards.greenhouse.io/company" \
  --selectors "#grnhse_iframe" ".job-post" \
  --parser greenhouse

# Test Angular job application
python -m tools.selector_tester \
  --url "https://careers.angular-company.com" \
  --selectors "app-job-list" "mat-card" \
  --parser angular \
  --save \
  --format markdown

# Test multiple selectors and save results
python -m tools.selector_tester \
  --url "https://company.com/careers" \
  --selectors ".position-title" ".location" ".department" ".apply-link" \
  --save
```

### Batch Testing

Create a shell script for batch testing:

```bash
#!/bin/bash
# test_all_companies.sh

urls=(
  "https://company1.com/jobs"
  "https://company2.com/careers"
  "https://company3.greenhouse.io"
)

for url in "${urls[@]}"; do
  python -m tools.selector_tester \
    --url "$url" \
    --selectors ".job-title" ".job-description" \
    --save \
    --format json
done
```

## Dependencies

The tools in this directory depend on:

- `parsers` module: For parsing strategies
- `services` module: For web extraction services
- `playwright`: For browser automation
- `loguru`: For logging

Ensure these dependencies are installed and the parent modules are accessible.
