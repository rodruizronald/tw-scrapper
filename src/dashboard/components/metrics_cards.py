"""
Reusable metric card components.
"""

from typing import Literal

import streamlit as st


def render_metric_card(
    label: str,
    value: str | int | float,
    delta: str | None = None,
    delta_color: Literal["normal", "inverse", "off"] = "normal",
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
            delta_color_value = metric.get("delta_color", "normal")
            # Ensure delta_color is one of the allowed values
            if delta_color_value not in ("normal", "inverse", "off"):
                delta_color_value = "normal"

            render_metric_card(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta"),
                delta_color=delta_color_value,  # type: ignore[arg-type]
                icon=metric.get("icon", "📊"),
            )


def render_status_badge(status: str) -> str:
    """
    Render a colored status badge.

    Args:
        status: Status string (e.g., 'completed', 'failed', 'pending')

    Returns:
        HTML string for colored badge
    """
    status_colors = {
        "completed": "#28a745",  # Green
        "failed": "#dc3545",  # Red
        "pending": "#ffc107",  # Yellow
        "running": "#17a2b8",  # Blue
        "skipped": "#6c757d",  # Gray
    }

    color = status_colors.get(status.lower(), "#6c757d")

    return f'<span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: 500;">{status.upper()}</span>'
