"""
Database connection controller for MongoDB.

This module handles MongoDB connection management, configuration,
and provides a centralized database controller following best practices.
"""

from typing import Any, Optional

from loguru import logger
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from .config import get_database_config


class DatabaseController:
    """
    MongoDB database controller implementing singleton pattern.

    Provides synchronous database connections with proper connection
    pooling and error handling.
    """

    _instance: Optional["DatabaseController"] = None

    def __new__(cls) -> "DatabaseController":
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize database controller with configuration from DatabaseConfig."""
        if hasattr(self, "_initialized"):
            return

        # Initialize instance variables
        self._client: MongoClient[Any] | None = None
        self._config = get_database_config()

        self._initialized: bool = True
        logger.info(
            f"Database controller initialized for database: {self._config.database}"
        )

    def get_client(self) -> MongoClient[Any]:
        """
        Get MongoDB client.

        Returns:
            MongoClient: Configured MongoDB client

        Raises:
            ConnectionFailure: If unable to connect to MongoDB
        """
        if self._client is None:
            try:
                # Use connection string from config or build it
                connection_string = (
                    self._config.connection_string
                    if self._config.connection_string
                    else self._config.build_connection_string()
                )

                # Explicit type annotation for clarity
                client: MongoClient[Any] = MongoClient(
                    connection_string,
                    connectTimeoutMS=self._config.connection_timeout,
                    serverSelectionTimeoutMS=self._config.server_selection_timeout,
                )
                # Test connection
                client.admin.command("ping")
                self._client = client
                logger.info("Successfully connected to MongoDB")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise ConnectionFailure(f"Unable to connect to MongoDB: {e}") from e

        return self._client

    def get_database(self) -> Database[Any]:
        """
        Get database instance.

        Returns:
            Database: Database instance
        """
        client = self.get_client()
        return client[self._config.database]

    def get_collection(self, collection_name: str) -> Collection[Any]:
        """
        Get collection instance.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection: Collection instance
        """
        db = self.get_database()
        return db[collection_name]

    def close_connections(self) -> None:
        """Close all database connections."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            client = self.get_client()
            client.admin.command("ping")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def create_indexes(self) -> None:
        """Create database indexes for optimal performance."""
        try:
            db = self.get_database()
            job_listings = db[self._config.job_listings_collection]

            # Create indexes with proper method calls
            try:
                # Unique signature index for deduplication
                job_listings.create_index("signature", unique=True)
                logger.debug("Created unique index for signature")
            except Exception as e:
                logger.warning(f"Failed to create index for signature: {e}")

            # Regular indexes
            regular_indexes = [
                "company",
                "url",
                "active",
                "created_at",
                "updated_at",
                "location",
                "work_mode",
                "employment_type",
                "experience_level",
                "job_function",
                "main_technologies",
                "province",
            ]

            for field in regular_indexes:
                try:
                    job_listings.create_index(field)
                    logger.debug(f"Created index for {field}")
                except Exception as e:
                    logger.warning(f"Failed to create index for {field}: {e}")

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")

    def get_database_stats(self) -> dict[str, Any]:
        """
        Get database statistics.

        Returns:
            dict: Database statistics
        """
        try:
            db = self.get_database()
            stats = db.command("dbStats")

            # Get collection-specific stats
            collections_stats = {}
            for collection_name in db.list_collection_names():
                try:
                    coll_stats = db.command("collStats", collection_name)
                    collections_stats[collection_name] = {
                        "count": coll_stats.get("count", 0),
                        "size": coll_stats.get("size", 0),
                        "avgObjSize": coll_stats.get("avgObjSize", 0),
                    }
                except Exception as e:
                    logger.warning(
                        f"Failed to get stats for collection {collection_name}: {e}"
                    )

            return {
                "database": {
                    "collections": stats.get("collections", 0),
                    "dataSize": stats.get("dataSize", 0),
                    "storageSize": stats.get("storageSize", 0),
                    "indexes": stats.get("indexes", 0),
                    "indexSize": stats.get("indexSize", 0),
                },
                "collections": collections_stats,
            }
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {}


# Global database controller instance
db_controller = DatabaseController()
