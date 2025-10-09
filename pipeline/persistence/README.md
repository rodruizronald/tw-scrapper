# Persistence Layer

This module provides a comprehensive persistence layer for storing job listings in MongoDB, following clean architecture principles and repository pattern.

## Architecture

The persistence layer consists of four main components:

### 1. Database Controller (`database.py`)

- **Purpose**: Manages MongoDB connections and database-level operations
- **Features**:
  - Singleton pattern for connection management
  - Synchronous MongoDB client support
  - Connection pooling and error handling
  - Index management
  - Database statistics and health checks

### 2. Models (`models.py`)

- **Purpose**: Database models optimized for MongoDB storage
- **Key Model**: `JobListing` - The main database model for job data
- **Features**:
  - Optimized for querying and indexing
  - Includes metadata for tracking processing stages
  - Built-in validation and timestamp management
  - Support for incremental data enrichment

### 3. Repository (`repositories.py`)

- **Purpose**: CRUD operations and business logic for job listings
- **Features**:
  - Complete CRUD operations
  - Advanced querying and filtering
  - Bulk operations and statistics
  - Error handling and logging
  - Pagination support

### 4. Mappers (`mappers.py`)

- **Purpose**: Convert between domain models (`Job`) and database models (`JobListing`)
- **Features**:
  - Bidirectional mapping
  - Progressive data enrichment support
  - Data merging capabilities
  - Type-safe conversions

## Models Comparison

| Field          | `Job` (Domain Model)                        | `JobListing` (Database Model)                          |
| -------------- | ------------------------------------------- | ------------------------------------------------------ |
| Core Data      | `title`, `url`, `signature`, `company`      | Same                                                   |
| Details        | `JobDetails` with enums                     | `JobListingDetails` with strings                       |
| Requirements   | `JobRequirements`                           | `JobListingRequirements`                               |
| Technologies   | `JobTechnologies` with `Technology` objects | `JobListingTechnologies` with `TechnologyInfo` objects |
| Metadata       | None                                        | `_id`, `created_at`, `updated_at`, processing flags    |
| Stage Tracking | Properties based on data presence           | Explicit boolean flags                                 |

## Usage Examples

### Basic Setup

```python
from pipeline.persistence import (
    db_controller,
    job_listing_repository,
    JobMapper,
    JobListing
)
from pipeline.core.models import Job

# Test database connection
if db_controller.test_connection():
    print("Database connected successfully")

# Create indexes for optimal performance
db_controller.create_indexes()
```

### Creating and Storing Jobs

```python
# Convert domain model to database model
job = Job(
    title="Senior Python Developer",
    url="https://example.com/jobs/1",
    signature="unique_job_signature",
    company="Tech Corp"
)

job_listing = JobMapper.to_job_listing(job)

# Save to database
created = job_listing_repository.create(job_listing)
if created:
    print(f"Job created with ID: {created._id}")
```

### Progressive Data Enrichment

```python
# Stage 1: Basic job data
job_listing = JobListing(
    title="Data Scientist",
    url="https://example.com/jobs/2",
    signature="data_scientist_123",
    company="AI Corp"
)

# Save Stage 1
created = job_listing_repository.create(job_listing)

# Stage 2: Add details (after processing)
job_listing.details = JobListingDetails(
    location="Costa Rica",
    work_mode="Remote",
    employment_type="Full-time",
    # ... other details
)
job_listing.stage_2_completed = True

# Update with Stage 2 data
job_listing_repository.update(job_listing)
```

### Querying and Filtering

```python
# Find by company
tech_jobs = job_listing_repository.find_by_company("Tech Corp")

# Find by multiple filters
filtered_jobs = job_listing_repository.find_by_filters(
    location="Costa Rica",
    work_mode="Remote",
    technologies=["Python", "Django"],
    limit=50
)

# Find incomplete jobs (for processing)
incomplete_jobs = job_listing_repository.find_incomplete()

# Get statistics
stats = {
    "total": job_listing_repository.count_all(),
    "by_stage": job_listing_repository.count_by_stage(),
    "by_company": job_listing_repository.get_companies_stats()
}
```

### Converting Back to Domain Model

```python
# Retrieve from database
job_listing = job_listing_repository.get_by_signature("unique_signature")

# Convert to domain model for processing
if job_listing:
    job = JobMapper.to_job(job_listing)
    # Now use job in your pipeline stages
```

## Configuration

Set up your environment variables (see `.env.template`):

```bash
# MongoDB connection
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=tw_scrapper
MONGO_USERNAME=your_username
MONGO_PASSWORD=your_password

# Or use connection string
MONGO_CONNECTION_STRING=mongodb://username:password@host:port/database

# Repository settings
REPO_DEFAULT_QUERY_LIMIT=100
REPO_MAX_QUERY_LIMIT=1000
REPO_CLEANUP_DAYS=30
```

## Database Schema

### Collection: `job_listings`

```json
{
  "_id": ObjectId,
  "signature": String,  // Unique index
  "active": Boolean,
  "title": String,
  "url": String,
  "company": String,
  "location": String,
  "work_mode": String,
  "employment_type": String,
  "experience_level": String,
  "job_function": String,
  "province": String,
  "city": String,
  "description": String,
  "responsibilities": [String],
  "skill_must_have": [String],
  "skill_nice_to_have": [String],
  "benefits": [String],
  "technologies": [{
    "name": String,
    "category": String,
    "required": Boolean
  }],
  "main_technologies": [String],
  "created_at": Date,
  "updated_at": Date
}
```

### Indexes

The system automatically creates the following indexes for optimal performance:

- `signature` (unique) - For deduplication
- `company` - For company-based queries
- `url` - For URL-based lookups
- `created_at`, `updated_at` - For temporal queries
- `details.location`, `details.work_mode`, etc. - For filtering
- `technologies.main_technologies` - For technology-based search

## Error Handling

The persistence layer includes comprehensive error handling:

- **Connection errors**: Automatic retry and logging
- **Duplicate entries**: Handled gracefully with warnings
- **Validation errors**: Clear error messages for invalid data
- **Query errors**: Logged with context for debugging

## Performance Considerations

- **Indexes**: Automatically created for common query patterns
- **Connection pooling**: Built-in MongoDB connection pooling
- **Batch operations**: Supported for bulk data processing
- **Pagination**: Implemented for large result sets
- **Async support**: Available for high-throughput scenarios

## Testing

Run the examples to test the persistence layer:

```python
from pipeline.persistence.examples import run_all_examples
run_all_examples()
```

This design allows for fault tolerance, progress tracking, and efficient data retrieval throughout the pipeline.
