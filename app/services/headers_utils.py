"""HTTPヘッダー処理ユーティリティ."""

import logging

import streamlit as st

logger = logging.getLogger(__name__)


def get_header(name: str, default: str = "") -> str:
    """HTTPヘッダーを安全に取得.

    Args:
        name: ヘッダー名（例: "Cookie", "Host", "User-Agent"）
        default: ヘッダーが取得できない場合のデフォルト値

    Returns:
        ヘッダーの値、またはデフォルト値

    Examples:
        >>> get_header("Cookie")
        'session=abc123; user=john'
        >>> get_header("Host")
        'example.com'
        >>> get_header("Missing-Header", "fallback")
        'fallback'
    """
    try:
        return st.context.headers.get(name, default)
    except Exception:
        logger.warning(
            f"Failed to read {name} header from st.context.headers",
            exc_info=True,
        )
        return default
