
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

# Stage 2: Dependencies (Python packages)
# Has: Everything from base + your pip packages (playwright, openai, prefect, etc.)
FROM base AS dependencies

# Copy only dependency files first (better layer caching)
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install .

# Stage 3: Runtime (final image)
# Has: Everything from dependencies + your application code + non-root user
FROM dependencies AS runtime

# Create non-root user with specific UID/GID for consistency
# This script checks if the group/user already exists before creating
RUN groupadd -r -g 1001 pipeline 2>/dev/null || true && \
    useradd -r -u 1001 -g pipeline -m -s /bin/bash pipeline 2>/dev/null || true

# Copy application code
# --chown=1001:1001: Sets owner to our pipeline user (UID 1001:GID 1001)
COPY --chown=1001:1001 . /app

# Set PYTHONPATH to include src directory so Python can find your modules
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Ensure pipeline user has access to Playwright browsers
RUN chown -R 1001:1001 /ms-playwright 2>/dev/null || true && \
    chmod -R 755 /ms-playwright 2>/dev/null || true

# Ensure pipeline user owns all application files
RUN chown -R 1001:1001 /app

# Make startup script executable
RUN chmod +x /app/scripts/start-worker.sh

# Switch to non-root user (use UID instead of username for reliability)
USER 1001

# Use ENTRYPOINT with explicit bash interpreter instead of CMD
ENTRYPOINT ["/bin/bash", "/app/scripts/start-worker.sh"]
