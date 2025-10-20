# Multi-stage build for pipeline worker with Playwright

# Stage 1: Base setup (system setup)
# Has: Python, Playwright browsers, system dependencies
FROM mcr.microsoft.com/playwright/python:v1.51.0-noble AS base

# Set environment variables early
#
# Forces Python to run in unbuffered mode - prints output immediately to stdout/stderr
# Critical for Docker containers to see logs in real-time (no buffering delays)
ENV PYTHONUNBUFFERED=1 \
    # Prevents Python from writing .pyc bytecode files to disk
    # Reduces container size and avoids permission issues in read-only filesystems
    PYTHONDONTWRITEBYTECODE=1 \
    # Specifies where Playwright stores browser binaries
    # Uses the pre-installed location from the base image (mcr.microsoft.com/playwright)
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    # Disables pip's cache directory to reduce Docker layer size
    # Each pip install won't store downloaded packages (saves ~100-500MB)
    PIP_NO_CACHE_DIR=1 \
    # Suppresses pip's version check warnings
    # Reduces noise in logs and speeds up pip operations slightly
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Prevents Playwright from downloading browsers during pip install
    # Browsers are already included in the base image, so this avoids duplication
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Create app directory and set it as working directory
WORKDIR /app

# Install only Playwright's system dependencies
RUN apt-get update \
    && playwright install-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies (Python packages)
# Has: Everything from base + your pip packages (playwright, openai, prefect, etc.)
FROM base AS dependencies

# Copy only dependency files first (better layer caching)
COPY pyproject.toml ./
COPY README.md ./  # If referenced in pyproject.toml

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install . && \
    # Now playwright CLI is available - install system dependencies
    playwright install-deps chromium && \
    # Clean up apt cache
    rm -rf /var/lib/apt/lists/* && \
    # Verify Playwright installation
    python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Stage 3: Runtime (final image)
# Has: Everything from dependencies + your application code + non-root user
FROM dependencies AS runtime

# Create non-root user with specific UID/GID for consistency
# groupadd: Creates group 'pipeline' with GID 1000
# useradd: Creates user 'pipeline' with UID 1000, home dir, and bash shell
RUN groupadd -r -g 1000 pipeline && \
    useradd -r -u 1000 -g pipeline -m -s /bin/bash pipeline

# Copy application code
# --chown=pipeline:pipeline: Sets owner:group to pipeline:pipeline (UID 1000:GID 1000)
# . (source): Current directory on host (where Dockerfile is)
# /app (destination): Target directory in container
COPY --chown=pipeline:pipeline . /app

# Ensure pipeline user has access to Playwright browsers
RUN chown -R pipeline:pipeline /ms-playwright 2>/dev/null || true && \
    chmod -R 755 /ms-playwright 2>/dev/null || true

# Ensure pipeline user owns all application files
RUN chown -R pipeline:pipeline /app

# Make startup script executable
RUN chmod +x /app/scripts/start-worker.sh

# Switch to non-root user
USER pipeline

# Verify installations as non-root user
RUN python -c "import prefect; from playwright.sync_api import sync_playwright"

# Better health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD prefect version && python -c "from playwright.sync_api import sync_playwright" || exit 1
