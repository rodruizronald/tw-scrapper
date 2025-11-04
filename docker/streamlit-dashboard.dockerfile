
# Multi-stage build for Streamlit dashboard

# Stage 1: Base setup (system setup)
# Has: Python runtime and system dependencies
FROM python:3.12-slim AS base

# Set environment variables early
#
# Forces Python to run in unbuffered mode - prints output immediately to stdout/stderr
# Critical for Docker containers to see logs in real-time (no buffering delays)
ENV PYTHONUNBUFFERED=1 \
    # Prevents Python from writing .pyc bytecode files to disk
    # Reduces container size and avoids permission issues in read-only filesystems
    PYTHONDONTWRITEBYTECODE=1 \
    # Disables pip's cache directory to reduce Docker layer size
    # Each pip install won't store downloaded packages (saves ~100-500MB)
    PIP_NO_CACHE_DIR=1 \
    # Suppresses pip's version check warnings
    # Reduces noise in logs and speeds up pip operations slightly
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory and set it as working directory
WORKDIR /app

# Stage 2: Dependencies (Python packages)
# Has: Everything from base + dashboard pip packages (streamlit, plotly, pandas)
FROM base AS dependencies

# Copy only dependency files first (better layer caching)
COPY pyproject.toml ./
COPY src ./src

# Install only dashboard dependencies
RUN pip install ".[dashboard]"

# Stage 3: Runtime (final image)
# Has: Everything from dependencies + application code + non-root user
FROM dependencies AS runtime

# Create non-root user with specific UID/GID for consistency
# -r: system user (no home directory by default, but -m overrides this)
# -g 1001: group ID (matches worker for consistent file permissions across containers)
# -m: create home directory (/home/dashboard)
# -s /bin/bash: set shell (useful for debugging)
# 2>/dev/null || true: suppress errors if user/group already exists
RUN groupadd -r -g 1001 dashboard 2>/dev/null || true && \
    useradd -r -u 1001 -g dashboard -m -s /bin/bash dashboard 2>/dev/null || true

# Copy application code
# --chown=1001:1001: Sets owner to our dashboard user (UID 1001:GID 1001)
# This ensures the dashboard user can read all application files
COPY --chown=1001:1001 . /app

# Set PYTHONPATH to include src directory so Python can find your modules
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Ensure dashboard user owns all application files
RUN chown -R 1001:1001 /app

# Switch to non-root user (use UID instead of username for reliability)
USER 1001

# Start Streamlit dashboard
ENTRYPOINT ["/bin/bash", "/app/scripts/start-dashboard.sh"]
