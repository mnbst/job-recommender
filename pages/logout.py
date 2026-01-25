"""ログアウトページ."""

import streamlit as st

from services.auth import is_authenticated
from services.components.redirect import redirect


def render_logout_page() -> None:
    """ログアウトページを描画."""
    if is_authenticated():
        st.switch_page("pages/home.py")

    st.title("ログアウトしました")
    st.caption("またのご利用をお待ちしています。")
    redirect("https://job-recommender.com/")
    st.button("トップへ戻る", type="tertiary")


render_logout_page()
