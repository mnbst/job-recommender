"""Job Recommender - Streamlitのルーティング用エントリーポイント。"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

import streamlit as st

from components import render_sidebar
from services.app_bootstrap import get_redirect_uri, initialize_session, setup_app
from services.auth import (
    get_authorization_url,
    is_authenticated,
    render_login_button,
    should_auto_redirect_to_auth,
)
from services.logging_config import log_structured
from services.session import get_cookie_manager, get_session_cookie

if TYPE_CHECKING:
    from services.components.cookie_manager import CookieManager

_COOKIE_WAIT_ATTEMPTS_KEY = "cookie_wait_attempts"
_COOKIE_WAIT_MAX = 3
_COOKIE_WAIT_INTERVAL_SECONDS = 0.2

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


def _maybe_wait_for_cookie(cookie_manager: CookieManager) -> bool:
    """Cookie反映待ち（コールドスタート対策）.

    Returns:
        True: 認証済みまたはCookie取得成功、False: 待機継続が必要
    """
    if is_authenticated():
        st.session_state.pop(_COOKIE_WAIT_ATTEMPTS_KEY, None)
        return True

    attempts = st.session_state.get(_COOKIE_WAIT_ATTEMPTS_KEY, 0)
    if attempts >= _COOKIE_WAIT_MAX:
        log_structured(
            logger,
            "Cookie wait attempts exceeded, proceeding to login flow",
            level=logging.WARNING,
            attempts=attempts,
        )
        st.session_state.pop(_COOKIE_WAIT_ATTEMPTS_KEY, None)
        return False  # ログインフローへ進む

    # Cookieコンポーネントを明示的にレンダリングして取得を促す
    cookie_manager._render()
    session_id = get_session_cookie(cookie_manager)

    log_structured(
        logger,
        "Cookie wait attempt",
        attempts=attempts + 1,
        session_id_present=bool(session_id),
        initialized=cookie_manager._initialized,
    )

    # Cookie取得成功した場合は待機終了
    if session_id:
        st.session_state.pop(_COOKIE_WAIT_ATTEMPTS_KEY, None)
        return True

    st.session_state[_COOKIE_WAIT_ATTEMPTS_KEY] = attempts + 1
    with st.spinner("セッションを復元中..."):
        time.sleep(_COOKIE_WAIT_INTERVAL_SECONDS)
    # Client-side cookie取得のための限定的なrerun
    st.rerun()


def run() -> None:
    """アプリ起動処理（設定・認証・ナビゲーション）。"""
    setup_app()
    redirect_uri = get_redirect_uri()
    cookie_manager = get_cookie_manager()
    initialize_session(cookie_manager)

    logout_page, pages = _build_pages()
    pg = st.navigation(pages, position="hidden")
    is_logout_page = _is_logout_page(pg, logout_page)

    if not is_logout_page:
        _maybe_wait_for_cookie(cookie_manager)

    if not is_authenticated() and not is_logout_page:
        if should_auto_redirect_to_auth():
            auth_url = get_authorization_url(redirect_uri)
            st.markdown(
                f'<meta http-equiv="refresh" content="0; url={auth_url}">',
                unsafe_allow_html=True,
            )
        else:
            # フォールバック: ログインボタンを表示（コールドスタート対策）
            st.title("Job Recommender")
            st.info("GitHubアカウントでログインしてください。")
            render_login_button(redirect_uri)
        st.stop()

    if not is_logout_page:
        render_sidebar(cookie_manager, redirect_uri)

    pg.run()


if __name__ == "__main__":
    run()
