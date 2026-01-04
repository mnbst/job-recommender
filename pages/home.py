"""ホームページ - メイン機能."""

import streamlit as st

from components import job_search, profile_section, render_welcome
from components.job_search import load_settings
from services.auth import get_current_user, is_authenticated
from services.quota import get_quota_status

# デフォルトのリポジトリ数
DEFAULT_REPO_LIMIT = 10


def render_home() -> None:
    """ホームページを描画."""
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


render_home()
