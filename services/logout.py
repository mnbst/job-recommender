"""Logout service."""

from __future__ import annotations

import logging
import os

import httpx
import streamlit as st

from services.cache import delete_all_user_data
from services.logging_config import log_structured
from services.session import (
    delete_firestore_session,
    delete_session_cookie,
    get_session_cookie,
)
from services.session_keys import (
    ACCESS_TOKEN,
    LOGOUT_REQUESTED,
    SESSION_ID,
    USER,
)

logger = logging.getLogger(__name__)


def _get_oauth_config() -> tuple[str, str]:
    """環境変数からOAuthクレデンシャルを取得."""
    client_id = os.environ.get("GITHUB_OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET", "")
    return client_id, client_secret


def revoke_github_token(access_token: str) -> None:
    """GitHubのOAuthトークンを取り消し.

    これにより、次回ログイン時にGitHubの認証画面が表示される。
    """
    client_id, client_secret = _get_oauth_config()
    if not client_id or not client_secret:
        return

    try:
        # OAuth App認可自体を取り消す（トークンだけでなく認可全体）
        httpx.request(
            "DELETE",
            f"https://api.github.com/applications/{client_id}/grant",
            auth=(client_id, client_secret),
            json={"access_token": access_token},
        )
    except Exception:
        # 取り消し失敗は無視（ローカルログアウトは続行）
        log_structured(
            logger,
            "Failed to revoke GitHub token",
            level=logging.ERROR,
            exc_info=True,
        )


def logout(cookie_manager=None) -> None:
    """ユーザーセッションをクリア.

    Args:
        cookie_manager: CookieManager（セッション削除用、Noneの場合はローカルのみクリア）
    """
    st.session_state[LOGOUT_REQUESTED] = True
    user = st.session_state.get(USER)
    user_id = user.id if user else None
    logger.info("Logout started: user_id=%s", user_id)

    # GitHubトークンの取り消し（別アカウントでのログインを可能にする）
    access_token = st.session_state.get(ACCESS_TOKEN)
    if access_token:
        revoke_github_token(access_token)
        logger.info("GitHub token revoked: user_id=%s", user_id)

    # 永続化セッションの削除
    session_id = st.session_state.get(SESSION_ID)
    if cookie_manager is not None and not session_id:
        session_id = get_session_cookie(cookie_manager)

    if session_id and cookie_manager is not None:
        delete_firestore_session(session_id)
        delete_session_cookie(cookie_manager)
        logger.info("Session deleted: user_id=%s, session_id=%s", user_id, session_id)

    # Firestoreからユーザーデータを削除（creditsは維持）
    if user:
        delete_all_user_data(str(user.id))
        logger.info(
            "User data deleted from Firestore: user_id=%s (profiles, repos, settings)",
            user_id,
        )
