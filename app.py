"""Job Recommender - Streamlit Application."""

import logging
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from components import (
    job_search,
    profile_section,
    render_sidebar,
    render_welcome,
)
from components.job_search import load_settings
from services.auth import (
    get_current_user,
    handle_oauth_callback,
    is_authenticated,
    restore_session,
)
from services.quota import get_quota_status
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

# リダイレクトURI（本番環境ではCloud RunのURL）
REDIRECT_URI = os.environ.get(
    "OAUTH_REDIRECT_URI",
    "http://localhost:8501",
)

# デフォルトのリポジトリ数
DEFAULT_REPO_LIMIT = 10

# Sidebar
render_sidebar(cookie_manager, REDIRECT_URI)

# Main Content
st.title("Job Recommender")
st.caption("GitHubプロファイルから最適な求人をレコメンド")

if is_authenticated():
    user = get_current_user()
    if not user:
        st.error("ユーザー情報の取得に失敗しました")
        st.stop()

    user_id = user.id
    quota = get_quota_status(user_id)

    # 設定を読み込み
    load_settings(user_id)

    # プロファイルセクション
    profile = profile_section(
        user_id=user_id,
        user_login=user.login,
        quota=quota,
        repo_limit=DEFAULT_REPO_LIMIT,
    )

    if profile:
        st.divider()
        job_search(user_id, profile, quota, DEFAULT_REPO_LIMIT)
else:
    render_welcome()
