.PHONY: \
    format-check import-check type-check lint yaml-check check-all \
    format fix-imports fix-lint fix-all \
    install install-dev clean \
    pre-commit-install pre-commit-run pre-commit-update \
    up down restart purge logs logs-worker logs-server logs-db \
    rebuild rebuild-worker status shell-db shell-worker \
    backup restore clean-data verify-indexes \
    dashboard \
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

# ═══════════════════════════════════════════════════════════
# Code quality checks
# ═══════════════════════════════════════════════════════════

format-check:
	@echo "Checking code formatting with Ruff..."
	@ruff format --check --diff src tools
	@echo "✅ Ruff formatting check completed successfully"

import-check:
	@echo "Checking import sorting with Ruff..."
	@ruff check --select I --diff src tools
	@echo "✅ Import sorting check completed successfully"

type-check:
	@echo "Running type checking with mypy..."
	@mypy src tools
	@echo "✅ Type checking completed successfully"

lint:
	@echo "Running linting with Ruff..."
	@ruff check src tools --statistics
	@echo "✅ Linting completed successfully"

yaml-check:
	@echo "Checking YAML files with yamllint..."
	@yamllint pipeline.yaml companies.yaml .pre-commit-config.yaml
	@echo "✅ YAML linting completed successfully"

check-all: format-check import-check lint type-check
	@echo "✅ All code quality checks completed successfully!"

# ═══════════════════════════════════════════════════════════
# Auto-formatting and fixing
# ═══════════════════════════════════════════════════════════

format:
	@echo "Auto-formatting code with Ruff..."
	@ruff format src tools
	@echo "✅ Ruff formatting applied successfully"

fix-imports:
	@echo "Fixing import sorting with Ruff..."
	@ruff check --select I --fix src tools
	@echo "✅ Import sorting fixed successfully"

fix-lint:
	@echo "Auto-fixing linting issues with Ruff..."
	@ruff check --fix src tools
	@echo "✅ Linting issues fixed successfully"

fix-all: format fix-lint fix-imports
	@echo "✅ All formatting and linting fixes completed applied!"

# ═══════════════════════════════════════════════════════════
# Installation
# ═══════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════
# Cleanup
# ═══════════════════════════════════════════════════════════

clean:
	@echo "Cleaning up Python cache files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed successfully"

# ═══════════════════════════════════════════════════════════
# Pre-commit hooks
# ═══════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════
# Docker Compose Commands (Treat as Single Unit)
# ═══════════════════════════════════════════════════════════

up:
	@echo "🚀 Starting all services..."
	@docker-compose -f docker/docker-compose.yml up -d
	@echo ""
	@echo "✅ All services started successfully!"
	@echo ""
	@echo "📊 Prefect UI:  http://localhost:4200"
	@echo "🗄️  MongoDB:    localhost:27017"
	@echo ""
	@echo "💡 Useful commands:"
	@echo "   make logs        - View all logs"
	@echo "   make logs-worker - View worker logs"
	@echo "   make status      - Check service status"
	@echo "   make down        - Stop all services"

down:
	@echo "Stopping all services..."
	@docker-compose -f docker/docker-compose.yml down
	@echo "✅ All services stopped"

restart:
	@echo "Restarting all services..."
	@docker-compose -f docker/docker-compose.yml restart
	@echo "✅ All services restarted"

purge:
	@echo "⚠️  WARNING: This will remove ALL volumes (MongoDB + Prefect data)!"
	@echo "This action cannot be undone."
	@echo ""
	@read -p "Type 'DELETE' to confirm: " confirm; \
	if [ "$$confirm" = "DELETE" ]; then \
		echo "🗑️  Stopping services and removing all volumes..."; \
		docker-compose -f docker/docker-compose.yml down -v; \
		echo "✅ All volumes removed"; \
		echo "💡 Run 'make up' to start with fresh volumes"; \
	else \
		echo "❌ Operation cancelled"; \
	fi

