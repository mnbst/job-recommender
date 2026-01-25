"""ログアウトページ."""

import streamlit as st

from services.auth import is_authenticated


def render_logout_page() -> None:
    """ログアウトページを描画."""
    if is_authenticated():
        st.switch_page("pages/home.py")
        st.stop()

    st.title("ログアウトしました")
    st.caption("またのご利用をお待ちしています。")
    st.link_button("トップへ戻る", "https://job-recommender.com/", width=200)


render_logout_page()
