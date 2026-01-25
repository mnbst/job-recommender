"""Job Recommender - Streamlitのルーティング用エントリーポイント。"""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.services.app_bootstrap import get_redirect_uri, initialize_session, setup_app
from app.services.auth import ensure_authenticated
from app.services.logging_config import get_logger
from app.services.streamlit_components.cookie_manager import get_cookie_manager
from app.ui import render_sidebar

logger = get_logger(__name__)


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


def run() -> None:
    """アプリ起動処理（設定・認証・ナビゲーション）。"""
    setup_app()

    # LPリダイレクト中は何も表示せずに停止（リダイレクト完了待ち）
    if st.session_state.get("redirect_to_lp", False):
        st.stop()

    # セッション初期化とページ構成
    redirect_uri = get_redirect_uri()
    cookie_manager = get_cookie_manager()
    initialize_session(cookie_manager)

    logout_page, pages = _build_pages()
    pg = st.navigation(pages, position="hidden")
    is_logout_page = _is_logout_page(pg, logout_page)

    # 認証チェック（未認証なら自動リダイレクト）
    if not is_logout_page:
        ensure_authenticated(redirect_uri, cookie_manager)

    # サイドバー表示（認証済みのみ）
    if not is_logout_page:
        render_sidebar(cookie_manager)

    pg.run()


if __name__ == "__main__":
    run()
