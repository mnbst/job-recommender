"""Plan page UI helpers."""

from __future__ import annotations

import streamlit as st


def render_plan_card(
    title: str | None,
    metric_label: str,
    metric_value: str,
    *,
    caption: str | None = None,
    button_label: str | None = None,
    button_key: str | None = None,
    button_disabled: bool = True,
) -> None:
    """Render a simple plan/credit card."""
    with st.container(border=True):
        if title:
            st.subheader(title)
        st.metric(metric_label, metric_value)
        if caption:
            st.caption(caption)
        if button_label:
            st.button(
                button_label,
                key=button_key,
                disabled=button_disabled,
                use_container_width=True,
            )
