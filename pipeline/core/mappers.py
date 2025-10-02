from typing import Any

from prefect.logging import get_run_logger

from pipeline.core.models import (
    EmploymentType,
    ExperienceLevel,
    JobDetails,
    JobSkills,
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
            # Map and validate each field
            eligible = self._extract_eligible(response)
            location = self._extract_location(response)
            work_mode = self._extract_work_mode(response)
            employment_type = self._extract_employment_type(response)
            experience_level = self._extract_experience_level(response)
            description = self._extract_description(response)

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


class JobSkillsMapper:
    """Maps OpenAI response to JobSkills model."""

    def __init__(self):
        self.logger = get_run_logger()

    def map_from_openai_response(self, response: dict[str, Any]) -> JobSkills:
        """
        Transform OpenAI response to JobSkills model.

        Args:
            response: Raw OpenAI response dictionary

        Returns:
            JobSkills: Validated and typed job skills

        Raises:
            ValueError: If response format is invalid or required fields are missing
        """
        try:
            # Map and validate each field
            responsibilities = self._extract_responsibilities(response)
            skill_must_have = self._extract_skill_must_have(response)
            skill_nice_to_have = self._extract_skill_nice_to_have(response)
            benefits = self._extract_benefits(response)

            return JobSkills(
                responsibilities=responsibilities,
                skill_must_have=skill_must_have,
                skill_nice_to_have=skill_nice_to_have,
                benefits=benefits,
            )

        except Exception as e:
            self.logger.error(f"Failed to map OpenAI response to JobSkills: {e}")
            raise ValueError(f"Invalid OpenAI response format: {e}") from e

    def _extract_responsibilities(self, job_data: dict[str, Any]) -> list[str]:
        """Extract and validate responsibilities field."""
        responsibilities = job_data.get("responsibilities")
        if not isinstance(responsibilities, list):
            raise ValueError(f"Invalid responsibilities value: {responsibilities}")

        # Validate each item is a string
        for i, item in enumerate(responsibilities):
            if not isinstance(item, str):
                raise ValueError(f"Invalid responsibility item at index {i}: {item}")

        return [item.strip() for item in responsibilities if item.strip()]

    def _extract_skill_must_have(self, job_data: dict[str, Any]) -> list[str]:
        """Extract and validate skill_must_have field."""
        skill_must_have = job_data.get("skill_must_have")
        if not isinstance(skill_must_have, list):
            raise ValueError(f"Invalid skill_must_have value: {skill_must_have}")

        # Validate each item is a string
        for i, item in enumerate(skill_must_have):
            if not isinstance(item, str):
                raise ValueError(f"Invalid must-have skill item at index {i}: {item}")

        return [item.strip() for item in skill_must_have if item.strip()]

    def _extract_skill_nice_to_have(self, job_data: dict[str, Any]) -> list[str]:
        """Extract and validate skill_nice_to_have field."""
        skill_nice_to_have = job_data.get("skill_nice_to_have")
        if not isinstance(skill_nice_to_have, list):
            raise ValueError(f"Invalid skill_nice_to_have value: {skill_nice_to_have}")

        # Validate each item is a string
        for i, item in enumerate(skill_nice_to_have):
            if not isinstance(item, str):
                raise ValueError(
                    f"Invalid nice-to-have skill item at index {i}: {item}"
                )

        return [item.strip() for item in skill_nice_to_have if item.strip()]

    def _extract_benefits(self, job_data: dict[str, Any]) -> list[str]:
        """Extract and validate benefits field."""
        benefits = job_data.get("benefits")
        if not isinstance(benefits, list):
            raise ValueError(f"Invalid benefits value: {benefits}")

        # Validate each item is a string
        for i, item in enumerate(benefits):
            if not isinstance(item, str):
                raise ValueError(f"Invalid benefit item at index {i}: {item}")

        return [item.strip() for item in benefits if item.strip()]