# ═══════════════════════════════════════════════════════════
# Logs (View individual service logs)
# ═══════════════════════════════════════════════════════════

logs:
	@echo "📋 Showing all logs (Press Ctrl+C to exit)..."
	@docker-compose -f docker/docker-compose.yml logs -f

logs-worker:
	@echo "📋 Showing worker logs (Press Ctrl+C to exit)..."
	@docker-compose -f docker/docker-compose.yml logs -f prefect-worker

logs-server:
	@echo "📋 Showing Prefect server logs (Press Ctrl+C to exit)..."
	@docker-compose -f docker/docker-compose.yml logs -f prefect-server

logs-db:
	@echo "📋 Showing MongoDB logs (Press Ctrl+C to exit)..."
	@docker-compose -f docker/docker-compose.yml logs -f mongodb

# ═══════════════════════════════════════════════════════════
# Rebuild Commands
# ═══════════════════════════════════════════════════════════

rebuild:
	@echo "🔨 Rebuilding and restarting all services..."
	@docker-compose -f docker/docker-compose.yml up -d --build
	@echo "✅ All services rebuilt and restarted"
	@echo "💡 Run 'make logs' to view logs"

rebuild-worker:
	@echo "🔨 Rebuilding and restarting worker only..."
	@docker-compose -f docker/docker-compose.yml up -d --build --no-deps prefect-worker
	@echo "✅ Worker rebuilt and restarted"
	@echo "💡 Run 'make logs-worker' to view logs"

# ═══════════════════════════════════════════════════════════
# Status & Shell Access
# ═══════════════════════════════════════════════════════════

status:
	@echo "📊 Service Status:"
	@echo ""
	@docker-compose -f docker/docker-compose.yml ps
	@echo ""
	@echo "🏥 Health Checks:"
	@docker exec tw-mongodb mongosh -u admin -p admin --authenticationDatabase admin --eval "db.adminCommand('ping')" --quiet 2>/dev/null && echo "✅ MongoDB: Healthy" || echo "❌ MongoDB: Unhealthy"
	@curl -sf http://localhost:4200/api/health > /dev/null && echo "✅ Prefect Server: Healthy" || echo "❌ Prefect Server: Unhealthy"

shell-db:
	@echo "🐚 Connecting to MongoDB shell..."
	@docker exec -it tw-mongodb mongosh -u admin -p admin --authenticationDatabase admin

shell-worker:
	@echo "🐚 Connecting to worker container..."
	@docker exec -it tw-prefect-worker bash

# ═══════════════════════════════════════════════════════════
# Database Operations (MongoDB-specific)
# ═══════════════════════════════════════════════════════════

backup:
	@echo "💾 Creating MongoDB backup..."
	@mkdir -p ./backups
	@docker exec tw-mongodb mongodump \
		--username admin \
		--password admin \
		--authenticationDatabase admin \
		--db tw_scrapper \
		--out /tmp/backup
	@docker cp tw-mongodb:/tmp/backup/tw_scrapper ./backups/backup-$(shell date +%Y%m%d-%H%M%S)
	@echo "✅ Backup saved to ./backups/backup-$(shell date +%Y%m%d-%H%M%S)"

restore:
	@echo "📂 Available backups:"
	@ls -1 ./backups/ 2>/dev/null || echo "No backups found"
	@echo ""
	@read -p "Enter backup folder name: " backup; \
	if [ -d "./backups/$$backup" ]; then \
		docker cp ./backups/$$backup tw-mongodb:/tmp/restore && \
		docker exec tw-mongodb mongorestore \
			--username admin \
			--password admin \
			--authenticationDatabase admin \
			--db tw_scrapper \
			--drop \
			/tmp/restore && \
		echo "✅ MongoDB restore completed successfully"; \
	else \
		echo "❌ Backup folder not found"; \
		exit 1; \
	fi

