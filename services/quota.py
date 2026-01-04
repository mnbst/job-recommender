"""Freemium quota management service（クレジット制）."""

from dataclasses import dataclass
from datetime import UTC, datetime

import streamlit as st
from google.cloud.firestore_v1 import DocumentSnapshot

from services.cache import get_firestore_client
from services.const import (
    FREE_PLAN_INITIAL_PROFILE_CREDITS,
    FREE_PLAN_INITIAL_SEARCH_CREDITS,
)
from services.session_keys import QUOTA_STATUS


@dataclass
class QuotaStatus:
    """ユーザーのクォータ状態."""

    profile_credits: int  # 残りプロファイル生成クレジット
    search_credits: int  # 残り求人検索クレジット
    can_generate_profile: bool
    can_search: bool


def _get_credits_data(user_id: int) -> dict | None:
    """クレジットデータを取得."""
    try:
        db = get_firestore_client()
        doc_ref = db.collection("credits").document(str(user_id))
        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]

        if not doc.exists:
            return None

        return doc.to_dict()
    except Exception:
        return None


def _init_credits(user_id: int) -> dict:
    """クレジットを初期化."""
    try:
        db = get_firestore_client()
        doc_ref = db.collection("credits").document(str(user_id))
        now = datetime.now(UTC)

        data = {
            "user_id": user_id,
            "profile_credits": FREE_PLAN_INITIAL_PROFILE_CREDITS,
            "search_credits": FREE_PLAN_INITIAL_SEARCH_CREDITS,
            "created_at": now,
            "updated_at": now,
        }
        doc_ref.set(data)
        return data
    except Exception:
        return {
            "profile_credits": FREE_PLAN_INITIAL_PROFILE_CREDITS,
            "search_credits": FREE_PLAN_INITIAL_SEARCH_CREDITS,
        }


def _fetch_quota_status(user_id: int) -> QuotaStatus:
    """Firestoreからクォータ状態を取得（内部用）."""
    credits_data = _get_credits_data(user_id)

    if credits_data is None:
        # 初回アクセス → クレジット初期化
        credits_data = _init_credits(user_id)

    profile_credits = credits_data.get(
        "profile_credits", FREE_PLAN_INITIAL_PROFILE_CREDITS
    )
    search_credits = credits_data.get(
        "search_credits", FREE_PLAN_INITIAL_SEARCH_CREDITS
    )

    return QuotaStatus(
        profile_credits=profile_credits,
        search_credits=search_credits,
        can_generate_profile=profile_credits > 0,
        can_search=search_credits > 0,
    )


def get_quota_status(user_id: int) -> QuotaStatus:
    """ユーザーのクォータ状態を取得（session_stateキャッシュ付き）.

    Args:
        user_id: GitHubUser.id

    Returns:
        QuotaStatus
    """
    # session_stateにキャッシュがあれば返す
    if QUOTA_STATUS in st.session_state:
        return st.session_state[QUOTA_STATUS]

    # Firestoreから取得してキャッシュ
    quota = _fetch_quota_status(user_id)
    st.session_state[QUOTA_STATUS] = quota
    return quota


def invalidate_quota_cache() -> None:
    """クォータキャッシュを無効化."""
    st.session_state.pop(QUOTA_STATUS, None)


def consume_profile_credit(user_id: int) -> bool:
    """プロファイル生成クレジットを1消費.

    Args:
        user_id: GitHubUser.id

    Returns:
        成功した場合True
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("credits").document(str(user_id))
        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]
        now = datetime.now(UTC)

        if not doc.exists:
            # 初期化してから消費
            _init_credits(user_id)
            doc = doc_ref.get()  # type: ignore[assignment]

        data = doc.to_dict()
        if data is None:
            return False

        current_credits = data.get("profile_credits", 0)
        if current_credits <= 0:
            return False

        doc_ref.update(
            {
                "profile_credits": current_credits - 1,
                "updated_at": now,
            }
        )
        invalidate_quota_cache()
        return True
    except Exception:
        return False


def consume_search_credit(user_id: int) -> bool:
    """求人検索クレジットを1消費.

    Args:
        user_id: GitHubUser.id

    Returns:
        成功した場合True
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("credits").document(str(user_id))
        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]
        now = datetime.now(UTC)

        if not doc.exists:
            # 初期化してから消費
            _init_credits(user_id)
            doc = doc_ref.get()  # type: ignore[assignment]

        data = doc.to_dict()
        if data is None:
            return False

        current_credits = data.get("search_credits", 0)
        if current_credits <= 0:
            return False

        doc_ref.update(
            {
                "search_credits": current_credits - 1,
                "updated_at": now,
            }
        )
        invalidate_quota_cache()
        return True
    except Exception:
        return False


def add_credits(
    user_id: int,
    profile_credits: int = 0,
    search_credits: int = 0,
) -> bool:
    """クレジットを追加（課金時などに使用）.

    Args:
        user_id: GitHubUser.id
        profile_credits: 追加するプロファイルクレジット
        search_credits: 追加する検索クレジット

    Returns:
        成功した場合True
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("credits").document(str(user_id))
        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]
        now = datetime.now(UTC)

        if not doc.exists:
            _init_credits(user_id)
            doc = doc_ref.get()  # type: ignore[assignment]

        data = doc.to_dict()
        if data is None:
            return False

        current_profile = data.get("profile_credits", 0)
        current_search = data.get("search_credits", 0)

        doc_ref.update(
            {
                "profile_credits": current_profile + profile_credits,
                "search_credits": current_search + search_credits,
                "updated_at": now,
            }
        )
        invalidate_quota_cache()
        return True
    except Exception:
        return False
