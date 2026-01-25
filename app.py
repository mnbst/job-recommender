"""Job Recommender - Streamlit Application."""

import logging
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from components import render_sidebar
from services.auth import (
    get_authorization_url,
    get_current_user,
    handle_oauth_callback,
    is_authenticated,
    restore_session,
)
from services.logging_config import is_cloud_run, log_structured, setup_logging
from services.session import get_cookie_manager
from services.session_keys import LOGOUT_REQUESTED

logger = logging.getLogger(__name__)

# ログ設定（Cloud Run環境では構造化ログを使用）
setup_logging()

# .env.local から環境変数を読み込み（ローカル環境のみ）
if not is_cloud_run():
    load_dotenv(Path(__file__).parent / ".env.local")

# Page config
st.set_page_config(
    page_title="Job Recommender",
    page_icon="💼",
    layout="wide",
)


# リダイレクトURI（localhost経由の場合は動的に設定）
def get_redirect_uri() -> str:
    """リクエストのホストに基づいてredirect_uriを決定."""
    # Streamlitのcontext からホスト情報を取得
    try:
        host_header = st.context.headers.get("Host", "")
        if host_header.startswith("localhost"):
            return f"http://{host_header}"
    except Exception:
        log_structured(
            logger,
            "Failed to read Host header from Streamlit context",
            level=logging.ERROR,
            exc_info=True,
        )
    # デフォルトは環境変数
    return os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8501")


REDIRECT_URI = get_redirect_uri()

# CookieManagerの取得（セッション永続化用）
cookie_manager = get_cookie_manager()

logout_requested = st.session_state.pop(LOGOUT_REQUESTED, False)
if logout_requested:
    st.session_state[LOGOUT_REQUESTED] = False
    user_id = get_current_user()
    user_id = user_id.id if user_id else None
    st.session_state.clear()
    logger.info("Logout completed: user_id=%s", user_id)
    # ランディングページへリダイレクト
    st.markdown(
        '<meta http-equiv="refresh" content="0; url=/">',
        unsafe_allow_html=True,
    )
    st.stop()
else:
    # セッション復元（Cookieから）
    restore_session(cookie_manager)

if not logout_requested:
    # OAuthコールバック処理
    handle_oauth_callback(cookie_manager)

# 未認証の場合の処理
if not is_authenticated():
    if is_cloud_run():
        # Cloud Run: 静的ページ経由でのみアクセスを許可
        st.stop()
    else:
        # ローカル: GitHub認証にリダイレクト
        auth_url = get_authorization_url(REDIRECT_URI)
        st.markdown(
            f'<meta http-equiv="refresh" content="0; url={auth_url}">',
            unsafe_allow_html=True,
        )
        st.stop()

# Sidebar
render_sidebar(cookie_manager, REDIRECT_URI)

# Navigation
pages = {
    "メイン": [
        st.Page("pages/home.py", title="ホーム", icon="🏠", default=True),
    ],
    "情報": [
        st.Page("pages/plans.py", title="プラン・利用制限", icon="📋"),
        st.Page("pages/privacy.py", title="プライバシーポリシー", icon="🔒"),
        st.Page("pages/terms.py", title="利用規約", icon="📜"),
    ],
}

pg = st.navigation(pages)
pg.run()
