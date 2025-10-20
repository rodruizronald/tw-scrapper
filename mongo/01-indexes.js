
db = db.getSiblingDB('tw_scrapper');

// ============================================
// JOB LISTINGS INDEXES
// ============================================

// Core indexes
db.job_listings.createIndex({ "signature": 1 }, { unique: true });
db.job_listings.createIndex({ "created_at": -1 });  // Recent jobs first
db.job_listings.createIndex({ "active": 1 });

// Compound indexes for common filter combinations
db.job_listings.createIndex({ "company": 1, "active": 1 });
db.job_listings.createIndex({ "company": 1, "created_at": -1 });
db.job_listings.createIndex({ "location": 1, "active": 1 });
db.job_listings.createIndex({ "active": 1, "created_at": -1 });

// Individual field indexes for filtering
db.job_listings.createIndex({ "work_mode": 1 });
db.job_listings.createIndex({ "employment_type": 1 });
db.job_listings.createIndex({ "experience_level": 1 });

// Technology searches
db.job_listings.createIndex({ "main_technologies": 1 });

// URL lookups
db.job_listings.createIndex({ "url": 1 });

print("Optimized indexes created for job_listings collection");

// ============================================
// JOB METRICS DAILY INDEXES
// ============================================

// Core indexes - date is the primary query dimension
db.job_metrics_daily.createIndex({ "date": -1 });  // Recent metrics first
db.job_metrics_daily.createIndex({ "company": 1, "date": -1 });  // Company trends over time
db.job_metrics_daily.createIndex({ "date": -1, "company": 1 });  // Date range queries with company filter

// Unique constraint to prevent duplicate metrics for same company/date
db.job_metrics_daily.createIndex({ "company": 1, "date": 1 }, { unique: true });

print("Optimized indexes created for job_metrics_daily collection");

// ============================================
// JOB METRICS AGGREGATES INDEXES
// ============================================

// Core index - date is the unique key and primary query dimension
db.job_metrics_aggregates.createIndex({ "date": 1 }, { unique: true });  // Unique daily aggregates

// Date range queries (for find_aggregates_by_date_range method)
db.job_metrics_aggregates.createIndex({ "date": -1 });  // Recent aggregates first

print("Optimized indexes created for job_metrics_aggregates collection");
