.PHONY: format-check import-check type-check lint check-all format format-fix install install-dev clean help

# Load environment variables from .env file if it exists
ifneq (,$(wildcard ./.env))
	include .env
	export
endif

# Python configuration
PYTHON ?= python
PIP ?= pip

# Default target
.DEFAULT_GOAL := help

# Code quality checks
format-check:
	@echo "Checking code formatting with Black..."
	@black --check --diff .
	@echo "✅ Black formatting check completed successfully"

import-check:
	@echo "Checking import sorting with isort..."
	@isort --check-only --diff .
	@echo "✅ Import sorting check completed successfully"

type-check:
	@echo "Running type checking with mypy..."
	@mypy . --ignore-missing-imports
	@echo "✅ Type checking completed successfully"

lint:
	@echo "Running linting with flake8..."
	@flake8 . --count --show-source --statistics
	@echo "✅ Linting completed successfully"

check-all: format-check import-check type-check lint
	@echo "✅ All code quality checks completed successfully!"

# Auto-formatting
format:
	@echo "Auto-formatting code with Black..."
	@black .
	@echo "✅ Black formatting applied successfully"

format-fix: format
	@echo "Auto-sorting imports with isort..."
	@isort .
	@echo "✅ Code formatting and import sorting completed successfully"

# Installation
install:
	@echo "Installing production dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "Installing Playwright browsers..."
	@playwright install
	@echo "✅ Production dependencies installed successfully"

install-dev:
	@echo "Installing development dependencies..."
	@$(PIP) install -r requirements-dev.txt
	@echo "Installing Playwright browsers..."
	@playwright install
	@echo "✅ Development dependencies installed successfully"

# Cleanup
clean:
	@echo "Cleaning up Python cache files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "✅ Cleanup completed successfully"

# Show help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Code Quality:"
	@echo "  format-check   - Check code formatting with Black"
	@echo "  import-check   - Check import sorting with isort"
	@echo "  type-check     - Run type checking with mypy"
	@echo "  lint           - Run linting with flake8"
	@echo "  check-all      - Run all code quality checks"
	@echo ""
	@echo "Code Formatting:"
	@echo "  format         - Auto-format code with Black"
	@echo "  format-fix     - Auto-format code and sort imports"
	@echo ""
	@echo "Environment Setup:"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo "  clean          - Clean up Python cache files"
	@echo ""
	@echo "Examples:"
	@echo "  make check-all     # Run all quality checks"
	@echo "  make format-fix    # Fix formatting and imports"
	@echo "  make install-dev   # Setup development environment"
	@echo ""
	@echo "Note: Configuration is read from .env file if present"