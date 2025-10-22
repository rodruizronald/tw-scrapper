"""
Repository for aggregate job metrics persistence.

Handles database operations for daily aggregate metrics without business logic.
"""

from typing import Any

from bson import ObjectId
from loguru import logger
from pymongo.errors import PyMongoError
from utils.timezone import now_local

from data.base import BaseRepository
from data.config import db_config
from data.database import DatabaseController

from .models import DailyAggregateMetrics


class JobAggregateMetricsRepository(BaseRepository[DailyAggregateMetrics]):
    """
    Repository for aggregate job metrics database operations.

    Handles pipeline-wide daily aggregated metrics storage and retrieval.
    """

    def __init__(
        self,
        db_controller: DatabaseController,
    ):
        """
        Initialize aggregate metrics repository.

        Args:
            db_controller: Database controller instance
            collection_name: Name of aggregates collection
        """
        super().__init__(db_controller, db_config.job_metrics_aggregates_collection)

    # Implement abstract methods from BaseRepository
    def _to_dict(self, model: DailyAggregateMetrics) -> dict[str, Any]:
        """Convert model to dictionary for storage."""
        return model.to_dict()

    def _from_dict(self, data: dict[str, Any]) -> DailyAggregateMetrics:
        """Convert dictionary to model."""
        return DailyAggregateMetrics.from_dict(data)

    def _get_unique_key(self, model: DailyAggregateMetrics) -> str:
        """Get unique identifier for logging."""
        return model.date

    def _get_id(self, model: DailyAggregateMetrics) -> ObjectId | None:
        """Get MongoDB _id from model."""
        return model._id

    def _set_id(self, model: DailyAggregateMetrics, object_id: ObjectId) -> None:
        """Set MongoDB _id on model."""
        model._id = object_id

    # Domain-specific methods
    def upsert_daily_aggregate(self, date: str, metrics: DailyAggregateMetrics) -> bool:
        """
        Insert or update daily aggregate metrics.

        Args:
            date: Date in YYYY-MM-DD format
            metrics: DailyAggregateMetrics object

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert to dict
            metrics_dict = metrics.to_dict()

            # Remove _id if present (MongoDB will handle it)
            metrics_dict.pop("_id", None)

            # Separate created_at from other fields
            created_at = metrics_dict.pop("created_at", now_local())

            # Update updated_at to current time
            metrics_dict["updated_at"] = now_local()

            # Use update_one with upsert=True
            result = self.collection.update_one(
                {"date": date, "document_type": "daily_aggregate"},
                {
                    "$set": metrics_dict,  # Update these fields
                    "$setOnInsert": {"created_at": created_at},  # Only set on creation
                },
                upsert=True,
            )

            if result.upserted_id:
                logger.info(f"Created new daily aggregate for {date}")
            elif result.modified_count > 0:
                logger.info(f"Updated daily aggregate for {date}")
            else:
                logger.debug(f"No changes to daily aggregate for {date}")

            return True

        except PyMongoError as e:
            logger.error(f"Error upserting daily aggregate for {date}: {e}")
            return False

    def find_daily_aggregate(self, date: str) -> DailyAggregateMetrics | None:
        """
        Find daily aggregate metrics for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Daily aggregate metrics or None
        """
        try:
            doc = self.collection.find_one({"date": date})

            if doc:
                return DailyAggregateMetrics.from_dict(doc)

            return None

        except PyMongoError as e:
            logger.error(f"Error finding daily aggregate for {date}: {e}")
            return None

    def find_aggregates_by_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> list[DailyAggregateMetrics]:
        """
        Query aggregate metrics within date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of daily aggregate metrics
        """
        try:
            query: dict[str, Any] = {"date": {"$gte": start_date, "$lte": end_date}}

            cursor = self.collection.find(query).sort("date", -1)

            results = [DailyAggregateMetrics.from_dict(doc) for doc in cursor]

            logger.debug(
                f"Found {len(results)} aggregate metrics between {start_date} and {end_date}"
            )
            return results

        except PyMongoError as e:
            logger.error(f"Error querying aggregate metrics by date range: {e}")
            return []
