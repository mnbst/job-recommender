"""Job search component."""

import streamlit as st

from services.cache import UserSettings, get_user_settings, save_user_settings
from services.quota import QuotaStatus, consume_credit, get_quota_status
from services.research import JobPreferences, JobSearchResult, search_jobs
from services.session_keys import JOB_PREFERENCES, JOB_RESULTS


def _save_settings(user_id: int, repo_limit: int) -> None:
    """設定をFirestoreに保存."""
    if not user_id:
        return
    settings = UserSettings(
        repo_limit=repo_limit,
        job_location=st.session_state.get("job_location", "東京"),
        salary_range=st.session_state.get("salary_range", "指定なし"),
        work_style=st.session_state.get("work_style", []),
        job_type=st.session_state.get("job_type", []),
        employment_type=st.session_state.get("employment_type", []),
        other_preferences=st.session_state.get("other_preferences", ""),
    )
    save_user_settings(user_id, settings)


def load_settings(user_id: int) -> None:
    """Firestoreから設定を読み込み."""
    if "settings_loaded" not in st.session_state and user_id:
        saved_settings = get_user_settings(user_id)
        st.session_state["job_location"] = saved_settings.job_location
        st.session_state["salary_range"] = saved_settings.salary_range
        st.session_state["work_style"] = saved_settings.work_style
        st.session_state["job_type"] = saved_settings.job_type
        st.session_state["employment_type"] = saved_settings.employment_type
        st.session_state["other_preferences"] = saved_settings.other_preferences
        st.session_state["settings_loaded"] = True


def job_search(
    user_id: int,
    profile: dict,
    quota: QuotaStatus,
    repo_limit: int,
) -> None:
    """求人検索フラグメント."""
    st.header("求人検索")

    @st.fragment
    def search_conditions():
        """検索条件フォーム."""
        with st.expander("希望条件を設定", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.text_input(
                    "勤務地",
                    placeholder="例: 東京、大阪、リモート",
                    key="job_location",
                )
                st.select_slider(
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
                )
                st.multiselect(
                    "働き方",
                    options=[
                        "フルリモート",
                        "ハイブリッド",
                        "出社",
                        "フレックス",
                        "副業OK",
                    ],
                    key="work_style",
                )

            with col2:
                st.multiselect(
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
                )
                st.multiselect(
                    "雇用形態",
                    options=["正社員", "フリーランス", "業務委託", "契約社員"],
                    key="employment_type",
                )
                st.text_area(
                    "その他の希望",
                    placeholder="例: スタートアップ希望、自社サービス開発など",
                    height=100,
                    key="other_preferences",
                )

    search_conditions()
    search_col1, search_col2 = st.columns([1, 3])
    with search_col1:
        search_disabled = not quota.can_use
        search_button = st.button(
            "求人を検索",
            disabled=search_disabled,
            type="primary",
            use_container_width=True,
        )
    with search_col2:
        st.caption(f"残り {quota.credits} クレジット")

    if search_disabled:
        st.warning("クレジットがありません。")

    if search_button:
        _save_settings(user_id, repo_limit)
        consume_credit(user_id)

        with st.spinner("求人を検索中..."):
            preferences = JobPreferences(
                location=st.session_state.get("job_location", ""),
                salary_range=st.session_state.get("salary_range", "指定なし"),
                work_style=st.session_state.get("work_style") or None,
                job_type=st.session_state.get("job_type") or None,
                employment_type=st.session_state.get("employment_type") or None,
                other=st.session_state.get("other_preferences", ""),
            )
            # 検索条件を保存（追加検索用）
            st.session_state[JOB_PREFERENCES] = preferences
            job_results = search_jobs(profile, preferences=preferences)
            st.session_state[JOB_RESULTS] = job_results
            st.rerun()

    _display_job_results(user_id, profile)


def _display_job_results(user_id: int, profile: dict) -> None:
    """求人結果を表示."""
    job_results: JobSearchResult | None = st.session_state.get(JOB_RESULTS)

    if not job_results:
        return

    if job_results.status == "success" and job_results.recommendations:
        total = len(job_results.recommendations)
        st.success(f"{total}件の求人を表示")

        for rec in job_results.recommendations:
            with st.expander(f"**{rec.job_title}** @ {rec.company}"):
                st.write("**会社:**", rec.company)
                st.write("**勤務地:**", rec.location)
                if rec.salary_range:
                    st.write("**給与:**", rec.salary_range)

                st.write("---")
                st.write("**マッチ理由:**")
                st.info(rec.reason.summary)

                st.write("**マッチした条件:**")
                for condition in rec.reason.matched_conditions:
                    st.write(f"- {condition}")

                if rec.reason.why_good:
                    st.write("**詳細:**")
                    st.write(rec.reason.why_good)

                if rec.sources:
                    st.write("**ソース:**")
                    for source in rec.sources:
                        st.markdown(f"- [{source.used_for}]({source.url})")

        # 「もっと見る」ボタン
        _show_more_button(user_id, profile)

    elif job_results.error:
        st.warning(f"{job_results.error}")


def _show_more_button(user_id: int, profile: dict) -> None:
    """追加検索ボタンを表示."""
    quota = get_quota_status(user_id)
    job_results: JobSearchResult | None = st.session_state.get(JOB_RESULTS)

    if not job_results or not job_results.recommendations:
        return

    col1, col2 = st.columns([1, 3])
    with col1:
        more_disabled = not quota.can_use
        more_button = st.button(
            "もっと見る (最大3件)",
            disabled=more_disabled,
            use_container_width=True,
        )
    with col2:
        st.caption(f"1クレジット消費 (残り {quota.credits})")

    if more_button:
        consume_credit(user_id)

        # 既存の企業名を取得して除外
        exclude_companies = [rec.company for rec in job_results.recommendations]

        # 保存された検索条件を取得
        preferences: JobPreferences | None = st.session_state.get(JOB_PREFERENCES)
        if preferences is None:
            preferences = JobPreferences()

        with st.spinner("追加の求人を検索中..."):
            new_results = search_jobs(
                profile,
                preferences=preferences,
                exclude_companies=exclude_companies,
            )

            if new_results.status == "success" and new_results.recommendations:
                combined_recommendations = (
                    job_results.recommendations + new_results.recommendations
                )
                st.session_state[JOB_RESULTS] = JobSearchResult(
                    recommendations=combined_recommendations,
                    status="success",
                )
            elif new_results.error:
                st.warning(f"追加検索エラー: {new_results.error}")
            else:
                st.info("これ以上の求人が見つかりませんでした")
            st.rerun()
