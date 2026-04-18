"""Pydantic models for structured agent extraction output."""

from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    """Structured output model for the browser-use agent."""

    jobs: list[str] = Field(description="List of all job posting URLs found")
