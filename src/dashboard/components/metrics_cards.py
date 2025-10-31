"""
Reusable metric card components.
"""

import streamlit as st


def render_metric_card(
    label: str,
    value: str | int | float,
    delta: str | None = None,
    delta_color: str = "normal",
    icon: str = "📊",
) -> None:
    """
    Render a metric card.

    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        delta_color: Color of delta (normal, inverse, off)
        icon: Icon emoji
    """
    st.metric(
        label=f"{icon} {label}",
        value=value,
        delta=delta,
        delta_color=delta_color,
    )


def render_metric_cards_row(metrics: list[dict]) -> None:
    """
    Render a row of metric cards.

    Args:
        metrics: List of metric dicts with keys: label, value, delta, delta_color, icon
    """
    cols = st.columns(len(metrics))

    for i, metric in enumerate(metrics):
        with cols[i]:
            render_metric_card(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta"),
                delta_color=metric.get("delta_color", "normal"),
                icon=metric.get("icon", "📊"),
            )


def render_status_badge(status: str) -> str:
    """
    Get HTML for status badge.

    Args:
        status: Status string (success, partial, failed)

    Returns:
        HTML string for badge
    """
    colors = {
        "success": "#4caf50",
        "partial": "#ff9800",
        "failed": "#f44336",
    }

    icons = {
        "success": "✓",
        "partial": "⚠",
        "failed": "✗",
    }

    color = colors.get(status, "#9e9e9e")
    icon = icons.get(status, "?")

    return f"""
    <span style='background-color: {color}; color: white; padding: 4px 8px;
          border-radius: 4px; font-weight: bold;'>
        {icon} {status.upper()}
    </span>
    """