verify-indexes:
	@echo "🔍 Verifying MongoDB indexes..."
	@docker exec tw-mongodb mongosh \
		-u admin \
		-p admin \
		--authenticationDatabase admin \
		--eval "db.getSiblingDB('tw_scrapper').job_listings.getIndexes()" \
		--quiet
	@echo "✅ Index verification completed"

clean-data:
	@echo "⚠️  WARNING: This will delete ALL MongoDB data!"
	@echo "This action cannot be undone."
	@echo ""
	@read -p "Type 'DELETE' to confirm: " confirm; \
	if [ "$$confirm" = "DELETE" ]; then \
		echo "🗑️  Dropping MongoDB database..."; \
		docker exec tw-mongodb mongosh \
			-u admin \
			-p admin \
			--authenticationDatabase admin \
			--eval "db.getSiblingDB('tw_scrapper').dropDatabase()" \
			--quiet; \
		echo "✅ MongoDB data deleted (Prefect data preserved)"; \
		echo "💡 Database will be recreated on next pipeline run"; \
	else \
		echo "❌ Operation cancelled"; \
	fi

# ═══════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════

dashboard:
	@echo "🚀 Starting Pipeline Health Dashboard..."
	@echo "📊 Dashboard will be available at http://localhost:8501"
	@echo "⏹️  Press Ctrl+C to stop the dashboard"
	@echo ""
	@PYTHONPATH=src streamlit run src/dashboard/app.py --server.port=8501 --server.address=localhost

# ═══════════════════════════════════════════════════════════
# Help
# ═══════════════════════════════════════════════════════════

help:
	@echo "╔══════════════════════════════════════════════════════════╗"
	@echo "║            Job Processing Pipeline - Makefile            ║"
	@echo "╚══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🐳 Docker Compose (Main Commands):"
	@echo "  make up              - Start all services (MongoDB + Prefect)"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make purge           - Remove all volumes (data loss!)"
	@echo "  make status          - Show service status & health"
	@echo "  make rebuild         - Rebuild and restart all services"
	@echo "  make rebuild-worker  - Rebuild worker only (faster)"
	@echo ""
	@echo "📋 Logs:"
	@echo "  make logs            - View all logs"
	@echo "  make logs-worker     - View worker logs only"
	@echo "  make logs-server     - View Prefect server logs"
	@echo "  make logs-db         - View MongoDB logs"
	@echo ""
	@echo "🐚 Shell Access:"
	@echo "  make shell-db        - MongoDB shell"
	@echo "  make shell-worker    - Worker container bash"
	@echo ""
	@echo "💾 Database Operations:"
	@echo "  make backup          - Backup MongoDB data"
	@echo "  make restore         - Restore MongoDB data"
	@echo "  make verify-indexes  - Verify MongoDB indexes"
	@echo "  make clean-data      - Delete all data (⚠️  destructive)"
	@echo ""
	@echo "📋 Code Quality:"
	@echo "  make check-all       - Run all quality checks"
	@echo "  make fix-all         - Apply all auto-fixes"
	@echo "  make format          - Auto-format code"
	@echo "  make lint            - Run linting"
	@echo "  make type-check      - Run type checking"
	@echo ""
	@echo "📦 Environment Setup:"
	@echo "  make install         - Install production dependencies"
	@echo "  make install-dev     - Install development dependencies"
	@echo "  make clean           - Clean cache files"
	@echo ""
	@echo "🪝 Pre-commit:"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run     - Run pre-commit checks"
	@echo ""
	@echo "📊 Dashboard:"
	@echo "  make dashboard       - Start Pipeline Health Dashboard"
	@echo ""
	@echo "💡 Quick Start:"
	@echo "  1. make up           - Start all services"
	@echo "  2. make logs-worker  - Watch pipeline execution"
	@echo "  3. make dashboard    - View metrics dashboard"
	@echo "  4. Open http://localhost:4200 to view Prefect UI"
	@echo ""
