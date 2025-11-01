"""
Main entry point for Pipeline Health Dashboard.

Multi-page Streamlit app with sidebar navigation and calendar-based date selection.
"""

import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Pipeline Health Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

# Main page content
st.title("📊 Pipeline Health Dashboard")
st.markdown("---")

st.info(
    "👈 **Select a date from the calendar in the sidebar to view metrics.**\n\n"
    "Navigate between pages using the sidebar menu."
)

# Display selected date if any
if st.session_state.selected_date:
    st.success(f"📅 Selected Date: **{st.session_state.selected_date}**")
    st.markdown("Navigate to a page from the sidebar to view detailed metrics.")
else:
    st.warning("⚠️ No date selected. Click on a date in the sidebar calendar.")

# Instructions
with st.expander("How to Use This Dashboard"):
    st.markdown("""
    ### Navigation
    1. **Select a Date**: Use the date picker in the sidebar to choose a date
    2. **View Pages**: Use the sidebar navigation to switch between:
       - **Overview**: Pipeline-wide metrics and stage performance
       - **Companies**: Individual company processing details
       - **Stage Analysis**: Deep dive into each stage's performance
       - **Issues & Alerts**: Failed and partial company runs

    ### Calendar & Heatmap
    - Use the **date picker** to select any date
    - View **month heatmap** by expanding the "View Month Heatmap" section
    - Color indicators show success rates:
      - 🟢 **Excellent** (≥95%): All jobs successful
      - 🔵 **Good** (75-94%): Most jobs successful
      - 🟡 **Fair** (50-74%): Half jobs successful
      - 🟠 **Poor** (25-49%): Many failures
      - 🔴 **Critical** (<25%): Most jobs failed
      - ⚪ **No Data**: No runs recorded

    ### Features
    - Click the **↻ Refresh** button to reload data
    - Expand the heatmap section to see monthly overview
    - Success rate and company count displayed for selected date
    """)

st.markdown("---")
st.caption("Pipeline Health Dashboard v1.0")
