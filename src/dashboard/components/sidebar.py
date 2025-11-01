"""
Sidebar component with calendar heatmap and navigation.
"""

import calendar
from datetime import datetime

import streamlit as st

from services import job_metrics_service
from utils.timezone import today_local


def render_sidebar() -> None:
    """Render the sidebar with calendar, heatmap, and navigation."""
    with st.sidebar:
        st.title("📅 Calendar & Navigation")

        # Calendar with Heatmap
        _render_calendar_heatmap()

        st.markdown("---")

        # Navigation Menu
        _render_navigation_menu()

        st.markdown("---")

        # Quick Filters (Optional)
        _render_quick_filters()


def _render_calendar_heatmap() -> None:
    """Render calendar with heatmap visualization using st.date_input."""
    st.subheader("Select Date")

    # Initialize and get selected date
    _initialize_selected_date()
    current_date = _get_current_date()

    # Date input widget
    selected_date_obj = st.date_input(
        label="Pick a date",
        value=current_date,
        format="YYYY-MM-DD",
        help="Select a date to view job metrics",
        key="date_picker",
    )

    # Update session state when date changes
    _update_selected_date(selected_date_obj)

    # Refresh button
    if st.button("↻ Refresh", key="refresh_heatmap", help="Reload heatmap data"):
        st.rerun()

    # Get and display heatmap data
    heatmap_data = job_metrics_service.get_heatmap_data(
        selected_date_obj.year, selected_date_obj.month
    )
    heatmap_dict = {item["date"]: item for item in heatmap_data}

    # Display selected date info and heatmap
    _display_selected_date_info(heatmap_dict)
    _display_heatmap_legend(
        heatmap_data, selected_date_obj.month, selected_date_obj.year
    )


def _initialize_selected_date() -> None:
    """Initialize selected_date in session state if not exists."""
    if "selected_date" not in st.session_state:
        most_recent = job_metrics_service.get_most_recent_date()
        st.session_state.selected_date = (
            most_recent if most_recent else today_local().strftime("%Y-%m-%d")
        )


def _get_current_date():
    """Get current date from session state or fallback to today."""
    try:
        if st.session_state.selected_date:
            return datetime.strptime(st.session_state.selected_date, "%Y-%m-%d").date()  # noqa: DTZ007
        return today_local()
    except (ValueError, TypeError):
        return today_local()


def _update_selected_date(selected_date_obj) -> None:
    """Update session state when date changes."""
    if selected_date_obj:
        selected_date_str = selected_date_obj.strftime("%Y-%m-%d")
        if st.session_state.selected_date != selected_date_str:
            st.session_state.selected_date = selected_date_str
            st.rerun()


def _display_selected_date_info(heatmap_dict: dict) -> None:
    """Display information about the selected date."""
    if not st.session_state.selected_date:
        return

    if st.session_state.selected_date in heatmap_dict:
        data = heatmap_dict[st.session_state.selected_date]
        _display_date_status(data)
    else:
        st.info(f"Selected: {st.session_state.selected_date} (No data available)")


def _display_date_status(data: dict) -> None:
    """Display date status with color coding based on success rate."""
    success_rate = data["success_rate"]
    message = (
        f"✓ Selected: {st.session_state.selected_date} | "
        f"Success Rate: {success_rate:.1f}% | "
        f"Companies: {data['company_count']}"
    )

    if success_rate >= 95:
        st.success(message)
    elif success_rate >= 75:
        st.info(message)
    elif success_rate >= 50:
        st.warning(message)
    else:
        st.error(message)


def _display_heatmap_legend(
    heatmap_data: list, current_month: int, current_year: int
) -> None:
    """Display heatmap legend and month overview."""
    with st.expander("📊 View Month Heatmap", expanded=False):
        st.caption("Success Rate Legend:")
        st.markdown(
            """
            - 🟢 **Excellent** (≥95%): All jobs successful
            - 🔵 **Good** (75-94%): Most jobs successful
            - 🟡 **Fair** (50-74%): Half jobs successful
            - 🟠 **Poor** (25-49%): Many failures
            - 🔴 **Critical** (<25%): Most jobs failed
            - ⚪ **No Data**: No runs recorded
            """
        )

        if heatmap_data:
            st.caption(
                f"Month Overview: {calendar.month_name[current_month]} {current_year}"
            )
            _display_heatmap_items(heatmap_data)
        else:
            st.caption("No data available for this month")


def _display_heatmap_items(heatmap_data: list) -> None:
    """Display heatmap items with emoji indicators."""
    for item in sorted(heatmap_data, key=lambda x: x["date"])[:10]:
        rate = item["success_rate"]
        emoji = _get_success_emoji(rate)
        st.caption(
            f"{emoji} {item['date']}: {rate:.1f}% ({item['company_count']} companies)"
        )


def _get_success_emoji(success_rate: float) -> str:
    """Get emoji based on success rate."""
    if success_rate >= 95:
        return "🟢"
    if success_rate >= 75:
        return "🔵"
    if success_rate >= 50:
        return "🟡"
    if success_rate >= 25:
        return "🟠"
    return "🔴"


def _render_navigation_menu() -> None:
    """Render navigation menu."""
    st.subheader("📊 Pages")

    pages = {
        "overview": "📈 Overview",
        "companies": "🏢 Companies",
        "stage_analysis": "🔄 Stage Analysis",
        "issues_alerts": "⚠️ Issues & Alerts",
    }

    for page_key, page_label in pages.items():
        if st.button(page_label, key=f"nav_{page_key}", use_container_width=True):
            st.switch_page(f"pages/{page_key}.py")


def _render_quick_filters() -> None:
    """Render quick filter options."""
    st.subheader("🔍 Quick Filters")

    if st.checkbox("Show only failed runs", key="filter_failed"):
        st.session_state.filter_status = "failed"
    elif st.checkbox("Show only partial runs", key="filter_partial"):
        st.session_state.filter_status = "partial"
    else:
        st.session_state.filter_status = None

    if st.button("Clear Filters", key="clear_filters"):
        st.session_state.filter_status = None
        st.rerun()
