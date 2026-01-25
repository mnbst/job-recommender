"""ログアウトページ."""

import streamlit as st

from app.services.session import delete_session_cookie
from app.services.streamlit_components.cookie_manager import get_cookie_manager
from app.services.streamlit_components.redirect import redirect


def render_logout_page() -> None:
    """ログアウトページを描画."""
    # Cookie削除を確実に実行（ログアウト後の再アクセスで認証を要求）
    cookie_manager = get_cookie_manager(key="cookie_manager_logout")
    delete_session_cookie(cookie_manager)

    st.title("ログアウトしました")
    st.caption("またのご利用をお待ちしています。")
    if st.button("トップへ戻る", type="tertiary"):
        st.session_state["redirect_to_lp"] = True
    if st.session_state.get("redirect_to_lp"):
        redirect("https://job-recommender.com/")
        st.stop()


render_logout_page()
