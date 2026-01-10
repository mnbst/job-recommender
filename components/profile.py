"""Profile display component."""

import streamlit as st

from services.cache import (
    get_cached_profile,
    invalidate_profile_cache,
    invalidate_repos_cache,
    save_profile_cache,
    save_repos_cache,
)
from services.github import (
    RepoMetadata,
    analyze_selected_repos,
    get_repos_metadata,
)
from services.profile import generate_profile
from services.quota import QuotaStatus, consume_credit
from services.session_keys import JOB_RESULTS

# セッションキー
REPO_METADATA_KEY = "repo_metadata_list"
SELECTED_REPOS_KEY = "selected_repos"


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


def _format_repo_label(repo: RepoMetadata) -> str:
    """リポジトリのラベルをフォーマット."""
    lang = repo.language or "N/A"
    fork_badge = " [Fork]" if repo.is_fork else ""
    return f"{repo.name} ({lang}, {repo.stars} stars){fork_badge}"


def _render_repo_selector(
    user_login: str,
    repo_limit: int,
    key_prefix: str = "",
) -> list[str] | None:
    """リポジトリ選択UIを描画.

    Returns:
        選択されたリポジトリ名のリスト、または未選択/読み込み前はNone
    """
    metadata_key = f"{key_prefix}{REPO_METADATA_KEY}"
    selected_key = f"{key_prefix}{SELECTED_REPOS_KEY}"

    # リポジトリ一覧を読み込み
    if metadata_key not in st.session_state:
        if st.button("リポジトリを読み込む", key=f"{key_prefix}load_repos"):
            with st.spinner("リポジトリ一覧を取得中..."):
                repos_meta = get_repos_metadata(user_login, limit=repo_limit)
                st.session_state[metadata_key] = repos_meta
                st.rerun()
        return None

    repos_meta: list[RepoMetadata] = st.session_state[metadata_key]

    if not repos_meta:
        st.warning("リポジトリが見つかりませんでした")
        return None

    # リポジトリ選択UI
    st.caption(f"{len(repos_meta)} 件のリポジトリが見つかりました")

    # オプション作成
    options = {_format_repo_label(r): r.name for r in repos_meta}

    # Fork以外をデフォルト選択
    default_labels = [
        _format_repo_label(r) for r in repos_meta if not r.is_fork
    ][:10]

    selected_labels = st.multiselect(
        "分析対象のリポジトリを選択",
        options=list(options.keys()),
        default=default_labels,
        key=selected_key,
        help="プロファイル生成に使用するリポジトリを選択してください",
    )

    if not selected_labels:
        st.warning("少なくとも1つのリポジトリを選択してください")
        return None

    return [options[label] for label in selected_labels]


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

        # 再生成UI
        with st.expander("プロファイルを再生成"):
            if not quota.can_use:
                st.warning("クレジットがありません。")
                return cached_profile

            st.caption(f"残り {quota.credits} クレジット")

            selected_repos = _render_repo_selector(
                user_login, repo_limit * 3, key_prefix="regen_"
            )

            if selected_repos:
                if st.button(
                    f"{len(selected_repos)} 件のリポジトリでプロファイル再生成",
                    type="primary",
                    key="regen_profile_btn",
                ):
                    _regenerate_profile(user_id, user_login, selected_repos)

        return cached_profile

    # プロファイル未生成
    st.info("プロファイルを生成して、あなたに最適な求人を見つけましょう。")

    if not quota.can_use:
        st.warning("クレジットがありません。")
        return None

    st.caption(f"残り {quota.credits} クレジット")

    selected_repos = _render_repo_selector(user_login, repo_limit * 3)

    if selected_repos:
        if st.button(
            f"{len(selected_repos)} 件のリポジトリでプロファイル生成",
            type="primary",
        ):
            _generate_profile(user_id, user_login, selected_repos)

    return None


def _regenerate_profile(user_id: int, user_login: str, repo_names: list[str]) -> None:
    """プロファイルを再生成."""
    consume_credit(user_id)
    invalidate_repos_cache(user_id)
    invalidate_profile_cache(user_id)
    st.session_state.pop("profile", None)
    st.session_state.pop(JOB_RESULTS, None)
    # セレクター状態をクリア
    st.session_state.pop(f"regen_{REPO_METADATA_KEY}", None)
    st.session_state.pop(f"regen_{SELECTED_REPOS_KEY}", None)

    with st.spinner("プロファイルを再生成中..."):
        repos = analyze_selected_repos(user_login, repo_names)
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
            st.error("リポジトリの分析に失敗しました")
        st.rerun()


def _generate_profile(user_id: int, user_login: str, repo_names: list[str]) -> None:
    """プロファイルを新規生成."""
    consume_credit(user_id)
    # セレクター状態をクリア
    st.session_state.pop(REPO_METADATA_KEY, None)
    st.session_state.pop(SELECTED_REPOS_KEY, None)

    with st.spinner("GitHubプロファイルを分析中..."):
        repos = analyze_selected_repos(user_login, repo_names)
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
            st.error("リポジトリの分析に失敗しました")
        st.rerun()
