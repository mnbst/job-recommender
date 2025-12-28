"""Job Recommender - Streamlit Application."""

import logging
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.auth import (
    get_current_user,
    handle_oauth_callback,
    is_authenticated,
    render_login_button,
    render_user_info,
)
from services.github import analyze_github_profile
from services.profile import generate_profile
from services.research import JobPreferences, search_jobs

# ログ設定（Cloud Run環境では構造化ログを使用）
if os.environ.get("K_SERVICE"):
    # Cloud Run環境
    import google.cloud.logging

    client = google.cloud.logging.Client()
    client.setup_logging()
else:
    # ローカル環境
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

# OAuthコールバック処理
handle_oauth_callback()

# リダイレクトURI（本番環境ではCloud RunのURL）
REDIRECT_URI = os.environ.get(
    "OAUTH_REDIRECT_URI",
    "http://localhost:8501",
)

st.title("💼 Job Recommender")
st.subheader("GitHubプロファイルから最適な求人をレコメンド")

# Sidebar
with st.sidebar:
    st.header("アカウント")

    if is_authenticated():
        render_user_info()
        st.divider()

        # 認証済みユーザーのGitHubユーザー名を自動設定
        user = get_current_user()
        github_username = user.login if user else ""

        st.header("分析設定")
        repo_limit = st.slider("分析するリポジトリ数", 1, 20, 10)

        st.header("希望条件")
        job_location = st.text_input(
            "勤務地", value="東京", placeholder="例: 東京、大阪、リモート"
        )
        salary_range = st.select_slider(
            "希望年収",
            options=[
                "指定なし",
                "400万〜",
                "500万〜",
                "600万〜",
                "800万〜",
                "1000万〜",
            ],
            value="指定なし",
        )
        work_style = st.multiselect(
            "働き方",
            options=["フルリモート", "ハイブリッド", "出社", "フレックス", "副業OK"],
            default=[],
        )
        job_type = st.multiselect(
            "希望職種",
            options=[
                "バックエンド",
                "フロントエンド",
                "フルスタック",
                "インフラ/SRE",
                "データエンジニア",
                "機械学習",
                "テックリード",
                "EM",
            ],
            default=[],
        )
        other_preferences = st.text_area(
            "その他の希望・アピール",
            placeholder="例: マネジメント経験3年、金融業界での開発経験、スタートアップ希望、自社サービス開発、英語環境など",
            height=100,
        )

        analyze_button = st.button("プロファイル分析", type="primary")
    else:
        st.info("GitHubアカウントでログインして、プロファイル分析を開始しましょう。")
        render_login_button(REDIRECT_URI)
        github_username = ""
        repo_limit = 10
        job_location = "東京"
        salary_range = "指定なし"
        work_style = []
        job_type = []
        other_preferences = ""
        analyze_button = False

# Main content
if analyze_button and github_username:
    with st.spinner("GitHubプロファイルを分析中..."):
        try:
            # Step 1: Fetch GitHub data
            st.info("📦 リポジトリ情報を取得中...")
            repos = analyze_github_profile(github_username, repo_limit)

            if not repos:
                st.error("リポジトリが見つかりませんでした")
                st.stop()

            st.success(f"✅ {len(repos)}個のリポジトリを取得しました")

            # Step 2: Generate profile
            st.info("🤖 プロファイルを生成中...")
            profile = generate_profile(repos)

            # Display profile
            st.header("📊 開発者プロファイル")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("技術スタック")
                tech = profile.get("tech_stack", {})
                st.write("**言語:**", ", ".join(tech.get("languages", [])))
                st.write("**フレームワーク:**", ", ".join(tech.get("frameworks", [])))
                st.write("**インフラ:**", ", ".join(tech.get("infrastructure", [])))

                st.subheader("得意領域")
                for area in profile.get("expertise_areas", []):
                    st.write(f"• {area}")

            with col2:
                st.subheader("スキル評価")
                assessment = profile.get("skill_assessment", {})
                st.write("**コード品質:**", assessment.get("code_quality", "-"))
                st.write("**設計力:**", assessment.get("design_ability", "-"))
                st.write("**完遂力:**", assessment.get("completion_rate", "-"))

                st.subheader("興味・関心")
                for interest in profile.get("interests", []):
                    st.write(f"• {interest}")

            st.subheader("💡 総合評価")
            st.info(profile.get("summary", ""))

            # Step 3: Search jobs with Perplexity (includes matching analysis)
            st.header("🔍 求人レコメンド")

            with st.spinner("求人を検索・分析中..."):
                preferences = JobPreferences(
                    location=job_location,
                    salary_range=salary_range,
                    work_style=work_style if work_style else None,
                    job_type=job_type if job_type else None,
                    other=other_preferences,
                )
                job_results = search_jobs(profile, preferences=preferences)

                if job_results.status == "success" and job_results.recommendations:
                    st.success(
                        f"✅ {len(job_results.recommendations)}件の求人がレコメンドされました"
                    )

                    for rec in job_results.recommendations:
                        with st.expander(f"**{rec.job_title}** @ {rec.company}"):
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                st.write("**会社:**", rec.company)
                                st.write("**勤務地:**", rec.location)
                                if rec.salary_range:
                                    st.write("**給与:**", rec.salary_range)

                                st.write("---")
                                st.write("**マッチ理由:**")
                                st.info(rec.reason.summary)

                                st.write("**マッチした条件:**")
                                for condition in rec.reason.matched_conditions:
                                    st.write(f"• {condition}")

                                if rec.reason.why_good:
                                    st.write("**詳細:**")
                                    st.write(rec.reason.why_good)

                            with col2:
                                st.write("**ソース:**")
                                for source in rec.sources:
                                    st.markdown(f"- [{source.used_for}]({source.url})")

                else:
                    error_msg = job_results.error or "求人検索に失敗しました"
                    st.warning(f"⚠️ {error_msg}")

                    if "PERPLEXITY_API_KEY" in error_msg:
                        st.info(
                            "💡 Perplexity APIキーを設定してください。"
                            "https://www.perplexity.ai で取得できます。"
                        )

                    # Show job fit info as fallback
                    st.subheader("推奨される職種・企業")
                    job_fit = profile.get("job_fit", {})
                    st.write(
                        "**理想的な職種:**", ", ".join(job_fit.get("ideal_roles", []))
                    )
                    st.write(
                        "**マッチする企業タイプ:**",
                        ", ".join(job_fit.get("company_types", [])),
                    )
                    st.write(
                        "**検索キーワード:**", ", ".join(job_fit.get("keywords", []))
                    )

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

else:
    # Welcome message
    if is_authenticated():
        st.markdown("""
        ### 使い方

        1. サイドバーの「プロファイル分析」ボタンをクリック
        2. AIがリポジトリを分析し、プロファイルを生成
        3. Perplexity AIが求人を検索・マッチング分析

        ---

        **機能:**
        - 📦 GitHubリポジトリの自動解析
        - 🤖 採用担当者目線でのプロファイル生成
        - 🔍 Perplexity AI による求人検索
        - 🎯 マッチング理由とソース付きのレコメンド
        """)
    else:
        st.markdown("""
        ### Job Recommender とは

        GitHubのプロファイルを分析して、あなたに最適な求人をレコメンドするサービスです。

        ---

        **特徴:**
        - 📦 GitHubリポジトリの自動解析
        - 🤖 採用担当者目線でのプロファイル生成
        - 🔍 Perplexity AI による求人検索
        - 🎯 マッチング理由とソース付きのレコメンド

        ---

        👈 **サイドバーからGitHubでログインして始めましょう！**
        """)
