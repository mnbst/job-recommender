"""Streamlit components.v2 APIを使用したリダイレクトコンポーネント."""

from pathlib import Path
from typing import Any

import streamlit.components.v2 as components

_JS_PATH = Path(__file__).parent / "redirect.js"
_JS_CODE = _JS_PATH.read_text(encoding="utf-8")

_redirect_component = components.component(
    name="redirect",
    js=_JS_CODE,
)


def redirect(url: str, *, delete_cookie: bool = False, key: str = "redirect") -> Any:
    """指定URLへ同一タブでリダイレクト.

    Args:
        url: 遷移先URL
        delete_cookie: リダイレクト前にjob_recommender_session Cookieを削除するか
        key: コンポーネントの一意キー
    """
    return _redirect_component(
        data={"url": url, "delete_cookie": delete_cookie},
        key=key,
        default=None,
    )
