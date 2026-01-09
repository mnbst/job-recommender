"""Freemium quota management service（共通クレジット制）."""

from datetime import UTC, datetime

import streamlit as st
from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from pydantic import BaseModel

from services.cache import get_firestore_client
from services.const import FREE_PLAN_INITIAL_CREDITS
from services.session_keys import QUOTA_STATUS


class QuotaStatus(BaseModel):
    """ユーザーのクォータ状態."""

    credits: int  # 残りクレジット
    can_use: bool  # クレジットが残っているか


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
    """クレジットを初期化（既存の場合はスキップ）."""
    db = get_firestore_client()
    doc_ref = db.collection("credits").document(str(user_id))
    now = datetime.now(UTC)

    data = {
        "user_id": user_id,
        "credits": FREE_PLAN_INITIAL_CREDITS,
        "created_at": now,
        "updated_at": now,
    }

    try:
        # create()は既存の場合AlreadyExistsを発生させる（競合回避）
        doc_ref.create(data)
        return data
    except AlreadyExists:
        # 既に存在する場合は現在の値を返す
        doc: DocumentSnapshot = doc_ref.get()  # type: ignore[assignment]
        return doc.to_dict() or data
    except Exception:
        return {"credits": FREE_PLAN_INITIAL_CREDITS}


def _fetch_quota_status(user_id: int) -> QuotaStatus:
    """Firestoreからクォータ状態を取得（内部用）."""
    credits_data = _get_credits_data(user_id)

    if credits_data is None:
        # 初回アクセス → クレジット初期化
        credits_data = _init_credits(user_id)

    credits = credits_data.get("credits", FREE_PLAN_INITIAL_CREDITS)

    return QuotaStatus(
        credits=credits,
        can_use=credits > 0,
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


def consume_credit(user_id: int) -> bool:
    """クレジットを1消費（トランザクションで競合回避）.

    Args:
        user_id: GitHubUser.id

    Returns:
        成功した場合True
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("credits").document(str(user_id))
        now = datetime.now(UTC)

        @firestore.transactional
        def consume_in_transaction(
            transaction: firestore.Transaction,
        ) -> int | None:
            doc: DocumentSnapshot = doc_ref.get(transaction=transaction)  # type: ignore[assignment]

            if not doc.exists:
                # トランザクション内で初期化
                transaction.set(
                    doc_ref,
                    {
                        "user_id": user_id,
                        "credits": FREE_PLAN_INITIAL_CREDITS - 1,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                return FREE_PLAN_INITIAL_CREDITS - 1

            data = doc.to_dict()
            if data is None:
                return None

            current_credits = data.get("credits", 0)
            if current_credits <= 0:
                return None

            new_credits = current_credits - 1
            transaction.update(
                doc_ref,
                {
                    "credits": new_credits,
                    "updated_at": now,
                },
            )
            return new_credits

        transaction = db.transaction()
        new_credits = consume_in_transaction(transaction)

        if new_credits is None:
            return False

        # キャッシュを新しい値で即座に更新
        st.session_state[QUOTA_STATUS] = QuotaStatus(
            credits=new_credits,
            can_use=new_credits > 0,
        )
        return True
    except Exception:
        return False


def add_credits(user_id: int, amount: int) -> bool:
    """クレジットを追加（トランザクションで競合回避）.

    Args:
        user_id: GitHubUser.id
        amount: 追加するクレジット数

    Returns:
        成功した場合True
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("credits").document(str(user_id))
        now = datetime.now(UTC)

        @firestore.transactional
        def add_in_transaction(
            transaction: firestore.Transaction,
        ) -> int | None:
            doc: DocumentSnapshot = doc_ref.get(transaction=transaction)  # type: ignore[assignment]

            if not doc.exists:
                # トランザクション内で初期化 + 追加
                new_credits = FREE_PLAN_INITIAL_CREDITS + amount
                transaction.set(
                    doc_ref,
                    {
                        "user_id": user_id,
                        "credits": new_credits,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                return new_credits

            data = doc.to_dict()
            if data is None:
                return None

            current_credits = data.get("credits", 0)
            new_credits = current_credits + amount
            transaction.update(
                doc_ref,
                {
                    "credits": new_credits,
                    "updated_at": now,
                },
            )
            return new_credits

        transaction = db.transaction()
        new_credits = add_in_transaction(transaction)

        if new_credits is None:
            return False

        # キャッシュを新しい値で即座に更新
        st.session_state[QUOTA_STATUS] = QuotaStatus(
            credits=new_credits,
            can_use=new_credits > 0,
        )
        return True
    except Exception:
        return False
