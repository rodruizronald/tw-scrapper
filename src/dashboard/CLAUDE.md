# Dashboard

Streamlit multi-page app for pipeline monitoring. Entry point: `app.py`.

## Structure

- **`app.py`** - Page config, session state init, page routing
- **`components/sidebar.py`** - Calendar date picker with heatmap, date selection drives all pages via `st.session_state.selected_date`
- **`components/metrics_cards.py`** - Reusable metric card and status badge renderers
- **`pages/overview.py`** - Key metrics, company status breakdown, stage performance, data growth
- **`pages/companies.py`** - Company list with status filter and search, expandable stage-by-stage details
- **`pages/stage_analysis.py`** - Per-stage tabs with success rates, company details, failure analysis, execution time stats
- **`pages/issues_alerts.py`** - Error summary, failed/partial companies, recommendations

## Data Source

All pages fetch from `services.metrics_service.job_metrics_service`. Key methods: `get_pipeline_health_metrics()`, `get_companies_by_date()`, `get_heatmap_data()`, `get_most_recent_date()`.

## Running

```bash
make dashboard                    # localhost:8501
# or
PYTHONPATH=src streamlit run src/dashboard/app.py --server.port=8501
```

## Conventions

- Date state: `st.session_state.selected_date` (YYYY-MM-DD string)
- Heatmap legend: green >= 95%, blue 75-94%, yellow 50-74%, orange 25-49%, red < 25%
- Custom CSS injected in sidebar for dark mode fixes
