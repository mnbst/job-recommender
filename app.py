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
    restore_session,
)
from services.cache import (
    UserSettings,
    get_cached_profile,
    get_cached_repos,
    get_user_settings,
    invalidate_profile_cache,
    invalidate_repos_cache,
    save_profile_cache,
    save_repos_cache,
    save_user_settings,
)
from services.github import analyze_github_profile
from services.profile import generate_profile
from services.research import JobPreferences, search_jobs
from services.session import get_cookie_manager

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

st.title("💼 Job Recommender")
st.subheader("GitHubプロファイルから最適な求人をレコメンド")

# Sidebar
with st.sidebar:
    st.header("アカウント")

    if is_authenticated():
        render_user_info(cookie_manager)
        st.divider()

        # 認証済みユーザーのGitHubユーザー名を自動設定
        user = get_current_user()
        github_username = user.login if user else ""
        user_id = user.id if user else 0

        # Firestoreから設定を読み込み（初回のみ）
        if "settings_loaded" not in st.session_state and user_id:
            saved_settings = get_user_settings(user_id)
            st.session_state["repo_limit"] = saved_settings.repo_limit
            st.session_state["job_location"] = saved_settings.job_location
            st.session_state["salary_range"] = saved_settings.salary_range
            st.session_state["work_style"] = saved_settings.work_style
            st.session_state["job_type"] = saved_settings.job_type
            st.session_state["employment_type"] = saved_settings.employment_type
            st.session_state["other_preferences"] = saved_settings.other_preferences
            st.session_state["settings_loaded"] = True

        def save_settings() -> None:
            """設定をFirestoreに保存."""
            if not user_id:
                return
            settings = UserSettings(
                repo_limit=st.session_state.get("repo_limit", 10),
                job_location=st.session_state.get("job_location", "東京"),
                salary_range=st.session_state.get("salary_range", "指定なし"),
                work_style=st.session_state.get("work_style", []),
                job_type=st.session_state.get("job_type", []),
                employment_type=st.session_state.get("employment_type", []),
                other_preferences=st.session_state.get("other_preferences", ""),
            )
            save_user_settings(user_id, settings)

        st.header("分析設定")
        repo_limit = st.slider(
            "分析するリポジトリ数",
            1,
            20,
            key="repo_limit",
            on_change=save_settings,
        )

        st.header("希望条件")
        job_location = st.text_input(
            "勤務地",
            placeholder="例: 東京、大阪、リモート",
            key="job_location",
            on_change=save_settings,
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
            key="salary_range",
            on_change=save_settings,
        )
        work_style = st.multiselect(
            "働き方",
            options=["フルリモート", "ハイブリッド", "出社", "フレックス", "副業OK"],
            key="work_style",
            on_change=save_settings,
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
            key="job_type",
            on_change=save_settings,
        )
        employment_type = st.multiselect(
            "雇用形態",
            options=["正社員", "フリーランス", "業務委託", "契約社員"],
            key="employment_type",
            on_change=save_settings,
        )
        other_preferences = st.text_area(
            "その他の希望・アピール",
            placeholder="例: マネジメント経験3年、金融業界での開発経験、スタートアップ希望、自社サービス開発、英語環境など",
            height=100,
            key="other_preferences",
            on_change=save_settings,
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
        employment_type = []
        other_preferences = ""
        analyze_button = False

# 再生成フラグのチェック
should_analyze = analyze_button or st.session_state.get("force_regenerate", False)


def on_regenerate(user_id: int) -> None:
    """再生成ボタンのコールバック."""
    invalidate_repos_cache(user_id)
    invalidate_profile_cache(user_id)
    # session_stateの分析結果もクリア
    st.session_state.pop("repos", None)
    st.session_state.pop("profile", None)
    st.session_state.pop("job_results", None)
    st.session_state["force_regenerate"] = True


# 分析実行
if should_analyze and github_username:
    st.session_state["force_regenerate"] = False

    with st.spinner("GitHubプロファイルを分析中..."):
        try:
            user = get_current_user()
            if user is None:
                st.error("ユーザー情報の取得に失敗しました")
                st.stop()

            # Step 1: Fetch GitHub data (with cache)
            cached_repos = get_cached_repos(user.id, repo_limit)

            if cached_repos:
                st.info("📦 キャッシュからリポジトリ情報を取得しました")
                repos = cached_repos
            else:
                st.info("📦 リポジトリ情報を取得中...")
                repos = analyze_github_profile(github_username, repo_limit)
                if repos:
                    save_repos_cache(user.id, repos)

            if not repos:
                st.error("リポジトリが見つかりませんでした")
                st.stop()

            st.success(f"✅ {len(repos)}個のリポジトリを取得しました")
            st.session_state["repos"] = repos

            # Step 2: Check cache or generate profile
            cached_profile = get_cached_profile(user.id, len(repos))

            if cached_profile:
                st.info("📦 キャッシュからプロファイルを取得しました")
                profile = cached_profile
            else:
                st.info("🤖 プロファイルを生成中...")
                profile = generate_profile(repos)
                save_profile_cache(
                    user_id=user.id,
                    github_login=user.login,
                    profile_data=profile,
                    repo_count=len(repos),
                )

            st.session_state["profile"] = profile

            # Step 3: Search jobs with Perplexity
            preferences = JobPreferences(
                location=job_location,
                salary_range=salary_range,
                work_style=work_style if work_style else None,
                job_type=job_type if job_type else None,
                employment_type=employment_type if employment_type else None,
                other=other_preferences,
            )
            job_results = search_jobs(profile, preferences=preferences)
            st.session_state["job_results"] = job_results

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

# session_stateにデータがあれば表示
if "profile" in st.session_state and is_authenticated():
    user = get_current_user()
    profile = st.session_state["profile"]
    repos = st.session_state.get("repos", [])

    # Display profile
    with st.container(horizontal_alignment="left"):
        st.header("📊 開発者プロファイル")
        if user:
            st.button(
                "🔄 再生成",
                help="最新のリポジトリ情報でプロファイルを再生成",
                on_click=on_regenerate,
                args=(user.id,),
            )

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

    # Display job results
    st.header("🔍 求人レコメンド")

    job_results = st.session_state.get("job_results")
    if job_results and job_results.status == "success" and job_results.recommendations:
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

                    @st.fragment
                    def fetch_job_url(
                        company: str,
                        job_title: str,
                        location: str,
                        key: str,
                        fallback_url: str | None,
                    ) -> None:
                        """求人URLを取得するフラグメント."""
                        from services.research import search_job_url

                        cache_key = f"job_url_{key}"

                        # キャッシュがあれば表示
                        if cache_key in st.session_state:
                            result = st.session_state[cache_key]
                            if result["url"]:
                                st.link_button("📋 求人ページ", result["url"])
                            elif fallback_url:
                                st.link_button("📄 参考ページ", fallback_url)
                            else:
                                st.caption("❌ 見つかりません")
                            return

                        # ボタンで検索実行
                        if st.button("🔗 リンク取得", key=f"btn_{key}"):
                            with st.spinner("検索中..."):
                                result = search_job_url(company, job_title, location)
                                st.session_state[cache_key] = {
                                    "url": result.url,
                                    "status": result.status,
                                }
                                st.rerun(scope="fragment")

                    job_key = f"{rec.company}_{rec.job_title}".replace(" ", "_")
                    fallback = rec.sources[0].url if rec.sources else None
                    fetch_job_url(
                        rec.company, rec.job_title, rec.location, job_key, fallback
                    )

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
                    pass  # 右カラムは空

    elif job_results:
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
        st.write("**理想的な職種:**", ", ".join(job_fit.get("ideal_roles", [])))
        st.write(
            "**マッチする企業タイプ:**",
            ", ".join(job_fit.get("company_types", [])),
        )
        st.write("**検索キーワード:**", ", ".join(job_fit.get("keywords", [])))

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
