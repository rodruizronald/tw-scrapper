from typing import Any

from prefect.logging import get_run_logger

from pipeline.core.models import (
    EmploymentType,
    ExperienceLevel,
    JobDetails,
    Location,
    WorkMode,
)


class JobDetailsMapper:
    """Maps OpenAI response to JobDetails model."""

    def __init__(self):
        self.logger = get_run_logger()

    def map_from_openai_response(self, response: dict[str, Any]) -> JobDetails:
        """
        Transform OpenAI response to JobDetails model.

        Args:
            response: Raw OpenAI response dictionary

        Returns:
            JobDetails: Validated and typed job details

        Raises:
            ValueError: If response format is invalid or required fields are missing
        """
        try:
            # Extract job data from response
            job_data = response.get("job")
            if not job_data:
                raise ValueError("Missing 'job' key in OpenAI response")

            # Map and validate each field
            eligible = self._extract_eligible(job_data)
            location = self._extract_location(job_data)
            work_mode = self._extract_work_mode(job_data)
            employment_type = self._extract_employment_type(job_data)
            experience_level = self._extract_experience_level(job_data)
            description = self._extract_description(job_data)

            return JobDetails(
                eligible=eligible,
                location=location,
                work_mode=work_mode,
                employment_type=employment_type,
                experience_level=experience_level,
                description=description,
            )

        except Exception as e:
            self.logger.error(f"Failed to map OpenAI response to JobDetails: {e}")
            raise ValueError(f"Invalid OpenAI response format: {e}") from e

    def _extract_eligible(self, job_data: dict[str, Any]) -> bool:
        """Extract and validate eligible field."""
        eligible = job_data.get("eligible")
        if not isinstance(eligible, bool):
            raise ValueError(f"Invalid eligible value: {eligible}")
        return eligible

    def _extract_location(self, job_data: dict[str, Any]) -> Location:
        """Extract and validate location field."""
        location_str = job_data.get("location")
        if not location_str:
            raise ValueError("Missing location field")

        try:
            return Location(location_str)
        except ValueError as err:
            raise ValueError(f"Invalid location value: {location_str}") from err

    def _extract_work_mode(self, job_data: dict[str, Any]) -> WorkMode:
        """Extract and validate work_mode field."""
        work_mode_str = job_data.get("work_mode")
        if not work_mode_str:
            raise ValueError("Missing work_mode field")

        try:
            return WorkMode(work_mode_str)
        except ValueError as err:
            raise ValueError(f"Invalid work_mode value: {work_mode_str}") from err

    def _extract_employment_type(self, job_data: dict[str, Any]) -> EmploymentType:
        """Extract and validate employment_type field."""
        employment_type_str = job_data.get("employment_type")
        if not employment_type_str:
            raise ValueError("Missing employment_type field")

        try:
            return EmploymentType(employment_type_str)
        except ValueError as err:
            raise ValueError(
                f"Invalid employment_type value: {employment_type_str}"
            ) from err

    def _extract_experience_level(self, job_data: dict[str, Any]) -> ExperienceLevel:
        """Extract and validate experience_level field."""
        experience_level_str = job_data.get("experience_level")
        if not experience_level_str:
            raise ValueError("Missing experience_level field")

        try:
            return ExperienceLevel(experience_level_str)
        except ValueError as err:
            raise ValueError(
                f"Invalid experience_level value: {experience_level_str}"
            ) from err

    def _extract_description(self, job_data: dict[str, Any]) -> str:
        """Extract and validate description field."""
        description = job_data.get("description")
        if not isinstance(description, str) or not description:
            raise ValueError(f"Invalid description value: {description}")

        # Validate max length as per prompt requirements
        if len(description) > 500:
            self.logger.warning(
                f"Description exceeds 500 characters: {len(description)}"
            )

        return description.strip()
