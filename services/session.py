"""Session persistence service using Firestore and Cookies."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import extra_streamlit_components as stx
import streamlit as st
from google.cloud.firestore_v1 import DocumentSnapshot

from services.auth import GitHubUser
from services.cache import get_firestore_client
from services.const import (
    MAX_COOKIE_RETRIES,
    SESSION_COOKIE_NAME,
    SESSION_TTL_DAYS,
)

COOKIE_RETRY_KEY = "_cookie_retry_count"


def get_cookie_manager() -> stx.CookieManager:
    """CookieManagerインスタンスを取得."""
    return stx.CookieManager()


def get_session_cookie(cookie_manager: stx.CookieManager) -> str | None:
    """Cookieからsession_idを取得（retry付き）.

    CookieManagerは非同期で動作するため、初回呼び出しでNoneが返る可能性あり。
    st.rerun()で再実行してコンポーネントマウントを待つ。

    Args:
        cookie_manager: CookieManagerインスタンス

    Returns:
        session_id または None（取得失敗 or 未設定）
    """
    session_id = cookie_manager.get(cookie=SESSION_COOKIE_NAME)

    if session_id is not None:
        # 取得成功 → retry countをリセット
        st.session_state.pop(COOKIE_RETRY_KEY, None)
        return session_id

    # Noneの場合、retryが必要か判定
    retry_count = st.session_state.get(COOKIE_RETRY_KEY, 0)

    if retry_count < MAX_COOKIE_RETRIES:
        # retry回数をインクリメントしてrerun
        st.session_state[COOKIE_RETRY_KEY] = retry_count + 1
        st.rerun()

    # retry上限到達 → Noneを返す（Cookieなしとして扱う）
    st.session_state.pop(COOKIE_RETRY_KEY, None)
    return None


def set_session_cookie(cookie_manager: stx.CookieManager, session_id: str) -> None:
    """Cookieにsession_idを設定（7日間有効）.

    Args:
        cookie_manager: CookieManagerインスタンス
        session_id: セッションID
    """
    expires_at = datetime.now() + timedelta(days=SESSION_TTL_DAYS)
    cookie_manager.set(
        cookie=SESSION_COOKIE_NAME,
        val=session_id,
        expires_at=expires_at,
    )


def delete_session_cookie(cookie_manager: stx.CookieManager) -> None:
    """Cookieからsession_idを削除.

    Args:
        cookie_manager: CookieManagerインスタンス
    """
    cookie_manager.delete(cookie=SESSION_COOKIE_NAME)


def get_firestore_session(session_id: str) -> dict[str, Any] | None:
    """Firestoreからセッションを取得.

    Args:
        session_id: セッションID

    Returns:
        セッションデータ（有効期限内）または None
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("sessions").document(session_id)
        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]

        if not doc.exists:
            return None

        data = doc.to_dict()
        if data is None:
            return None

        # TTLチェック（last_accessed_atから7日以上経過していたら無効）
        last_accessed = data.get("last_accessed_at")
        if last_accessed:
            expiry = last_accessed + timedelta(days=SESSION_TTL_DAYS)
            if datetime.now(UTC) > expiry:
                # 期限切れ → セッション削除
                delete_firestore_session(session_id)
                return None

        return data
    except Exception:
        return None


def save_firestore_session(
    session_id: str,
    user: GitHubUser,
    access_token: str,
) -> None:
    """Firestoreにセッションを保存.

    Args:
        session_id: セッションID
        user: GitHubUser
        access_token: GitHub access token
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("sessions").document(session_id)

        now = datetime.now(UTC)

        doc_ref.set(
            {
                "session_id": session_id,
                "user_id": user.id,
                "access_token": access_token,
                "user_data": {
                    "id": user.id,
                    "login": user.login,
                    "name": user.name,
                    "email": user.email,
                    "avatar_url": user.avatar_url,
                },
                "created_at": now,
                "last_accessed_at": now,
            }
        )
    except Exception:
        # 保存失敗は無視（セッション永続化は必須ではない）
        pass


def update_session_last_accessed(session_id: str) -> None:
    """セッションのlast_accessed_atを更新.

    Args:
        session_id: セッションID
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("sessions").document(session_id)
        doc_ref.update({"last_accessed_at": datetime.now(UTC)})
    except Exception:
        pass


def delete_firestore_session(session_id: str) -> None:
    """Firestoreからセッションを削除.

    Args:
        session_id: セッションID
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("sessions").document(session_id)
        doc_ref.delete()
    except Exception:
        pass


def generate_session_id() -> str:
    """新しいセッションIDを生成.

    Returns:
        UUID v4形式のセッションID
    """
    return str(uuid.uuid4())


def restore_session_from_dict(data: dict[str, Any]) -> tuple[GitHubUser, str]:
    """Firestoreのセッションデータからユーザー情報を復元.

    Args:
        data: Firestoreから取得したセッションデータ

    Returns:
        (GitHubUser, access_token)
    """
    user_data = data["user_data"]
    user = GitHubUser(
        id=user_data["id"],
        login=user_data["login"],
        name=user_data.get("name"),
        email=user_data.get("email"),
        avatar_url=user_data["avatar_url"],
    )
    return user, data["access_token"]
