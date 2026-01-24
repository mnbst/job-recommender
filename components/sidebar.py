"""Sidebar component."""

import streamlit as st

from components.credits import render_remaining_credits_caption
from services.auth import get_current_user, is_authenticated, render_login_button
from services.logout import logout
from services.quota import get_quota_status


def render_sidebar(cookie_manager, redirect_uri: str) -> None:
    """サイドバーを描画."""
    with st.sidebar:
        if is_authenticated():
            user = get_current_user()
            if user:
                quota = get_quota_status(user.id)

                st.write(f"**{user.login}**")
                st.divider()

                render_remaining_credits_caption(quota.credits)
                st.divider()

                st.button(
                    "ログアウト",
                    use_container_width=True,
                    on_click=logout,
                    args=(cookie_manager,),
                )
        else:
            st.info("GitHubでログインして始めましょう")
            render_login_button(redirect_uri)
