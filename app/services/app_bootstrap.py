"""Streamlitアプリの共通初期化処理。"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from app.services.headers_utils import get_header
from app.services.logging_config import get_logger, is_cloud_run, setup_logging
from app.services.session import delete_session_cookie
from app.services.session_keys import (
    ACCESS_TOKEN,
    EMPLOYMENT_TYPE,
    JOB_LOCATION,
    JOB_PREFERENCES,
    JOB_RESULTS,
    JOB_TYPE,
    LOGOUT_REQUESTED,
    OTHER_PREFERENCES,
    PROFILE,
    PROFILE_STATE,
    QUOTA_STATUS,
    REGEN_REPO_METADATA_LIST,
    REGEN_SELECTED_REPOS,
    REPO_METADATA_LIST,
    SALARY_RANGE,
    SELECTED_REPOS,
    SESSION_ID,
    SETTINGS_LOADED,
    USER,
    USER_SETTINGS,
    WORK_STYLE,
)

logger = get_logger(__name__)
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
    """ログアウト時の遷移処理を行う。"""
    logout_requested = st.session_state.pop(LOGOUT_REQUESTED, False)
    if logout_requested:
        # Cookieを削除（次回アクセス時に認証を要求）
        delete_session_cookie(cookie_manager)
        # ログアウトページ表示フラグを設定（early stopをスキップするため）
        st.session_state["_show_logout_page"] = True
        # 認証・ユーザーデータのキーのみを削除（フラグは保持）
        _clear_user_session_keys()
        logger.info("User logged out")
        st.switch_page("pages/logout.py")
        st.stop()
        return True

    return False


def _clear_user_session_keys() -> None:
    """ログアウト時にユーザー関連のsession_stateキーをクリア（制御フラグは保持）."""
    keys_to_clear = [
        USER,
        ACCESS_TOKEN,
        SESSION_ID,
        PROFILE_STATE,
        REPO_METADATA_LIST,
        SELECTED_REPOS,
        REGEN_REPO_METADATA_LIST,
        REGEN_SELECTED_REPOS,
        SETTINGS_LOADED,
        JOB_LOCATION,
        SALARY_RANGE,
        WORK_STYLE,
        JOB_TYPE,
        EMPLOYMENT_TYPE,
        OTHER_PREFERENCES,
        QUOTA_STATUS,
        PROFILE,
        USER_SETTINGS,
        JOB_RESULTS,
        JOB_PREFERENCES,
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
