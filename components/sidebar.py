"""Sidebar component."""

import streamlit as st

from services.auth import (
    get_current_user,
    is_authenticated,
    logout,
    render_login_button,
)
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

                st.caption(f"プロファイル生成: 残り {quota.profile_credits} 回")
                st.caption(f"求人検索: 残り {quota.search_credits} 回")
                st.divider()

                if st.button("ログアウト", use_container_width=True):
                    logout(cookie_manager)
                    st.rerun()
        else:
            st.info("GitHubでログインして始めましょう")
            render_login_button(redirect_uri)
