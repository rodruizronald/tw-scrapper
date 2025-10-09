
db = db.getSiblingDB('tw_scrapper');

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

print("Optimized indexes created for JobListingRepository patterns");
