"""共通のログ設定とヘルパー."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import MutableMapping
from typing import Any

try:
    from google.cloud import logging as cloud_logging
except ModuleNotFoundError:
    cloud_logging = None

# グローバル変数でロギング初期化状態を管理
_logging_initialized = False


def is_cloud_run() -> bool:
    """Cloud Run環境のときにTrueを返す."""
    return bool(os.environ.get("K_SERVICE"))


def setup_logging() -> None:
    """ローカル/Cloud Run環境向けのログ設定."""
    global _logging_initialized

    # 既に初期化済みの場合はスキップ（重複ハンドラー防止）
    if _logging_initialized:
        return

    if is_cloud_run():
        if cloud_logging is None:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            logging.getLogger(__name__).warning(
                "google.cloud.logging is not available; falling back to basic logging."
            )
            _logging_initialized = True
            return

        client = cloud_logging.Client()
        client.setup_logging()
        _logging_initialized = True
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    _logging_initialized = True


def _get_user_context() -> tuple[str | None, str | None]:
    """session_stateからuser_id, loginを取得（循環importを避けるため遅延import）."""
    try:
        import streamlit as st

        from app.services.session_keys import USER

        user = st.session_state.get(USER)
        if user:
            return str(user.id), user.login
        return None, None
    except (ImportError, AttributeError, RuntimeError):
        return None, None


class UserContextAdapter(logging.LoggerAdapter):
    """user_id, loginを自動的に含めるLoggerAdapter."""

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """ログメッセージにuser_id, loginを追加."""
        user_id, login = _get_user_context()
        extra = kwargs.get("extra", {})

        if is_cloud_run():
            # Cloud Loggingの構造化ログ用
            json_fields = extra.get("json_fields", {})
            if user_id:
                json_fields["user_id"] = user_id
            if login:
                json_fields["login"] = login
            extra["json_fields"] = json_fields
        else:
            # ローカル環境用
            if login:
                msg = f"[{login}] {msg}"
            elif user_id:
                msg = f"[user_id={user_id}] {msg}"

        kwargs["extra"] = extra
        return msg, kwargs  # type: ignore


def get_logger(name: str) -> logging.LoggerAdapter:
    """user_id付きロガーを取得."""
    base_logger = logging.getLogger(name)
    return UserContextAdapter(base_logger, {})


def log_structured(
    logger: logging.Logger,
    message: str,
    *,
    level: int = logging.INFO,
    exc_info: bool | BaseException | None = None,
    **fields: Any,
) -> None:
    """Cloud Runでは構造化ログ、ローカルでは可読なテキストで出力."""
    if is_cloud_run():
        extra = {"json_fields": fields} if fields else None
        logger.log(level, message, extra=extra, exc_info=exc_info)
        return

    if fields:
        message = f"{message}: {json.dumps(fields, ensure_ascii=False)}"
    logger.log(level, message, exc_info=exc_info)
