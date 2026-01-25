"""ログアウトページ."""

import streamlit as st

from app.services.logging_config import get_logger
from app.services.streamlit_components.redirect import redirect

logger = get_logger(__name__)


def render_logout_page() -> None:
    """ログアウトページを描画."""
    # rerunカウンターで無限ループを検出
    rerun_count = st.session_state.get("_logout_page_rerun_count", 0)
    st.session_state["_logout_page_rerun_count"] = rerun_count + 1

    # 2回目以降のrerunでフラグをクリア（Cookie削除によるrerunの後）
    if rerun_count >= 1:
        st.session_state.pop("_show_logout_page", None)

    st.title("ログアウトしました")
    st.caption("またのご利用をお待ちしています。")
    if st.button("トップへ戻る", type="tertiary"):
        # ログアウトページから離れる際にフラグをクリア
        st.session_state.pop("_show_logout_page", None)
        st.session_state.pop("_logout_page_rerun_count", None)
        st.session_state["redirect_to_lp"] = True

    if st.session_state.get("redirect_to_lp"):
        redirect("https://job-recommender.com/", delete_cookie=True)
        st.stop()


render_logout_page()
