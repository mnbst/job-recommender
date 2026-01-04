"""Welcome page component for unauthenticated users."""

import streamlit as st


def render_welcome() -> None:
    """未ログイン時のウェルカムメッセージを表示."""
    st.markdown("""
    ### Job Recommender とは

    GitHubのプロファイルを分析して、あなたに最適な求人をレコメンドするサービスです。

    ---

    **特徴:**
    - GitHubリポジトリの自動解析
    - 採用担当者目線でのプロファイル生成
    - Perplexity AI による求人検索
    - マッチング理由とソース付きのレコメンド

    ---

    **サイドバーからGitHubでログインして始めましょう！**
    """)
