"""Profile display component."""

import streamlit as st

from services.cache import (
    get_cached_profile,
    invalidate_profile_cache,
    invalidate_repos_cache,
    save_profile_cache,
    save_repos_cache,
)
from services.github import analyze_github_profile
from services.profile import generate_profile
from services.quota import QuotaStatus, consume_credit
from services.session_keys import JOB_RESULTS


def display_profile(profile: dict) -> None:
    """プロファイルを表示."""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("技術スタック")
        tech = profile.get("tech_stack", {})
        st.write("**言語:**", ", ".join(tech.get("languages", [])))
        st.write("**フレームワーク:**", ", ".join(tech.get("frameworks", [])))
        st.write("**インフラ:**", ", ".join(tech.get("infrastructure", [])))

        st.subheader("得意領域")
        for area in profile.get("expertise_areas", []):
            st.write(f"- {area}")

    with col2:
        st.subheader("スキル評価")
        assessment = profile.get("skill_assessment", {})
        st.write("**コード品質:**", assessment.get("code_quality", "-"))
        st.write("**設計力:**", assessment.get("design_ability", "-"))
        st.write("**完遂力:**", assessment.get("completion_rate", "-"))

        st.subheader("興味・関心")
        for interest in profile.get("interests", []):
            st.write(f"- {interest}")

    st.subheader("総合評価")
    st.info(profile.get("summary", ""))


def profile_section(
    user_id: int,
    user_login: str,
    quota: QuotaStatus,
    repo_limit: int,
) -> dict | None:
    """プロファイルセクションを描画.

    Returns:
        キャッシュまたは新規生成したプロファイル（なければNone）
    """
    st.header("開発者プロファイル")

    cached_profile = get_cached_profile(user_id, repo_limit)

    if cached_profile:
        display_profile(cached_profile)
        st.session_state["profile"] = cached_profile

        regen_col1, regen_col2 = st.columns([3, 1])
        with regen_col1:
            regen_disabled = not quota.can_use
            if st.button(
                "プロファイル再生成",
                disabled=regen_disabled,
                help="最新のリポジトリ情報でプロファイルを再生成",
            ):
                _regenerate_profile(user_id, user_login, repo_limit)

        with regen_col2:
            st.caption(f"残り {quota.credits} クレジット")

        if regen_disabled:
            st.warning("クレジットがありません。")

        return cached_profile

    # プロファイル未生成
    st.info("プロファイルを生成して、あなたに最適な求人を見つけましょう。")

    gen_col1, gen_col2 = st.columns([1, 3])
    with gen_col1:
        gen_disabled = not quota.can_use
        if st.button(
            "プロファイルを生成",
            type="primary",
            disabled=gen_disabled,
            use_container_width=True,
        ):
            _generate_profile(user_id, user_login, repo_limit)

    with gen_col2:
        st.caption(f"残り {quota.credits} クレジット")

    if gen_disabled:
        st.warning("クレジットがありません。")

    return None


def _regenerate_profile(user_id: int, user_login: str, repo_limit: int) -> None:
    """プロファイルを再生成."""
    consume_credit(user_id)
    invalidate_repos_cache(user_id)
    invalidate_profile_cache(user_id)
    st.session_state.pop("profile", None)
    st.session_state.pop(JOB_RESULTS, None)

    with st.spinner("プロファイルを再生成中..."):
        repos = analyze_github_profile(user_login, repo_limit)
        if repos:
            save_repos_cache(user_id, repos)
            profile = generate_profile(repos)
            save_profile_cache(
                user_id=user_id,
                github_login=user_login,
                profile_data=profile,
                repo_count=len(repos),
            )
            st.session_state["profile"] = profile
        else:
            st.error("リポジトリが見つかりませんでした")
        st.rerun()


def _generate_profile(user_id: int, user_login: str, repo_limit: int) -> None:
    """プロファイルを新規生成."""
    consume_credit(user_id)

    with st.spinner("GitHubプロファイルを分析中..."):
        repos = analyze_github_profile(user_login, repo_limit)
        if repos:
            save_repos_cache(user_id, repos)
            profile = generate_profile(repos)
            save_profile_cache(
                user_id=user_id,
                github_login=user_login,
                profile_data=profile,
                repo_count=len(repos),
            )
            st.session_state["profile"] = profile
        else:
            st.error("リポジトリが見つかりませんでした")
        st.rerun()
