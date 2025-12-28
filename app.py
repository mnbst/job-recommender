"""Job Recommender - Streamlit Application."""

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.github import analyze_github_profile
from services.profile import generate_profile
from services.research import search_jobs

# .env.local から環境変数を読み込み
load_dotenv(Path(__file__).parent / ".env.local")
# Page config
st.set_page_config(
    page_title="Job Recommender",
    page_icon="💼",
    layout="wide",
)

st.title("💼 Job Recommender")
st.subheader("GitHubプロファイルから最適な求人をレコメンド")

# Sidebar
with st.sidebar:
    st.header("設定")
    github_username = st.text_input(
        "GitHubユーザー名",
        placeholder="例: octocat",
    )
    repo_limit = st.slider("分析するリポジトリ数", 1, 20, 10)
    job_location = st.text_input(
        "勤務地", value="Japan", placeholder="例: Tokyo, Japan"
    )

    analyze_button = st.button("プロファイル分析", type="primary")

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
                job_results = search_jobs(profile, location=job_location)

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
    st.markdown("""
    ### 使い方

    1. サイドバーにGitHubユーザー名を入力
    2. 「プロファイル分析」ボタンをクリック
    3. AIがリポジトリを分析し、プロファイルを生成
    4. Perplexity AIが求人を検索・マッチング分析

    ---

    **機能:**
    - 📦 GitHubリポジトリの自動解析
    - 🤖 採用担当者目線でのプロファイル生成
    - 🔍 Perplexity AI による求人検索
    - 🎯 マッチング理由とソース付きのレコメンド
    """)
