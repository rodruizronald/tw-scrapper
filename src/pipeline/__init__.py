"""
Job Pipeline Package

A modular pipeline for extracting and processing job listings from company career pages.
Combines web scraping with AI-powered content analysis for intelligent job data extraction.

Key Features:
- Automated job listing extraction from career pages
- AI-powered job parsing using OpenAI
- Duplicate detection and historical tracking
- Concurrent processing with rate limiting
- Comprehensive error handling and logging
- Modular architecture for easy extension
- MongoDB data layer for storage

"""

# Version information
__version__ = "1.0.0"
__author__ = "Job Pipeline Team"
__description__ = "AI-powered job listing extraction pipeline with MongoDB integration"

# Public API
__all__ = [
    "__author__",
    "__description__",
    "__version__",
]
