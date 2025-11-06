#!/bin/bash

set -e

# Check if script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "⚠️  This script should be sourced, not executed directly"
    echo "Please run: source scripts/dev-setup.sh"
    exit 1
fi

echo "🔧 Setting up development environment..."
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]"

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

echo ""
echo "✅ Development environment ready!"
echo ""
echo "Virtual environment is now active in this shell"
echo "To deactivate: deactivate"
