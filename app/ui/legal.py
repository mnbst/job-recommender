"""Shared helpers for legal pages."""

from __future__ import annotations

import streamlit as st


def render_page_header(title: str, updated_at: str) -> None:
    """Render page title and updated date."""
    st.title(title)
    st.markdown(f"最終更新日: {updated_at}")
    st.divider()


def render_section(title: str) -> None:
    """Render a section header."""
    st.header(title)


def render_section_divider() -> None:
    """Render a section divider."""
    st.divider()
