"""GitHub OAuth 認証サービス."""

import os
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import streamlit as st

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@dataclass
class GitHubUser:
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


def handle_oauth_callback() -> bool:
    """OAuthコールバックを処理してユーザーを認証.

    認証成功時はTrue、それ以外はFalseを返す.
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
    st.session_state["user"] = user
    st.session_state["access_token"] = access_token

    # クエリパラメータをクリア
    st.query_params.clear()

    return True


def get_current_user() -> GitHubUser | None:
    """現在認証されているユーザーを取得."""
    return st.session_state.get("user")


def is_authenticated() -> bool:
    """ユーザーが認証されているかチェック."""
    return get_current_user() is not None


def logout() -> None:
    """ユーザーセッションをクリア."""
    st.session_state.pop("user", None)
    st.session_state.pop("access_token", None)


def render_login_button(redirect_uri: str) -> None:
    """GitHubログインボタンを表示."""
    client_id, _ = get_oauth_config()

    if not client_id:
        st.warning("GitHub OAuthが設定されていません。")
        return

    auth_url = get_authorization_url(redirect_uri)
    st.link_button("GitHubでログイン", auth_url, use_container_width=True)


def render_user_info() -> None:
    """認証済みユーザー情報を表示."""
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
        logout()
        st.rerun()
