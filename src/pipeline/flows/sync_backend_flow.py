"""Flow to synchronize companies and technologies with the backend."""

import logging

from prefect import flow, get_run_logger, task

from core.models.jobs import CompanyData
from pipeline.config import PipelineConfig
from pipeline.flows.helpers import load_companies_from_file
from services.company_service import CompanyService


@task(
    name="sync_companies",
    description="Synchronize companies from YAML with backend",
    retries=2,
    retry_delay_seconds=10,
)
def sync_companies_task(companies_from_yaml: list[CompanyData]) -> dict[str, int]:
    """
    Synchronize companies with the backend.

    Compares companies from YAML file with existing companies in the backend
    and creates any missing ones.

    Args:
        companies_from_yaml: List of companies loaded from companies.yaml

    Returns:
        Dictionary with sync statistics:
        - total_yaml: Total companies in YAML
        - total_backend: Total companies in backend after sync
        - created: Number of companies created
        - already_exists: Number of companies that already existed
    """
    logger = get_run_logger()

    logger.info(
        f"Starting company sync with {len(companies_from_yaml)} companies from YAML"
    )

    stats = {
        "total_yaml": len(companies_from_yaml),
        "total_backend": 0,
        "created": 0,
        "already_exists": 0,
    }

    try:
        with CompanyService() as company_service:
            # Fetch all existing companies from backend
            logger.info("Fetching existing companies from backend...")
            existing_companies = company_service.get_all_companies()
            existing_company_names = {
                company.name.lower() for company in existing_companies
            }

            logger.info(
                f"Found {len(existing_companies)} existing companies in backend"
            )

            # Compare and create missing companies
            for company_data in companies_from_yaml:
                company_name_lower = company_data.name.lower()

                if company_name_lower in existing_company_names:
                    logger.debug(f"Company already exists: {company_data.name}")
                    stats["already_exists"] += 1
                else:
                    logger.info(f"Creating new company: {company_data.name}")
                    created_company = company_service.create_company(
                        name=company_data.name,
                        is_active=company_data.enabled,
                    )

                    if created_company:
                        logger.info(
                            f"✓ Successfully created company: {created_company.name} "
                            f"(ID: {created_company.id})"
                        )
                        stats["created"] += 1
                        existing_company_names.add(company_name_lower)
                    else:
                        # This shouldn't happen since we checked for existence,
                        # but handle gracefully in case of race conditions
                        logger.warning(
                            f"Company creation returned None for: {company_data.name}. "
                            "Likely a duplicate created by another process."
                        )
                        stats["already_exists"] += 1

            # Get final count of companies in backend
            final_companies = company_service.get_all_companies()
            stats["total_backend"] = len(final_companies)

            logger.info(
                f"Company sync completed - Created: {stats['created']}, "
                f"Already existed: {stats['already_exists']}, "
                f"Total in backend: {stats['total_backend']}"
            )

            return stats

    except Exception as e:
        logger.error(f"Error during company sync: {e}")
        raise


@flow(
    name="sync_backend",
    description="Synchronize companies and technologies with the backend",
    version="1.0.0",
    retries=0,
    timeout_seconds=300,  # 5 minute timeout
)
async def sync_backend_flow():
    """
    Synchronize backend data before running the main pipeline.

    This flow ensures that all companies and technologies from the configuration
    files exist in the backend database before processing jobs.

    Steps:
    1. Load companies from companies.yaml
    2. Fetch existing companies from backend
    3. Create missing companies
    4. (Future) Sync job technologies

    Returns:
        Dictionary with sync statistics for companies and technologies
    """
    logger = get_run_logger()
    logger.info("Starting backend synchronization flow")

    try:
        # Load configuration
        config = PipelineConfig.load()
        logger.info("Configuration loaded")

        # Configure service loggers
        logger.info("Configuring service loggers...")
        logging.getLogger("services.company_service").setLevel(logging.INFO)

        # Load companies from YAML file
        logger.info(f"Loading companies from: {config.companies_file_path}")
        companies = load_companies_from_file(config.companies_file_path, logger)
        logger.info(f"Loaded {len(companies)} companies from YAML")

        # Sync companies with backend
        logger.info("Syncing companies with backend...")
        company_stats = sync_companies_task(companies)

        # Prepare results
        results = {
            "companies": company_stats,
            # "technologies": {}  # To be implemented later
        }

        logger.info("Backend synchronization completed successfully")
        logger.info(f"Summary: {results}")

    except Exception as e:
        logger.error(f"Backend synchronization failed: {e}")
        raise
