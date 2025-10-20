
#!/bin/bash
set -e

echo '⏳ Waiting for Prefect server...'
sleep 10

echo '🏊 Creating work pool...'
prefect work-pool create job-scraper-pool --type process 2>/dev/null || \
  echo '✓ Pool already exists'

echo '📦 Deploying flows...'
prefect deploy --all --no-prompt

echo '🚀 Starting worker in background...'
prefect worker start --pool job-scraper-pool &
WORKER_PID=$!

echo '⏳ Waiting for worker to be ready...'
sleep 5

echo '▶️  Triggering initial deployment...'
prefect deployment run 'job_processing_pipeline/job-scraper-production'
echo '✅ Initial deployment triggered!'

echo '👀 Worker running. Pipeline will execute shortly...'
echo '📊 View progress at: http://localhost:4200'

# Keep container running
wait $WORKER_PID
