import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from prefect import get_run_logger

from pipeline.core.config import PathsConfig
from pipeline.core.models import (
    Job,
)
from pipeline.utils.exceptions import FileOperationError


class FileService:
    """Service for handling file operations in the pipeline."""

    def __init__(self, paths: PathsConfig):
        """
        Initialize file service.

        Args:
            paths_config: Base directory for all file operations
        """
        self.paths = paths
        self.logger = get_run_logger()

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
        company_dir = self.paths.output_dir / sanitized_name
        company_dir.mkdir(parents=True, exist_ok=True)
        return company_dir

    def save_stage_results(
        self,
        jobs: list[Job],
        company_name: str,
        stage_tag: str,
    ) -> None:
        """
        Save jobs to a JSON file in the company-specific directory.

        Args:
            jobs: List of Job objects to save
            company_name: Company name for directory creation
            stage_tag: Stage identifier

        Returns:
            Path to the saved file

        Raises:
            FileOperationError: If file cannot be saved
        """
        try:
            company_dir = self.get_company_output_dir(company_name)
            filename = self.paths.get_stage_output_filename(stage_tag)
            output_path = company_dir / filename

            # Convert Job objects to dictionaries using to_dict method
            jobs_list = [job.to_dict() for job in jobs]

            jobs_data = {
                "company": company_name,
                "jobs": jobs_list,
                "total_jobs": len(jobs),
                "saved_at": datetime.now(UTC).astimezone().isoformat(),
            }

            # Save to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(jobs_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(jobs)} jobs to {output_path}")

        except Exception as e:
            error_msg = f"Failed to save jobs: {e!s}"
            self.logger.error(f"{error_msg}")
            raise FileOperationError(
                "save", str(output_path), error_msg, company_name
            ) from e

    def load_stage_results(
        self,
        company_name: str,
        stage_tag: str,
    ) -> list[Job]:
        """
        Load stage results for a company and convert to Job objects.

        Args:
            company_name: Company name
            stage_tag: Stage identifier (e.g., "stage_1")

        Returns:
            List of Job objects

        Raises:
            FileNotFoundError: If stage results file not found
            Exception: For other file operation errors
        """
        logger = get_run_logger()

        company_dir = self.get_company_output_dir(company_name)
        filename = self.paths.get_stage_output_filename(stage_tag)
        stage_result_file = company_dir / filename

        logger.info(f"Loading jobs from: {stage_tag}")

        if not stage_result_file.exists():
            raise FileNotFoundError(
                f"{stage_tag} results file not found: {stage_result_file}"
            )

        try:
            with open(stage_result_file, encoding="utf-8") as f:
                data = json.load(f)

            # Extract jobs from the JSON structure
            jobs_data = data.get("jobs", [])

            # Convert to Job objects using from_dict method
            job_objects = [Job.from_dict(job_dict) for job_dict in jobs_data]

            logger.info(f"Loaded {len(job_objects)} jobs for company: {company_name}")
            return job_objects

        except Exception as e:
            error_msg = f"Failed to load {stage_tag} results: {e}"
            logger.error(error_msg)
            raise FileOperationError(
                "load", str(stage_result_file), error_msg, company_name
            ) from e

    def load_previous_day_signatures(self, company_name: str) -> set[str]:
        """
        Load job signatures for a company from previous day.

        Args:
            company_name: Company name

        Returns:
            Set of job signatures from previous day
        """
        try:
            current_date = datetime.now(UTC).astimezone()
            previous_date = current_date - timedelta(days=1)
            previous_timestamp = previous_date.strftime("%Y%m%d")

            # Build path to previous day's jobs file
            previous_day_base = self.paths.output_dir.parent / previous_timestamp
            sanitized_name = self.sanitize_company_name(company_name)
            previous_company_dir = previous_day_base / sanitized_name
            unfiltered_signatures = previous_company_dir / "unfiltered_signatures.json"

            if not unfiltered_signatures.exists():
                self.logger.info(
                    f"No signatures from previous day at {unfiltered_signatures}"
                )
                return set()

            with open(unfiltered_signatures, encoding="utf-8") as f:
                previous_data = json.load(f)

            signatures = set(previous_data.get("signatures", []))
            self.logger.info(f"Loaded {len(signatures)} signatures from previous day")
            return signatures

        except Exception as e:
            self.logger.warning(f"Error loading signatures from yesterday: {e}")
            return set()

    def save_signatures(
        self,
        signatures: set[str],
        company_name: str,
        filename: str,
    ) -> Path:
        """
        Save job signatures.

        Args:
            signatures: Set of job signatures
            company_name: Company name
            filename: Output filename

        Returns:
            Path to the saved file
        """
        try:
            company_dir = self.get_company_output_dir(company_name)
            output_path = company_dir / filename

            data = {
                "company": company_name,
                "signatures": list(signatures),
                "count": len(signatures),
                "timestamp": datetime.now(UTC).astimezone().isoformat(),
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(signatures)} signatures to {output_path}")
            return output_path

        except Exception as e:
            error_msg = f"Failed to save signatures: {e!s}"
            self.logger.error(f"{error_msg}")
            raise FileOperationError(
                "save", str(output_path), error_msg, company_name
            ) from e
