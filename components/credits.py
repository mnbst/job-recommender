"""Credit-related UI helpers."""

from __future__ import annotations

import streamlit as st


def render_remaining_credits_caption(
    credits: int,
    *,
    prefix: str = "残り",
    suffix: str = "クレジット",
) -> None:
    """Render a standard remaining-credits caption."""
    st.caption(f"{prefix} {credits} {suffix}")


def render_credit_button(
    label: str,
    *,
    credits: int,
    can_use: bool,
    caption: str | None = None,
    type: str | None = None,
    key: str | None = None,
    use_container_width: bool = True,
    layout: tuple[int, int] | None = (1, 3),
    warning_text: str = "クレジットがありません。",
    show_warning_when_disabled: bool = True,
) -> bool:
    """Render a button with credits caption and disabled handling."""
    if caption is None:
        caption = f"残り {credits} クレジット"

    button_kwargs = {
        "label": label,
        "disabled": not can_use,
        "key": key,
        "use_container_width": use_container_width,
    }
    if type is not None:
        button_kwargs["type"] = type

    if layout is not None:
        col_button, col_caption = st.columns(list(layout))
        with col_button:
            clicked = st.button(**button_kwargs)
        with col_caption:
            st.caption(caption)
    else:
        st.caption(caption)
        clicked = st.button(**button_kwargs)

    if show_warning_when_disabled and not can_use:
        st.warning(warning_text)

    return clicked
