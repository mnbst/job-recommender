"""ホームページ - メイン機能."""

import streamlit as st

from app.services.auth import get_current_user, is_authenticated
from app.services.quota import get_quota_status
from app.services.session_keys import SHOW_PROFILE_SUCCESS
from app.ui import job_search, profile_section, render_welcome
from app.ui.job_search import load_settings

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

        with st.expander("クレジットの使い方"):
            st.markdown(
                """
| 機能 | 消費 | 内容 |
|------|------|------|
| プロファイル生成 | 1 | GitHubリポジトリを分析 |
| 求人検索 | 1 | 3件の求人を表示 |
| もっと見る | 1 | 最大3件を追加表示 |
"""
            )

        # 設定を読み込み
        load_settings(user_id)

        # プロファイルセクション
        profile = profile_section(
            user_id=user_id,
            user_login=user.login,
            quota=quota,
            repo_limit=DEFAULT_REPO_LIMIT,
        )

        # プロファイル生成成功後のガイダンス
        if st.session_state.pop(SHOW_PROFILE_SUCCESS, False):
            st.success(
                "プロファイルを生成しました！"
                "下の「求人検索」で希望条件を設定して求人を探しましょう。"
            )

        if profile:
            st.divider()
            job_search(user_id, profile, quota, DEFAULT_REPO_LIMIT)
    else:
        render_welcome()


render_home()
