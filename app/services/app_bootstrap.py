"""Streamlitアプリの共通初期化処理。"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from app.services.auth import get_current_user, handle_oauth_callback, restore_session
from app.services.headers_utils import get_header
from app.services.logging_config import is_cloud_run, setup_logging
from app.services.session import delete_session_cookie
from app.services.session_keys import LOGOUT_REQUESTED

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def setup_app() -> None:
    """ログ設定・環境変数読込・ページ設定をまとめて行う。"""
    setup_logging()
    if not is_cloud_run():
        load_dotenv(PROJECT_ROOT / ".env.local")

    st.set_page_config(
        page_title="Job Recommender",
        page_icon="💼",
        layout="wide",
    )


def get_redirect_uri() -> str:
    """リクエストのホストに基づいてredirect_uriを決定する。"""
    host_header = get_header("Host")
    if host_header and host_header.startswith("localhost"):
        return f"http://{host_header}"
    return os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8501")


def initialize_session(cookie_manager) -> bool:
    """セッション復元やログアウト時の遷移処理を行う。"""
    logout_requested = st.session_state.pop(LOGOUT_REQUESTED, False)
    if logout_requested:
        user_id = get_current_user()
        user_id = user_id.id if user_id else None
        # Cookieを削除（次回アクセス時に認証を要求）
        delete_session_cookie(cookie_manager)
        st.session_state.clear()
        logger.info("Logout completed: user_id=%s", user_id)
        st.switch_page("pages/logout.py")
        st.stop()
        return True

    restore_session(cookie_manager)
    handle_oauth_callback(cookie_manager)
    return False
