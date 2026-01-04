"""Firestore cache service for developer profiles and repositories."""

import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import streamlit as st
from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentSnapshot

from services.const import CACHE_TTL_DAYS
from services.github import FileContent, RepoInfo
from services.session_keys import PROFILE, USER_SETTINGS


def get_firestore_client() -> firestore.Client:
    """Firestoreクライアントを取得."""
    project_id = os.getenv("GCP_PROJECT_ID")
    return firestore.Client(project=project_id, database="(default)")


def _fetch_cached_profile(user_id: int, repo_count: int) -> dict[str, Any] | None:
    """Firestoreからキャッシュされたプロファイルを取得（内部用）."""
    try:
        db = get_firestore_client()
        doc_ref = db.collection("profiles").document(str(user_id))
        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]

        if not doc.exists:
            return None

        data = doc.to_dict()
        if data is None:
            return None

        # リポジトリ数が異なる場合はキャッシュ無効
        repo_count_cached = data.get("repo_count")
        if repo_count_cached and repo_count_cached > repo_count:
            return None

        # TTLチェック
        updated_at = data.get("updated_at")
        if updated_at:
            expiry = updated_at + timedelta(days=CACHE_TTL_DAYS)
            if datetime.now(UTC) > expiry:
                return None

        return data.get("profile_data")
    except Exception:
        return None


def get_cached_profile(user_id: int, repo_count: int) -> dict[str, Any] | None:
    """キャッシュされたプロファイルを取得（session_stateキャッシュ付き）.

    Args:
        user_id: GitHubUser.id
        repo_count: 分析するリポジトリ数

    Returns:
        キャッシュが有効ならprofile_data、それ以外はNone
    """
    # session_stateにキャッシュがあれば返す
    if PROFILE in st.session_state:
        return st.session_state[PROFILE]

    # Firestoreから取得してキャッシュ
    profile = _fetch_cached_profile(user_id, repo_count)
    if profile is not None:
        st.session_state[PROFILE] = profile
    return profile


def invalidate_profile_session_cache() -> None:
    """プロファイルのsession_stateキャッシュを無効化."""
    st.session_state.pop(PROFILE, None)


def save_profile_cache(
    user_id: int,
    github_login: str,
    profile_data: dict[str, Any],
    repo_count: int,
) -> None:
    """プロファイルをキャッシュに保存.

    Args:
        user_id: GitHubUser.id
        github_login: GitHubUser.login
        profile_data: generate_profile() の戻り値
        repo_count: 分析したリポジトリ数
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("profiles").document(str(user_id))

        now = datetime.now(UTC)

        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]
        created_at = now
        if doc.exists:
            existing_data = doc.to_dict()
            if existing_data and existing_data.get("created_at"):
                created_at = existing_data["created_at"]

        doc_ref.set(
            {
                "user_id": user_id,
                "github_login": github_login,
                "profile_data": profile_data,
                "repo_count": repo_count,
                "created_at": created_at,
                "updated_at": now,
                "version": 1,
            }
        )
        # session_stateキャッシュを更新
        st.session_state[PROFILE] = profile_data
    except Exception:
        pass


def invalidate_profile_cache(user_id: int) -> None:
    """キャッシュを明示的に無効化（削除）."""
    try:
        db = get_firestore_client()
        doc_ref = db.collection("profiles").document(str(user_id))
        doc_ref.delete()
        invalidate_profile_session_cache()
    except Exception:
        pass


def get_cached_repos(user_id: int, repo_count: int) -> list[RepoInfo] | None:
    """キャッシュされたリポジトリ情報を取得.

    Args:
        user_id: GitHubUser.id
        repo_count: 取得するリポジトリ数

    Returns:
        キャッシュが有効ならRepoInfoリスト、それ以外はNone
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("repos").document(str(user_id))
        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]

        if not doc.exists:
            return None

        data = doc.to_dict()
        if data is None:
            return None

        # リポジトリ数が異なる場合はキャッシュ無効
        cached_repo_count = data.get("repo_count")
        if cached_repo_count and cached_repo_count > repo_count:
            return None

        # TTLチェック
        updated_at = data.get("updated_at")
        if updated_at:
            expiry = updated_at + timedelta(days=CACHE_TTL_DAYS)
            if datetime.now(UTC) > expiry:
                return None

        # dictからRepoInfoに復元
        repos_data = data.get("repos", [])
        return [_dict_to_repo_info(r) for r in repos_data]
    except Exception:
        return None


