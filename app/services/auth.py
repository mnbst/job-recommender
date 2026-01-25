"""GitHub OAuth 認証サービス."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx
import streamlit as st

from app.services.const import GITHUB_AUTHORIZE_URL, GITHUB_TOKEN_URL, GITHUB_USER_URL
from app.services.models import GitHubUser
from app.services.session import (
    delete_session_cookie,
    delete_user_sessions,
    generate_session_id,
    get_firestore_session,
    get_session_cookie,
    restore_session_from_dict,
    save_firestore_session,
    set_session_cookie,
    update_session_last_accessed,
)
from app.services.session_keys import ACCESS_TOKEN, SESSION_ID, USER

if TYPE_CHECKING:
    from app.services.streamlit_components.cookie_manager import CookieManager

logger = logging.getLogger(__name__)


def get_oauth_config() -> tuple[str, str]:
    """環境変数からOAuthクレデンシャルを取得."""
    client_id = os.environ.get("GITHUB_OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET", "")
    return client_id, client_secret


def should_auto_redirect_to_auth() -> bool:
    """ローカル/Greenのみ自動リダイレクトを許可する。"""
    k_service = os.environ.get("K_SERVICE", "")
    return (not k_service) or k_service.endswith("-green")


def get_authorization_url(redirect_uri: str) -> str:
    """GitHub OAuth認可URLを生成."""
    client_id, _ = get_oauth_config()

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
    }
    return f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> str | None:
    """認可コードをアクセストークンに交換."""
    client_id, client_secret = get_oauth_config()

    response = httpx.post(
        GITHUB_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
        },
        headers={"Accept": "application/json"},
    )

    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None


def get_github_user(access_token: str) -> GitHubUser | None:
    """アクセストークンでGitHubユーザー情報を取得."""
    response = httpx.get(
        GITHUB_USER_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    if response.status_code == 200:
        data = response.json()
        return GitHubUser(
            id=data["id"],
            login=data["login"],
            name=data.get("name"),
            email=data.get("email"),
            avatar_url=data["avatar_url"],
        )
    return None


def handle_oauth_callback(cookie_manager: CookieManager | None = None) -> bool:
    """OAuthコールバックを処理してユーザーを認証.

    Args:
        cookie_manager: CookieManager（セッション永続化用、Noneの場合は永続化しない）

    Returns:
        認証成功時はTrue、それ以外はFalse
    """
    # 既に認証済みの場合はスキップ
    if is_authenticated():
        return True

    query_params = st.query_params

    # OAuthコールバックかチェック
    code = query_params.get("code")

    if not code:
        return False

    # コードをトークンに交換
    access_token = exchange_code_for_token(code)
    if not access_token:
        st.error("GitHubの認証に失敗しました。")
        # クエリパラメータをクリアして再試行可能に
        st.query_params.clear()
        return False

    # ユーザー情報を取得
    user = get_github_user(access_token)
    if not user:
        st.error("ユーザー情報の取得に失敗しました。")
        st.query_params.clear()
        return False

    # セッション永続化
    session_id: str | None = None
    if cookie_manager is not None:
        # 既存セッションを削除（1ユーザー1セッションを保証）
        delete_user_sessions(user.id)

        session_id = generate_session_id()
        save_firestore_session(session_id, user, access_token)
        set_session_cookie(cookie_manager, session_id)

    _set_authenticated_session(user, access_token, session_id)

    # クエリパラメータをクリア
    st.query_params.clear()

    return True


def get_current_user() -> GitHubUser | None:
    """現在認証されているユーザーを取得."""
    return st.session_state.get(USER)


def is_authenticated() -> bool:
    """ユーザーが認証されているかチェック."""
    return get_current_user() is not None


def _set_authenticated_session(
    user: GitHubUser,
    access_token: str,
    session_id: str | None = None,
) -> None:
    """認証済みセッションをsession_stateにセット."""
    st.session_state[USER] = user
    st.session_state[ACCESS_TOKEN] = access_token
    if session_id:
        st.session_state[SESSION_ID] = session_id
    else:
        st.session_state.pop(SESSION_ID, None)


def render_login_button(redirect_uri: str) -> None:
    """GitHubログインボタンを表示."""
    client_id, _ = get_oauth_config()

    if not client_id:
        st.warning("GitHub OAuthが設定されていません。")
        return

    auth_url = get_authorization_url(redirect_uri)
    st.link_button("GitHubでログイン", auth_url, use_container_width=True)


def restore_session(cookie_manager: CookieManager) -> bool:
    """Cookieからセッションを復元.

    起動時に呼び出し、Cookieに有効なセッションがあれば復元する。

    Args:
        cookie_manager: CookieManager

    Returns:
        復元成功時はTrue、それ以外はFalse
    """
    # 既に認証済みならスキップ
    if is_authenticated():
        return True

    # Cookieからsession_idを取得
    session_id = get_session_cookie()
    if not session_id:
        return False

    # Firestoreからセッションを取得
    session_data = get_firestore_session(session_id)
    if not session_data:
        # セッションが無効 → Cookie削除
        delete_session_cookie(cookie_manager)
        return False

    # セッション復元
    user, access_token = restore_session_from_dict(session_data)
    _set_authenticated_session(user, access_token, session_id)

    # last_accessed_at を更新
    update_session_last_accessed(session_id)

    return True


def ensure_authenticated(
    redirect_uri: str,
    cookie_manager: CookieManager | None = None,
) -> None:
    """未認証なら処理を停止する（ローカル/Greenのみ自動リダイレクト）。"""
    if cookie_manager is not None:
        restore_session(cookie_manager)

    handle_oauth_callback(cookie_manager)

    if not is_authenticated():
        if should_auto_redirect_to_auth():
            auth_url = get_authorization_url(redirect_uri)
            st.html(f'<meta http-equiv="refresh" content="0; url={auth_url}">')
        st.stop()
