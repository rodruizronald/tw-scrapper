from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from loguru import logger
from pymongo.errors import DuplicateKeyError, PyMongoError

from .database import db_controller as global_db_controller
from .models import JobListing

if TYPE_CHECKING:
    from pymongo.collection import Collection
    from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

    from .database import DatabaseController


"""
Repository layer for job listing CRUD operations.

This module provides the repository pattern implementation for JobListing
with comprehensive CRUD operations, querying, and business logic methods.
"""


class JobListingRepository:
    """
    Repository for JobListing CRUD operations following repository pattern.

    Provides high-level database operations with error handling, logging,
    and business logic encapsulation.
    """

    def __init__(self, db_controller: DatabaseController | None = None) -> None:
        """
        Initialize repository with database controller.

        Args:
            db_controller: Database controller instance (uses global if None)
        """
        self.db_controller = db_controller or global_db_controller
        self._collection: Collection | None = None
        # Get collection name from config
        self.collection_name = self.db_controller._config.job_listings_collection

    @property
    def collection(self) -> Collection:
        """Get MongoDB collection with lazy initialization."""
        if self._collection is None:
            # Use the simplified database method to get a proper Collection type
            db = self.db_controller.get_database()
            self._collection = db[self.collection_name]
        return self._collection

    def create(self, job_listing: JobListing) -> JobListing | None:
        """
        Create a new job listing in the database.

        Args:
            job_listing: JobListing instance to create

        Returns:
            JobListing: Created job listing with assigned _id, or None if failed

        Raises:
            ValueError: If job listing data is invalid
        """
        try:
            # Validate job listing
            job_listing.__post_init__()

            # Prepare document for insertion
            doc = job_listing.to_dict()

            # Remove _id if present (let MongoDB generate it)
            doc.pop("_id", None)

            # Insert document
            result: InsertOneResult = self.collection.insert_one(doc)

            if result.inserted_id:
                job_listing._id = result.inserted_id
                logger.info(f"Created job listing: {job_listing.signature}")
                return job_listing
            else:
                logger.error(f"Failed to create job listing: {job_listing.signature}")
                return None

        except DuplicateKeyError:
            logger.warning(f"Job listing already exists: {job_listing.signature}")
            return None
        except (PyMongoError, ValueError) as e:
            logger.error(f"Error creating job listing {job_listing.signature}: {e}")
            return None

    def get_by_signature(self, signature: str) -> JobListing | None:
        """
        Retrieve job listing by unique signature.

        Args:
            signature: Unique job signature

        Returns:
            JobListing: Found job listing or None
        """
        try:
            doc = self.collection.find_one({"signature": signature})
            if doc:
                return JobListing.from_dict(doc)
            return None
        except PyMongoError as e:
            logger.error(f"Error retrieving job listing by signature {signature}: {e}")
            return None

    def update(self, job_listing: JobListing) -> bool:
        """
        Update existing job listing in the database.

        Args:
            job_listing: JobListing instance to update

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            if not job_listing._id:
                logger.error("Cannot update job listing without _id")
                return False

            # Update timestamp
            job_listing.update_timestamp()

            # Prepare update document
            doc = job_listing.to_dict()
            doc.pop("_id", None)  # Remove _id from update document

            # Update document
            result: UpdateResult = self.collection.update_one(
                {"_id": job_listing._id}, {"$set": doc}
            )

            if result.modified_count > 0:
                logger.info(f"Updated job listing: {job_listing.signature}")
                return True
            else:
                logger.warning(
                    f"No changes made to job listing: {job_listing.signature}"
                )
                return False

        except PyMongoError as e:
            logger.error(f"Error updating job listing {job_listing.signature}: {e}")
            return False

    def delete_by_signature(self, signature: str) -> bool:
        """
        Delete job listing by signature.

        Args:
            signature: Unique job signature

        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            result: DeleteResult = self.collection.delete_one({"signature": signature})

            if result.deleted_count > 0:
                logger.info(f"Deleted job listing with signature: {signature}")
                return True
            else:
                logger.warning(f"No job listing found with signature: {signature}")
                return False

        except PyMongoError as e:
            logger.error(f"Error deleting job listing with signature {signature}: {e}")
            return False

    def find_by_company(self, company: str, limit: int = 100) -> list[JobListing]:
        """
        Find job listings by company name.

        Args:
            company: Company name
            limit: Maximum number of results

        Returns:
            list[JobListing]: List of matching job listings
        """
        try:
            cursor = self.collection.find({"company": company}).limit(limit)
            return [JobListing.from_dict(doc) for doc in cursor]
        except PyMongoError as e:
            logger.error(f"Error finding job listings by company {company}: {e}")
            return []

    def find_active_jobs(self, limit: int = 100) -> list[JobListing]:
        """
        Find active job listings.

        Args:
            limit: Maximum number of results

        Returns:
            list[JobListing]: List of active job listings
        """
        try:
            cursor = self.collection.find({"active": True}).limit(limit)
            return [JobListing.from_dict(doc) for doc in cursor]
        except PyMongoError as e:
            logger.error(f"Error finding active job listings: {e}")
            return []

    def find_inactive_jobs(self, limit: int = 100) -> list[JobListing]:
        """
        Find inactive job listings.

        Args:
            limit: Maximum number of results

        Returns:
            list[JobListing]: List of inactive job listings
        """
        try:
            cursor = self.collection.find({"active": False}).limit(limit)
            return [JobListing.from_dict(doc) for doc in cursor]
        except PyMongoError as e:
            logger.error(f"Error finding inactive job listings: {e}")
            return []

    def find_by_filters(
        self,
        company: str | None = None,
        location: str | None = None,
        work_mode: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
        technologies: list[str] | None = None,
        active: bool | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[JobListing]:
        """
        Find job listings with multiple filters.

        Args:
            company: Company name filter
            location: Location filter
            work_mode: Work mode filter
            employment_type: Employment type filter
            experience_level: Experience level filter
            technologies: List of required technologies
            active: Active status filter
            limit: Maximum number of results
            skip: Number of results to skip (for pagination)

        Returns:
            list[JobListing]: List of matching job listings
        """
        try:
            query: dict[str, Any] = {}

            # Add filters
            if company:
                query["company"] = {"$regex": company, "$options": "i"}

            if location:
                query["location"] = location

            if work_mode:
                query["work_mode"] = work_mode

            if employment_type:
                query["employment_type"] = employment_type

            if experience_level:
                query["experience_level"] = experience_level

            if technologies:
                query["main_technologies"] = {"$in": technologies}

            if active is not None:
                query["active"] = active

            cursor = self.collection.find(query).skip(skip).limit(limit)
            return [JobListing.from_dict(doc) for doc in cursor]
        except PyMongoError as e:
            logger.error(f"Error finding job listings with filters: {e}")
            return []

    def count_all(self) -> int:
        """
        Count total number of job listings.

        Returns:
            int: Total count of job listings
        """
        try:
            return self.collection.count_documents({})
        except PyMongoError as e:
            logger.error(f"Error counting job listings: {e}")
            return 0

    def count_active(self) -> int:
        """
        Count active job listings.

        Returns:
            int: Count of active job listings
        """
        try:
            return self.collection.count_documents({"active": True})
        except PyMongoError as e:
            logger.error(f"Error counting active job listings: {e}")
            return 0

    def count_inactive(self) -> int:
        """
        Count inactive job listings.

        Returns:
            int: Count of inactive job listings
        """
        try:
            return self.collection.count_documents({"active": False})
        except PyMongoError as e:
            logger.error(f"Error counting inactive job listings: {e}")
            return 0

    def get_companies_stats(self) -> dict[str, int]:
        """
        Get job count statistics by company.

        Returns:
            dict[str, int]: Dictionary with company name as key and count as value
        """
        try:
            pipeline: list[dict[str, Any]] = [
                {"$group": {"_id": "$company", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]

            result = {}
            for doc in self.collection.aggregate(pipeline):
                result[doc["_id"]] = doc["count"]

            return result
        except PyMongoError as e:
            logger.error(f"Error getting company statistics: {e}")
            return {}

    def find_jobs_for_stage(self, stage: int, limit: int = 100) -> list[JobListing]:
        """
        Find jobs that need processing for a specific stage.

        Args:
            stage: Stage number (2, 3, or 4)
            limit: Maximum number of results

        Returns:
            list[JobListing]: List of jobs ready for the specified stage
        """
        try:
            query: dict[str, Any] = {"active": True}

            if stage == 2:
                query["stage_1_completed"] = True
                query["stage_2_completed"] = False
            elif stage == 3:
                query["stage_1_completed"] = True
                query["stage_2_completed"] = True
                query["stage_3_completed"] = False
            elif stage == 4:
                query["stage_1_completed"] = True
                query["stage_2_completed"] = True
                query["stage_3_completed"] = True
                query["stage_4_completed"] = False
            else:
                logger.warning(f"Invalid stage number: {stage}")
                return []

            cursor = self.collection.find(query).limit(limit)
            jobs = [JobListing.from_dict(doc) for doc in cursor]
            logger.info(f"Found {len(jobs)} jobs ready for stage {stage}")
            return jobs

        except PyMongoError as e:
            logger.error(f"Error finding jobs for stage {stage}: {e}")
            return []

    def find_jobs_by_company_for_stage(
        self, company: str, stage: int, limit: int = 100
    ) -> list[JobListing]:
        """
        Find jobs for a specific company that need processing for a specific stage.

        Args:
            company: Company name
            stage: Stage number (2, 3, or 4)
            limit: Maximum number of results

        Returns:
            list[JobListing]: List of jobs ready for the specified stage
        """
        try:
            query: dict[str, Any] = {"active": True, "company": company}

            if stage == 2:
                query["stage_1_completed"] = True
                query["stage_2_completed"] = False
            elif stage == 3:
                query["stage_1_completed"] = True
                query["stage_2_completed"] = True
                query["stage_3_completed"] = False
            elif stage == 4:
                query["stage_1_completed"] = True
                query["stage_2_completed"] = True
                query["stage_3_completed"] = True
                query["stage_4_completed"] = False
            else:
                logger.warning(f"Invalid stage number: {stage}")
                return []

            cursor = self.collection.find(query).limit(limit)
            jobs = [JobListing.from_dict(doc) for doc in cursor]
            logger.info(f"Found {len(jobs)} jobs for {company} ready for stage {stage}")
            return jobs

        except PyMongoError as e:
            logger.error(f"Error finding jobs for {company} at stage {stage}: {e}")
            return []

    def count_by_stage(self) -> dict[str, int]:
        """
        Count jobs by stage completion.

        Returns:
            dict[str, int]: Dictionary with stage completion statistics
        """
        try:
            return {
                "stage_1_only": self.collection.count_documents(
                    {
                        "stage_1_completed": True,
                        "stage_2_completed": False,
                    }
                ),
                "stage_2_completed": self.collection.count_documents(
                    {"stage_2_completed": True, "stage_3_completed": False}
                ),
                "stage_3_completed": self.collection.count_documents(
                    {"stage_3_completed": True, "stage_4_completed": False}
                ),
                "stage_4_completed": self.collection.count_documents(
                    {"stage_4_completed": True}
                ),
                "fully_processed": self.collection.count_documents(
                    {
                        "stage_2_completed": True,
                        "stage_3_completed": True,
                        "stage_4_completed": True,
                    }
                ),
            }
        except PyMongoError as e:
            logger.error(f"Error counting jobs by stage: {e}")
            return {}

    def cleanup_old_entries(self, days: int = 30) -> int:
        """
        Delete job listings older than specified days.

        Args:
            days: Number of days (job listings older than this will be deleted)

        Returns:
            int: Number of deleted job listings
        """
        try:
            cutoff_date = datetime.now(UTC).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).timestamp() - (days * 24 * 60 * 60)

            cutoff_datetime = datetime.fromtimestamp(cutoff_date, UTC)

            result: DeleteResult = self.collection.delete_many(
                {"created_at": {"$lt": cutoff_datetime}}
            )

            deleted_count = result.deleted_count
            logger.info(
                f"Cleaned up {deleted_count} old job listings (older than {days} days)"
            )
            return deleted_count

        except PyMongoError as e:
            logger.error(f"Error cleaning up old job listings: {e}")
            return 0


# Global repository instance
job_listing_repository = JobListingRepository()
