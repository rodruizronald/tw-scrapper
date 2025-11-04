
#!/bin/bash
set -e

echo 'Starting Streamlit dashboard...'
echo 'Dashboard will be available at: http://localhost:8501'

# Start Streamlit with configuration
# MongoDB is already healthy thanks to depends_on condition
exec streamlit run src/dashboard/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
