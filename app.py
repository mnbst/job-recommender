"""Job Recommender - Streamlit Application."""

import streamlit as st

from services.github import analyze_github_profile
from services.profile import generate_profile, analyze_job_matches
from services.research import search_jobs

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

            # Step 3: Search jobs
            st.header("🔍 求人レコメンド")

            with st.spinner("求人を検索中..."):
                job_results = search_jobs(profile, location=job_location)

                if job_results.get("status") == "success" and job_results.get("jobs"):
                    jobs = job_results["jobs"]
                    st.success(f"✅ {len(jobs)}件の求人が見つかりました")
                    st.caption(f"検索クエリ: {job_results.get('query', '')}")

                    # Step 4: Analyze matches
                    st.info("🎯 マッチング分析中...")
                    matches = analyze_job_matches(profile, jobs)

                    # Create a lookup for match data
                    match_data = {m["index"]: m for m in matches}

                    # Display jobs sorted by match score
                    for match in matches:
                        job = jobs[match["index"]]
                        score = match.get("match_score", 0)

                        # Color-coded score
                        if score >= 4:
                            score_color = "🟢"
                        elif score >= 3:
                            score_color = "🟡"
                        else:
                            score_color = "🔴"

                        with st.expander(
                            f"{score_color} **{job.title}** @ {job.company_name} (マッチ度: {score}/5)"
                        ):
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                st.write("**会社:**", job.company_name)
                                st.write("**勤務地:**", job.location)
                                st.write("**説明:**")
                                st.write(
                                    job.description[:300] + "..."
                                    if len(job.description) > 300
                                    else job.description
                                )

                                if job.detected_extensions:
                                    ext = job.detected_extensions
                                    if ext.get("salary"):
                                        st.write("**給与:**", ext.get("salary"))
                                    if ext.get("schedule_type"):
                                        st.write(
                                            "**勤務形態:**", ext.get("schedule_type")
                                        )

                                if job.job_link:
                                    st.link_button("求人を見る", job.job_link)

                            with col2:
                                st.write("**マッチ理由:**")
                                st.write(match.get("match_reason", ""))

                                st.write("**注目ポイント:**")
                                for highlight in match.get("highlights", []):
                                    st.write(f"• {highlight}")

                else:
                    error_msg = job_results.get("error", "求人検索に失敗しました")
                    st.warning(f"⚠️ {error_msg}")

                    if "SERPAPI_API_KEY" in error_msg:
                        st.info(
                            "💡 SerpAPI APIキーを設定してください。https://serpapi.com で取得できます。"
                        )

                    # Show job fit info as alternative
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
    4. SerpAPIで求人を検索し、マッチング分析

    ---

    **機能:**
    - 📦 GitHubリポジトリの自動解析
    - 🤖 採用担当者目線でのプロファイル生成
    - 🔍 SerpAPI Google Jobs による求人検索
    - 🎯 AIによるマッチング分析
    """)