def save_repos_cache(
    user_id: int,
    repos: list[RepoInfo],
) -> None:
    """リポジトリ情報をキャッシュに保存.

    Args:
        user_id: GitHubUser.id
        repos: RepoInfoリスト
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("repos").document(str(user_id))

        now = datetime.now(UTC)

        doc_ref.set(
            {
                "user_id": user_id,
                "repos": [asdict(r) for r in repos],
                "repo_count": len(repos),
                "updated_at": now,
            }
        )
    except Exception:
        pass


def invalidate_repos_cache(user_id: int) -> None:
    """リポジトリキャッシュを無効化."""
    try:
        db = get_firestore_client()
        doc_ref = db.collection("repos").document(str(user_id))
        doc_ref.delete()
    except Exception:
        pass


def _dict_to_repo_info(data: dict[str, Any]) -> RepoInfo:
    """dictからRepoInfoを復元."""
    return RepoInfo(
        name=data["name"],
        description=data.get("description"),
        language=data.get("language"),
        languages=data.get("languages", {}),
        topics=data.get("topics", []),
        readme=data.get("readme"),
        stars=data.get("stars", 0),
        forks=data.get("forks", 0),
        updated_at=data.get("updated_at", ""),
        is_fork=data.get("is_fork", False),
        file_structure=data.get("file_structure", []),
        dependency_files=[
            FileContent(path=f["path"], content=f["content"])
            for f in data.get("dependency_files", [])
        ],
        main_files=[
            FileContent(path=f["path"], content=f["content"])
            for f in data.get("main_files", [])
        ],
        config_files=data.get("config_files", []),
    )


# ============================================
# User Settings Cache
# ============================================
@dataclass
class UserSettings:
    """ユーザー設定."""

    repo_limit: int = 10
    job_location: str = "東京"
    salary_range: str = "指定なし"
    work_style: list[str] = field(default_factory=list)
    job_type: list[str] = field(default_factory=list)
    employment_type: list[str] = field(default_factory=list)
    other_preferences: str = ""
    plan: str = "free"  # "free" | "premium"


def _fetch_user_settings(user_id: int) -> UserSettings:
    """Firestoreからユーザー設定を取得（内部用）."""
    try:
        db = get_firestore_client()
        doc_ref = db.collection("settings").document(str(user_id))
        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]

        if not doc.exists:
            return UserSettings()

        data = doc.to_dict()
        if data is None:
            return UserSettings()

        return UserSettings(
            repo_limit=data.get("repo_limit", 10),
            job_location=data.get("job_location", "東京"),
            salary_range=data.get("salary_range", "指定なし"),
            work_style=data.get("work_style", []),
            job_type=data.get("job_type", []),
            employment_type=data.get("employment_type", []),
            other_preferences=data.get("other_preferences", ""),
            plan=data.get("plan", "free"),
        )
    except Exception:
        return UserSettings()


def get_user_settings(user_id: int) -> UserSettings:
    """ユーザー設定を取得（session_stateキャッシュ付き）.

    Args:
        user_id: GitHubUser.id

    Returns:
        UserSettings（存在しない場合はデフォルト値）
    """
    # session_stateにキャッシュがあれば返す
    if USER_SETTINGS in st.session_state:
        return st.session_state[USER_SETTINGS]

    # Firestoreから取得してキャッシュ
    settings = _fetch_user_settings(user_id)
    st.session_state[USER_SETTINGS] = settings
    return settings


def invalidate_settings_session_cache() -> None:
    """ユーザー設定のsession_stateキャッシュを無効化."""
    st.session_state.pop(USER_SETTINGS, None)


def save_user_settings(user_id: int, settings: UserSettings) -> None:
    """ユーザー設定を保存.

    Args:
        user_id: GitHubUser.id
        settings: UserSettings
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("settings").document(str(user_id))

        doc_ref.set(
            {
                "user_id": user_id,
                "repo_limit": settings.repo_limit,
                "job_location": settings.job_location,
                "salary_range": settings.salary_range,
                "work_style": settings.work_style,
                "job_type": settings.job_type,
                "employment_type": settings.employment_type,
                "other_preferences": settings.other_preferences,
                "plan": settings.plan,
                "updated_at": datetime.now(UTC),
            }
        )
        # session_stateキャッシュを更新
        st.session_state[USER_SETTINGS] = settings
    except Exception:
        pass
