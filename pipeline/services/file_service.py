import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from pipeline.core.models import JobData, ProcessingResult
from pipeline.utils.exceptions import FileOperationError


class FileService:
    """Service for handling file operations in the pipeline."""

    def __init__(self, base_output_dir: Path):
        """
        Initialize file service.

        Args:
            base_output_dir: Base directory for all file operations
        """
        self.base_output_dir = base_output_dir
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_company_name(self, company_name: str) -> str:
        """
        Sanitize company name for use as directory name.

        Args:
            company_name: Original company name

        Returns:
            Sanitized company name (lowercase, underscores for spaces, alphanumeric only)
        """
        # Convert to lowercase
        sanitized = company_name.lower()

        # Replace spaces with underscores
        sanitized = re.sub(r"\s+", "_", sanitized)

        # Keep only alphanumeric characters and underscores
        sanitized = re.sub(r"[^a-z0-9_]", "", sanitized)

        # Remove multiple consecutive underscores
        sanitized = re.sub(r"_+", "_", sanitized)

        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")

        # Ensure it's not empty
        if not sanitized:
            sanitized = "unknown_company"

        return sanitized

    def get_company_output_dir(self, company_name: str) -> Path:
        """
        Get the output directory for a specific company.

        Args:
            company_name: Company name

        Returns:
            Path to company-specific output directory
        """
        sanitized_name = self.sanitize_company_name(company_name)
        company_dir = self.base_output_dir / sanitized_name
        company_dir.mkdir(parents=True, exist_ok=True)
        return company_dir

    async def save_jobs(
        self,
        jobs: list[JobData],
        company_name: str,
        filename: str = "jobs_stage_1.json",
    ) -> Path:
        """
        Save jobs to a JSON file in the company-specific directory.

        Args:
            jobs: List of job data to save
            company_name: Company name for directory creation
            filename: Output filename

        Returns:
            Path to the saved file

        Raises:
            FileOperationError: If file cannot be saved
        """
        company_context = f"[{company_name}]"

        try:
            company_dir = self.get_company_output_dir(company_name)
            output_path = company_dir / filename

            # Convert jobs to dictionaries
            jobs_data = {
                "company": company_name,
                "jobs": [
                    {
                        "title": job.title,
                        "url": job.url,
                        "signature": job.signature,
                        "company": job.company,
                        "timestamp": job.timestamp,
                    }
                    for job in jobs
                ],
                "total_jobs": len(jobs),
                "saved_at": datetime.now(UTC).astimezone().isoformat(),
            }

            # Save to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(jobs_data, f, indent=2, ensure_ascii=False)

            logger.success(f"{company_context} Saved {len(jobs)} jobs to {output_path}")
            return output_path

        except Exception as e:
            error_msg = f"Failed to save jobs: {e!s}"
            logger.error(f"{company_context} {error_msg}")
            raise FileOperationError(
                "save", str(output_path), error_msg, company_name
            ) from e

    def load_historical_signatures(self, company_name: str) -> set[str]:
        """
        Load historical job signatures for a company from previous day.

        Args:
            company_name: Company name

        Returns:
            Set of historical job signatures
        """
        company_context = f"[{company_name}]"

        try:
            current_date = datetime.now(UTC).astimezone()
            previous_date = current_date - timedelta(days=1)
            previous_timestamp = previous_date.strftime("%Y%m%d")

            # Build path to previous day's historical jobs file
            previous_day_base = (
                self.base_output_dir.parent.parent
                / previous_timestamp
                / "pipeline_stage_4"
            )
            sanitized_name = self.sanitize_company_name(company_name)
            previous_company_dir = previous_day_base / sanitized_name
            historical_file = previous_company_dir / "historical_jobs.json"

            if not historical_file.exists():
                logger.info(
                    f"{company_context} No historical signatures found at {historical_file}"
                )
                return set()

            with open(historical_file, encoding="utf-8") as f:
                historical_data = json.load(f)

            signatures = set(historical_data.get("signatures", []))
            logger.info(
                f"{company_context} Loaded {len(signatures)} historical signatures"
            )
            return signatures

        except Exception as e:
            logger.warning(
                f"{company_context} Error loading historical signatures: {e}"
            )
            return set()

    async def save_historical_signatures(
        self,
        signatures: set[str],
        company_name: str,
        filename: str = "historical_jobs.json",
    ) -> Path:
        """
        Save job signatures for historical tracking.

        Args:
            signatures: Set of job signatures
            company_name: Company name
            filename: Output filename

        Returns:
            Path to the saved file
        """
        company_context = f"[{company_name}]"

        try:
            company_dir = self.get_company_output_dir(company_name)
            output_path = company_dir / filename

            historical_data = {
                "company": company_name,
                "signatures": list(signatures),
                "count": len(signatures),
                "timestamp": datetime.now(UTC).astimezone().isoformat(),
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(historical_data, f, indent=2, ensure_ascii=False)

            logger.info(
                f"{company_context} Saved {len(signatures)} signatures to {output_path}"
            )
            return output_path

        except Exception as e:
            error_msg = f"Failed to save historical signatures: {e!s}"
            logger.error(f"{company_context} {error_msg}")
            raise FileOperationError(
                "save", str(output_path), error_msg, company_name
            ) from e

    def load_company_jobs(
        self, company_name: str, filename: str = "jobs_stage_1.json"
    ) -> list[dict[str, Any]]:
        """
        Load jobs for a specific company.

        Args:
            company_name: Company name
            filename: Input filename

        Returns:
            List of job dictionaries
        """
        company_context = f"[{company_name}]"

        try:
            company_dir = self.get_company_output_dir(company_name)
            input_path = company_dir / filename

            if not input_path.exists():
                logger.warning(f"{company_context} Jobs file not found: {input_path}")
                return []

            with open(input_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)

            jobs: list[dict[str, Any]] = data.get("jobs", [])
            logger.info(f"{company_context} Loaded {len(jobs)} jobs from {input_path}")
            return jobs

        except Exception as e:
            logger.error(f"{company_context} Error loading jobs: {e}")
            return []

    def create_processing_summary(
        self,
        results: list[ProcessingResult],
        summary_filename: str = "processing_summary.json",
    ) -> Path:
        """
        Create a summary file of all processing results.

        Args:
            results: List of processing results
            summary_filename: Summary filename

        Returns:
            Path to the summary file
        """
        try:
            summary_path = self.base_output_dir / summary_filename

            summary_data = {
                "total_companies": len(results),
                "successful_companies": len([r for r in results if r.success]),
                "failed_companies": len([r for r in results if not r.success]),
                "total_jobs_found": sum(r.jobs_found for r in results),
                "total_jobs_saved": sum(r.jobs_saved for r in results),
                "processing_timestamp": datetime.now(UTC).astimezone().isoformat(),
                "results": [
                    {
                        "company_name": r.company_name,
                        "success": r.success,
                        "jobs_found": r.jobs_found,
                        "jobs_saved": r.jobs_saved,
                        "processing_time": r.processing_time,
                        "error": r.error,
                        "output_path": str(r.output_path) if r.output_path else None,
                    }
                    for r in results
                ],
            }

            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)

            logger.success(f"Created processing summary: {summary_path}")
            return summary_path

        except Exception as e:
            logger.error(f"Error creating processing summary: {e}")
            raise FileOperationError("save", str(summary_path), str(e)) from e
