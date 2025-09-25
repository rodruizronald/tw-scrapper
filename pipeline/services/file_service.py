import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from prefect import get_run_logger

from pipeline.core.config import PathsConfig
from pipeline.core.models import JobData
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

    def save_jobs(
        self,
        jobs: list[JobData],
        company_name: str,
        stage_tag: str,
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
        try:
            company_dir = self.get_company_output_dir(company_name)
            filename = self.paths.get_stage_output_filename(stage_tag)
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

            self.logger.info(f"Saved {len(jobs)} jobs to {output_path}")
            return output_path

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
    ) -> list[JobData]:
        """
        Load stage results for a company and convert to JobData objects.

        Args:
            company_name: Company name
            stage_tag: Stage identifier (e.g., "stage_1")

        Returns:
            List of JobData objects

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

            # Convert to JobData objects
            job_objects = []
            for job_dict in jobs_data:
                job = JobData(
                    title=job_dict.get("title", ""),
                    url=job_dict.get("url", ""),
                    signature=job_dict.get("signature", ""),
                    company=job_dict.get("company", company_name),
                    timestamp=job_dict.get("timestamp", ""),
                )
                job_objects.append(job)

            logger.info(f"Loaded {len(job_objects)} jobs for company: {company_name}")
            return job_objects

        except Exception as e:
            error_msg = f"Failed to load {stage_tag} results: {e}"
            logger.error(error_msg)
            raise FileOperationError(
                "load", str(stage_result_file), error_msg, company_name
            ) from e

    def load_historical_signatures(self, company_name: str) -> set[str]:
        """
        Load historical job signatures for a company from previous day.

        Args:
            company_name: Company name

        Returns:
            Set of historical job signatures
        """
        try:
            current_date = datetime.now(UTC).astimezone()
            previous_date = current_date - timedelta(days=1)
            previous_timestamp = previous_date.strftime("%Y%m%d")

            # Build path to previous day's historical jobs file
            previous_day_base = self.paths.output_dir.parent.parent / previous_timestamp
            sanitized_name = self.sanitize_company_name(company_name)
            previous_company_dir = previous_day_base / sanitized_name
            historical_file = previous_company_dir / "historical_jobs.json"

            if not historical_file.exists():
                self.logger.info(f"No historical signatures found at {historical_file}")
                return set()

            with open(historical_file, encoding="utf-8") as f:
                historical_data = json.load(f)

            signatures = set(historical_data.get("signatures", []))
            self.logger.info(f"Loaded {len(signatures)} historical signatures")
            return signatures

        except Exception as e:
            self.logger.warning(f"Error loading historical signatures: {e}")
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
