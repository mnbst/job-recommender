"""Job Recommender - Streamlit Application."""

import logging
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from components import render_sidebar
from services.auth import handle_oauth_callback, restore_session
from services.session import get_cookie_manager

# ログ設定（Cloud Run環境では構造化ログを使用）
if os.environ.get("K_SERVICE"):
    import google.cloud.logging

    client = google.cloud.logging.Client()
    client.setup_logging()
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

# .env.local から環境変数を読み込み
load_dotenv(Path(__file__).parent / ".env.local")

# Page config
st.set_page_config(
    page_title="Job Recommender",
    page_icon="💼",
    layout="wide",
)

# CookieManagerの取得（セッション永続化用）
cookie_manager = get_cookie_manager()

# セッション復元（Cookieから）
restore_session(cookie_manager)

# OAuthコールバック処理
handle_oauth_callback(cookie_manager)


# リダイレクトURI（localhost経由の場合は動的に設定）
def get_redirect_uri() -> str:
    """リクエストのホストに基づいてredirect_uriを決定."""
    # Streamlitのcontext からホスト情報を取得
    try:
        host_header = st.context.headers.get("Host", "")
        if host_header.startswith("localhost"):
            return f"http://{host_header}"
    except Exception:
        pass
    # デフォルトは環境変数
    return os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8501")


REDIRECT_URI = get_redirect_uri()

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
