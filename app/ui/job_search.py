"""Job search component."""

import streamlit as st

from app.services.cache import get_user_settings, save_user_settings
from app.services.models import (
    JobPreferences,
    JobSearchResult,
    QuotaStatus,
    UserSettings,
)
from app.services.quota import consume_credit, get_quota_status
from app.services.research import search_jobs
from app.services.session_keys import (
    EMPLOYMENT_TYPE,
    JOB_LOCATION,
    JOB_PREFERENCES,
    JOB_RESULTS,
    JOB_TYPE,
    OTHER_PREFERENCES,
    SALARY_RANGE,
    SETTINGS_LOADED,
    WORK_STYLE,
)
from app.ui.credits import render_credit_button


def _save_settings(user_id: int, repo_limit: int) -> None:
    """設定をFirestoreに保存."""
    if not user_id:
        return
    settings = UserSettings(
        repo_limit=repo_limit,
        job_location=st.session_state.get(JOB_LOCATION, "東京"),
        salary_range=st.session_state.get(SALARY_RANGE, "指定なし"),
        work_style=st.session_state.get(WORK_STYLE, []),
        job_type=st.session_state.get(JOB_TYPE, []),
        employment_type=st.session_state.get(EMPLOYMENT_TYPE, []),
        other_preferences=st.session_state.get(OTHER_PREFERENCES, ""),
    )
    save_user_settings(user_id, settings)


def load_settings(user_id: int) -> None:
    """Firestoreから設定を読み込み."""
    if SETTINGS_LOADED not in st.session_state and user_id:
        saved_settings = get_user_settings(user_id)
        st.session_state[JOB_LOCATION] = saved_settings.job_location
        st.session_state[SALARY_RANGE] = saved_settings.salary_range
        st.session_state[WORK_STYLE] = saved_settings.work_style
        st.session_state[JOB_TYPE] = saved_settings.job_type
        st.session_state[EMPLOYMENT_TYPE] = saved_settings.employment_type
        st.session_state[OTHER_PREFERENCES] = saved_settings.other_preferences
        st.session_state[SETTINGS_LOADED] = True


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
                    key=JOB_LOCATION,
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
                    key=SALARY_RANGE,
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
                    key=WORK_STYLE,
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
                        "機械学習/AI",
                        "テックリード",
                        "EM/VPoE",
                        "プロダクトマネージャー",
                        "デザイナー（UI/UX）",
                        "データアナリスト",
                        "QA/テスト",
                        "マーケター",
                        "セールス/BizDev",
                    ],
                    key=JOB_TYPE,
                    help="複数選択可。GitHubの内容に関わらず希望職種を選べます",
                )
                st.multiselect(
                    "雇用形態",
                    options=["正社員", "フリーランス", "業務委託", "契約社員"],
                    key=EMPLOYMENT_TYPE,
                )
                st.text_area(
                    "その他の希望またはアピールポイント",
                    placeholder="例: スタートアップ希望、自社サービス開発、マネジメント経験ありなど",
                    height=100,
                    key=OTHER_PREFERENCES,
                )

    search_conditions()
    search_button = render_credit_button(
        "求人を検索 (1クレジット → 3件表示)",
        credits=quota.credits,
        can_use=quota.can_use,
        type="primary",
        use_container_width=True,
        layout=(1, 3),
    )

    if search_button:
        _save_settings(user_id, repo_limit)
        consume_credit(user_id)

        preferences = _build_preferences()
        # 検索条件を保存（追加検索用）
        st.session_state[JOB_PREFERENCES] = preferences
        _set_job_results(profile, preferences)

    _display_job_results(user_id, profile)


def _display_job_results(user_id: int, profile: dict) -> None:
    """求人結果を表示."""
    job_results: JobSearchResult | None = st.session_state.get(JOB_RESULTS)
    _render_job_results_state(job_results, user_id, profile)


def _render_job_results_state(
    job_results: JobSearchResult | None,
    user_id: int,
    profile: dict,
) -> None:
    """求人結果の状態に応じて表示."""
    if not job_results:
        return

    if job_results.status == "success" and job_results.recommendations:
        _render_job_results(job_results)
        _show_more_button(user_id, profile)
        return

    if job_results.error:
        st.warning(f"{job_results.error}")


def _render_job_results(job_results: JobSearchResult) -> None:
    """求人結果の一覧を表示."""
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


def _show_more_button(user_id: int, profile: dict) -> None:
    """追加検索ボタンを表示."""
    quota = get_quota_status(user_id)
    job_results: JobSearchResult | None = st.session_state.get(JOB_RESULTS)

    if not job_results or not job_results.recommendations:
        return

    more_button = render_credit_button(
        "もっと見る (最大3件)",
        credits=quota.credits,
        can_use=quota.can_use,
        caption=f"1クレジット消費 (残り {quota.credits})",
        use_container_width=True,
        layout=(1, 3),
    )

    if more_button:
        consume_credit(user_id)

        # 既存の企業名を取得して除外
        exclude_companies = [rec.company for rec in job_results.recommendations]

        # 保存された検索条件を取得
        preferences = st.session_state.get(JOB_PREFERENCES) or JobPreferences()
        _append_job_results(profile, preferences, exclude_companies)


def _build_preferences() -> JobPreferences:
    """検索条件をsession_stateから構築."""
    return JobPreferences(
        location=st.session_state.get(JOB_LOCATION, ""),
        salary_range=st.session_state.get(SALARY_RANGE, "指定なし"),
        work_style=st.session_state.get(WORK_STYLE) or None,
        job_type=st.session_state.get(JOB_TYPE) or None,
        employment_type=st.session_state.get(EMPLOYMENT_TYPE) or None,
        other=st.session_state.get(OTHER_PREFERENCES, ""),
    )


def _run_job_search(
    profile: dict,
    preferences: JobPreferences,
    *,
    exclude_companies: list[str] | None = None,
) -> JobSearchResult:
    """求人検索を実行."""
    return search_jobs(
        profile,
        preferences=preferences,
        exclude_companies=exclude_companies,
    )


def _set_job_results(profile: dict, preferences: JobPreferences) -> None:
    """求人検索の結果をセット."""
    with st.spinner("求人を検索中..."):
        job_results = _run_job_search(profile, preferences)
        st.session_state[JOB_RESULTS] = job_results
        st.rerun()


def _append_job_results(
    profile: dict,
    preferences: JobPreferences,
    exclude_companies: list[str],
) -> None:
    """追加検索結果を既存結果にマージ."""
    with st.spinner("追加の求人を検索中..."):
        new_results = _run_job_search(
            profile,
            preferences,
            exclude_companies=exclude_companies,
        )

        if new_results.status == "success" and new_results.recommendations:
            job_results: JobSearchResult | None = st.session_state.get(JOB_RESULTS)
            existing = job_results.recommendations if job_results else []
            combined_recommendations = existing + new_results.recommendations
            st.session_state[JOB_RESULTS] = JobSearchResult(
                recommendations=combined_recommendations,
                status="success",
            )
        elif new_results.error:
            st.warning(f"追加検索エラー: {new_results.error}")
        else:
            st.info("これ以上の求人が見つかりませんでした")
        st.rerun()
