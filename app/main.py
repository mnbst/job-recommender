"""Job Recommender - Streamlitのルーティング用エントリーポイント。"""

from __future__ import annotations

import logging
from typing import Any

import streamlit as st

from app.services.app_bootstrap import get_redirect_uri, initialize_session, setup_app
from app.services.auth import (
    get_authorization_url,
    is_authenticated,
    render_login_button,
    should_auto_redirect_to_auth,
)
from app.services.session import has_session_cookie_in_headers
from app.services.streamlit_components.cookie_manager import get_cookie_manager
from app.ui import render_sidebar

logger = logging.getLogger(__name__)


def _build_pages() -> tuple[Any, dict[str, list[Any]]]:
    """画面一覧（ナビゲーション構成）を組み立てる。"""
    logout_page = st.Page("pages/logout.py", title="ログアウト", icon="🚪")
    pages = {
        "メイン": [
            st.Page("pages/home.py", title="ホーム", icon="🏠", default=True),
        ],
        "情報": [
            st.Page("pages/plans.py", title="プラン・利用制限", icon="📋"),
            st.Page("pages/privacy.py", title="プライバシーポリシー", icon="🔒"),
            st.Page("pages/terms.py", title="利用規約", icon="📜"),
        ],
        "その他": [logout_page],
    }
    return logout_page, pages


def _is_logout_page(pg: Any, logout_page: Any) -> bool:
    """ログアウトページ判定（ページオブジェクトの差異に対応）。"""
    if pg == logout_page:
        return True
    page_name = (getattr(pg, "name", "") or "").lower()
    page_title = getattr(pg, "title", "")
    page_path = (getattr(pg, "url_path", "") or getattr(pg, "path", "") or "").lower()
    return (
        page_name == "logout"
        or page_title == "ログアウト"
        or page_path.strip("/") == "logout"
    )


def _is_oauth_callback() -> bool:
    """OAuthコールバック判定."""
    return bool(st.query_params.get("code"))


def run() -> None:
    """アプリ起動処理（設定・認証・ナビゲーション）。"""
    setup_app()

    # ===== Early Cookie Detection (Server-Side) =====
    # HTTPヘッダーから直接Cookieを読み取り、JS初期化を待たずに即座に判定
    has_cookie = has_session_cookie_in_headers()

    # Cookie無し & OAuthコールバックでもない → 早期終了
    if not has_cookie and not _is_oauth_callback():
        redirect_uri = get_redirect_uri()
        if should_auto_redirect_to_auth():
            auth_url = get_authorization_url(redirect_uri)
            st.markdown(
                f'<meta http-equiv="refresh" content="0; url={auth_url}">',
                unsafe_allow_html=True,
            )
        else:
            st.title("Job Recommender")
            st.info("GitHubアカウントでログインしてください。")
            render_login_button(redirect_uri)
        st.stop()

    # ===== 以降は Cookie有り or OAuthコールバック =====
    redirect_uri = get_redirect_uri()
    cookie_manager = get_cookie_manager()
    initialize_session(cookie_manager)

    logout_page, pages = _build_pages()
    pg = st.navigation(pages, position="hidden")
    is_logout_page = _is_logout_page(pg, logout_page)

    if not is_authenticated() and not is_logout_page:
        if should_auto_redirect_to_auth():
            auth_url = get_authorization_url(redirect_uri)
            st.markdown(
                f'<meta http-equiv="refresh" content="0; url={auth_url}">',
                unsafe_allow_html=True,
            )
        else:
            st.title("Job Recommender")
            st.info("GitHubアカウントでログインしてください。")
            render_login_button(redirect_uri)
        st.stop()

    if not is_logout_page:
        render_sidebar(cookie_manager, redirect_uri)

    pg.run()


if __name__ == "__main__":
    run()
