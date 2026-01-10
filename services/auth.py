"""GitHub OAuth 認証サービス."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx
import streamlit as st
from pydantic import BaseModel

from services.const import GITHUB_AUTHORIZE_URL, GITHUB_TOKEN_URL, GITHUB_USER_URL
from services.session_keys import (
    ACCESS_TOKEN,
    EMPLOYMENT_TYPE,
    JOB_LOCATION,
    JOB_PREFERENCES,
    JOB_RESULTS,
    JOB_TYPE,
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

if TYPE_CHECKING:
    import extra_streamlit_components as stx


class GitHubUser(BaseModel):
    """GitHubユーザー情報."""

    id: int
    login: str
    name: str | None
    email: str | None
    avatar_url: str


def get_oauth_config() -> tuple[str, str]:
    """環境変数からOAuthクレデンシャルを取得."""
    client_id = os.environ.get("GITHUB_OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET", "")
    return client_id, client_secret


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


def handle_oauth_callback(cookie_manager: stx.CookieManager | None = None) -> bool:
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

    # セッションに保存
    st.session_state[USER] = user
    st.session_state[ACCESS_TOKEN] = access_token

    # セッション永続化
    if cookie_manager is not None:
        from services.session import (
            generate_session_id,
            save_firestore_session,
            set_session_cookie,
        )

        session_id = generate_session_id()
        save_firestore_session(session_id, user, access_token)
        set_session_cookie(cookie_manager, session_id)
        st.session_state[SESSION_ID] = session_id

    # クエリパラメータをクリア
    st.query_params.clear()

    return True


def get_current_user() -> GitHubUser | None:
    """現在認証されているユーザーを取得."""
    return st.session_state.get(USER)


def is_authenticated() -> bool:
    """ユーザーが認証されているかチェック."""
    return get_current_user() is not None


def revoke_github_token(access_token: str) -> None:
    """GitHubのOAuthトークンを取り消し.

    これにより、次回ログイン時にGitHubの認証画面が表示される。
    """
    client_id, client_secret = get_oauth_config()
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
        pass


def logout(cookie_manager: stx.CookieManager | None = None) -> None:
    """ユーザーセッションをクリア.

    Args:
        cookie_manager: CookieManager（セッション削除用、Noneの場合はローカルのみクリア）
    """
    # GitHubトークンの取り消し（別アカウントでのログインを可能にする）
    access_token = st.session_state.get(ACCESS_TOKEN)
    if access_token:
        revoke_github_token(access_token)

    # 永続化セッションの削除
    session_id = st.session_state.get(SESSION_ID)
    if cookie_manager is not None and not session_id:
        from services.session import get_session_cookie

        session_id = get_session_cookie(cookie_manager)

    if session_id and cookie_manager is not None:
        from services.session import delete_firestore_session, delete_session_cookie

        delete_firestore_session(session_id)
        delete_session_cookie(cookie_manager)

    # 認証情報 + ユーザー固有キャッシュ/状態をまとめてクリア
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
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)

    for key in (PROFILE, USER_SETTINGS, QUOTA_STATUS, JOB_RESULTS, JOB_PREFERENCES):
        st.session_state.pop(key, None)


def render_login_button(redirect_uri: str) -> None:
    """GitHubログインボタンを表示."""
    client_id, _ = get_oauth_config()

    if not client_id:
        st.warning("GitHub OAuthが設定されていません。")
        return

    auth_url = get_authorization_url(redirect_uri)
    st.link_button("GitHubでログイン", auth_url, use_container_width=True)


def render_user_info(cookie_manager: stx.CookieManager | None = None) -> None:
    """認証済みユーザー情報を表示.

    Args:
        cookie_manager: CookieManager（ログアウト時のセッション削除用）
    """
    user = get_current_user()
    if not user:
        return

    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(user.avatar_url, width=50)
    with col2:
        st.write(f"**{user.name or user.login}**")
        st.write(f"@{user.login}")

    if st.button("ログアウト", type="secondary"):
        logout(cookie_manager)
        st.rerun()


def restore_session(cookie_manager: stx.CookieManager) -> bool:
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

    from services.session import (
        delete_session_cookie,
        get_firestore_session,
        get_session_cookie,
        restore_session_from_dict,
        update_session_last_accessed,
    )

    # Cookieからsession_idを取得
    session_id = get_session_cookie(cookie_manager)
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
    st.session_state[USER] = user
    st.session_state[ACCESS_TOKEN] = access_token
    st.session_state[SESSION_ID] = session_id

    # last_accessed_at を更新
    update_session_last_accessed(session_id)

    return True
