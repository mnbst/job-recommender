"""Session persistence service using Firestore and Cookies."""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from google.cloud.firestore_v1 import DocumentSnapshot

from services.cache import get_firestore_client
from services.components.cookie_manager import CookieManager
from services.components.cookie_manager import get_cookie_manager as get_cookie_manager
from services.const import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_DAYS,
)
from services.logging_config import log_structured
from services.models import GitHubUser

logger = logging.getLogger(__name__)


def get_session_cookie(cookie_manager: CookieManager) -> str | None:
    """Cookieからsession_idを取得.

    Args:
        cookie_manager: CookieManagerインスタンス

    Returns:
        session_id または None（未設定の場合）
    """
    return cookie_manager.get(cookie=SESSION_COOKIE_NAME)


def set_session_cookie(cookie_manager: CookieManager, session_id: str) -> None:
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


def delete_session_cookie(cookie_manager: CookieManager) -> None:
    """Cookieからsession_idを削除.

    Args:
        cookie_manager: CookieManagerインスタンス
    """
    if cookie_manager.get(cookie=SESSION_COOKIE_NAME) is not None:
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
        log_structured(
            logger,
            "Failed to fetch session",
            level=logging.ERROR,
            exc_info=True,
            session_id=session_id,
        )
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
        log_structured(
            logger,
            "Failed to save session",
            level=logging.ERROR,
            exc_info=True,
            session_id=session_id,
        )


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
        log_structured(
            logger,
            "Failed to update session last_accessed_at",
            level=logging.ERROR,
            exc_info=True,
            session_id=session_id,
        )


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
        log_structured(
            logger,
            "Failed to delete session",
            level=logging.ERROR,
            exc_info=True,
            session_id=session_id,
        )


def delete_user_sessions(user_id: int) -> int:
    """指定ユーザーの全セッションを削除.

    Args:
        user_id: GitHubユーザーID

    Returns:
        削除したセッション数
    """
    try:
        db = get_firestore_client()
        sessions_ref = db.collection("sessions")
        query = sessions_ref.where("user_id", "==", user_id)
        docs = query.stream()

        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1

        if deleted_count > 0:
            log_structured(
                logger,
                "Deleted existing user sessions",
                level=logging.INFO,
                user_id=user_id,
                deleted_count=deleted_count,
            )

        return deleted_count
    except Exception:
        log_structured(
            logger,
            "Failed to delete user sessions",
            level=logging.ERROR,
            exc_info=True,
            user_id=user_id,
        )
        return 0


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
