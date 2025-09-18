.PHONY: \
    format-check import-check type-check lint yaml-check check-all \
    format fix-imports fix-lint fix-all \
    install install-dev clean \
    prefect-server prefect-config prefect-reset \
    pre-commit-install pre-commit-run pre-commit-update \
    help

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
	@echo "Checking code formatting with Ruff..."
	@ruff format --check --diff .
	@echo "✅ Ruff formatting check completed successfully"

import-check:
	@echo "Checking import sorting with Ruff..."
	@ruff check --select I --diff .
	@echo "✅ Import sorting check completed successfully"

type-check:
	@echo "Running type checking with mypy..."
	@mypy . --ignore-missing-imports
	@echo "✅ Type checking completed successfully"

lint:
	@echo "Running linting with Ruff..."
	@ruff check . --statistics
	@echo "✅ Linting completed successfully"

# YAML linting
yaml-check:
	@echo "Checking YAML files with yamllint..."
	@yamllint pipeline.yaml companies.yaml .pre-commit-config.yaml
	@echo "✅ YAML linting completed successfully"

check-all: format-check import-check lint type-check
	@echo "✅ All code quality checks completed successfully!"

# Auto-formatting and fixing
format:
	@echo "Auto-formatting code with Ruff..."
	@ruff format .
	@echo "✅ Ruff formatting applied successfully"

fix-imports:
	@echo "Fixing import sorting with Ruff..."
	@ruff check --select I --fix .
	@echo "✅ Import sorting fixed successfully"

fix-lint:
	@echo "Auto-fixing linting issues with Ruff..."
	@ruff check --fix .
	@echo "✅ Linting issues fixed successfully"

# Combined fix command (most commonly used)
fix-all: format fix-lint fix-imports
	@echo "✅ All formatting and linting fixes completed applied!"

# Installation
install:
	@echo "Installing production dependencies..."
	@$(PIP) install -e .
	@echo "Installing Playwright browsers..."
	@playwright install
	@echo "✅ Production dependencies installed successfully"

install-dev:
	@echo "Installing development dependencies..."
	@$(PIP) install -e ".[dev]"
	@echo "Installing Playwright browsers..."
	@playwright install
	@echo "✅ Development dependencies installed successfully"

# Cleanup
clean:
	@echo "Cleaning up Python cache files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed successfully"

# Prefect server management
prefect-server:
	@echo "Starting Prefect server..."
	@echo "🚀 Server will be available at http://127.0.0.1:4200"
	@echo "Press Ctrl+C to stop the server"
	@prefect server start

prefect-config:
	@echo "Configuring Prefect to use local server..."
	@prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
	@echo "✅ Prefect configured for local server"

prefect-reset:
	@echo "Resetting Prefect to default configuration..."
	@prefect config unset PREFECT_API_URL
	@echo "✅ Prefect reset to default configuration"

# Pre-commit hooks
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	@pre-commit install
	@echo "✅ Pre-commit hooks installed successfully"

pre-commit-run:
	@echo "Running pre-commit on all files..."
	@pre-commit run --all-files
	@echo "✅ Pre-commit checks completed successfully"

pre-commit-update:
	@echo "Updating pre-commit hooks..."
	@pre-commit autoupdate
	@echo "✅ Pre-commit hooks updated successfully"

# Show help
help:
	@echo "╔══════════════════════════════════════════════════════════╗"
	@echo "║                   Available Commands                     ║"
	@echo "╚══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📋 Code Quality Checks:"
	@echo "  make format-check       - Check code formatting with Ruff"
	@echo "  make import-check       - Check import sorting with Ruff"
	@echo "  make lint               - Run linting with Ruff"
	@echo "  make type-check         - Run type checking with mypy"
	@echo "  make yaml-check         - Check YAML files with yamllint"
	@echo "  make check-all          - Run ALL quality checks"
	@echo ""
	@echo "🔧 Code Formatting & Fixes:"
	@echo "  make format             - Auto-format code with Ruff"
	@echo "  make fix-imports        - Fix import sorting"
	@echo "  make fix-lint           - Fix linting issues"
	@echo "  make fix-all            - Apply ALL auto-fixes (recommended)"
	@echo ""
	@echo "📦 Environment Setup:"
	@echo "  make install            - Install production dependencies"
	@echo "  make install-dev        - Install development dependencies"
	@echo "  make clean              - Clean up cache files"
	@echo ""
	@echo "🔮 Prefect Management:"
	@echo "  make prefect-server     - Start Prefect server locally"
	@echo "  make prefect-config     - Configure Prefect to use local server"
	@echo "  make prefect-reset      - Reset Prefect to default configuration"
	@echo ""
	@echo "🪝 Pre-commit Hooks:"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run     - Run pre-commit on all files"
	@echo "  make pre-commit-update  - Update pre-commit hooks"
	@echo ""
