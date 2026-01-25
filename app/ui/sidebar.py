"""Sidebar component."""

import streamlit as st

from app.services.auth import get_current_user, is_authenticated, render_login_button
from app.services.logout import logout
from app.services.quota import get_quota_status
from app.ui.credits import render_remaining_credits_caption


def render_sidebar(cookie_manager, redirect_uri: str) -> None:
    """サイドバーを描画."""
    with st.sidebar:
        if is_authenticated():
            user = get_current_user()
            if user:
                st.markdown("### メニュー")
                st.page_link("pages/home.py", label="ホーム", icon="🏠")
                st.page_link("pages/plans.py", label="プラン・利用制限", icon="📋")
                st.page_link(
                    "pages/privacy.py", label="プライバシーポリシー", icon="🔒"
                )
                st.page_link("pages/terms.py", label="利用規約", icon="📜")
                st.divider()

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
