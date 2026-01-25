"""Streamlit components.v2 APIを使用したCookie Managerコンポーネント."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v2 as components

from app.services.cookie_utils import parse_cookie_header
from app.services.headers_utils import get_header

# JavaScriptファイルを読み込み
_JS_PATH = Path(__file__).parent / "cookie_manager.js"
_JS_CODE = _JS_PATH.read_text(encoding="utf-8")

# コンポーネントを登録
_cookie_component = components.component(
    name="cookie_manager",
    js=_JS_CODE,
)

# session_stateキャッシュ用キー
_COOKIES_CACHE_KEY = "_cookie_manager_cache"

logger = logging.getLogger(__name__)


class CookieManager:
    """Streamlit components.v2を使用したCookie Manager.

    extra_streamlit_components.CookieManagerの代替実装。
    universal-cookieライブラリではなくdocument.cookieを直接操作する。

    特徴:
        - iframe不要（v2 API）でパフォーマンス向上
        - 既存APIとの互換性を維持
        - 依存パッケージ削減
        - session_stateキャッシュによるコールドスタート対策
    """

    def __init__(self, key: str = "cookie_manager") -> None:
        """CookieManagerを初期化.

        Args:
            key: コンポーネントインスタンスの一意キー
        """
        self._key = key
        self._cookies: dict[str, str] = {}
        self._result: Any = None
        self._initialized = False
        # session_stateからキャッシュ復元（コールドスタート対策）
        cached = st.session_state.get(_COOKIES_CACHE_KEY)
        if isinstance(cached, dict):
            self._update_cookies_cache(cached)

    @classmethod
    def get_from_headers(cls, cookie: str) -> str | None:
        """HTTPヘッダーからCookie値を取得（サーバーサイド、JS不要）."""
        if not cookie:
            return None
        try:
            cookie_header = get_header("Cookie")
            cookies = parse_cookie_header(cookie_header)
            return cookies.get(cookie)
        except Exception:
            logger.warning("Failed to read Cookie from HTTP headers", exc_info=True)
            return None

    @classmethod
    def get_all_from_headers(cls) -> dict[str, str]:
        """HTTPヘッダーから全Cookieを取得（サーバーサイド、JS不要）."""
        try:
            cookie_header = get_header("Cookie")
            cookies = parse_cookie_header(cookie_header)
            return cookies.copy()
        except Exception:
            logger.warning("Failed to read Cookie from HTTP headers", exc_info=True)
            return {}

    def _on_cookies_change(self, cookies: dict[str, str] | None = None) -> None:
        """cookies状態変更時のコールバック."""
        if isinstance(cookies, dict):
            self._update_cookies_cache(cookies)

    def _on_result_change(self, result: Any = None) -> None:
        """result状態変更時のコールバック."""
        self._result = result

    def _render(
        self,
        action: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """コンポーネントをレンダリングして結果を取得.

        Args:
            action: 実行するアクション（get, set, delete, get_all）
            **kwargs: アクションの追加パラメータ

        Returns:
            cookiesとresultを含むコンポーネント状態
        """
        data = {"action": action, **kwargs} if action else {}

        result = _cookie_component(
            data=data,
            key=f"{self._key}_{action or 'init'}",
            default={"cookies": {}, "result": None},
            on_cookies_change=self._on_cookies_change,
            on_result_change=self._on_result_change,
        )

        # v2 APIでは結果はコールバック経由で取得されるため、
        # resultの戻り値も確認
        if result and isinstance(result, dict):
            cookies = result.get("cookies")
            if isinstance(cookies, dict):
                self._update_cookies_cache(cookies)

        return result

    def get(self, cookie: str) -> str | None:
        """Cookie値を名前で取得.

        Args:
            cookie: Cookie名

        Returns:
            Cookie値。見つからない場合はNone
        """
        return self.get_from_headers(cookie)

    def _update_cookies_cache(self, cookies: dict[str, str]) -> None:
        """Cookieキャッシュと初期化状態を更新."""
        # 空dictでも初期化済みとみなす（同一keyの重複生成を防ぐ）
        self._cookies = cookies
        self._initialized = True
        # session_stateにキャッシュ（rerun後も利用可能に）
        st.session_state[_COOKIES_CACHE_KEY] = cookies

    def set(
        self,
        cookie: str,
        val: str,
        expires_at: datetime | None = None,
        max_age: int | None = None,
        path: str = "/",
        domain: str | None = None,
        secure: bool = False,
        same_site: str = "lax",
    ) -> None:
        """Cookieを設定.

        Args:
            cookie: Cookie名
            val: Cookie値
            expires_at: 有効期限（datetime）
            max_age: 最大有効期間（秒）
            path: Cookieパス
            domain: Cookieドメイン
            secure: Secureフラグ
            same_site: SameSite属性（strict, lax, none）
        """
        kwargs: dict[str, Any] = {
            "name": cookie,
            "value": val,
            "path": path,
            "sameSite": same_site,
        }

        if expires_at is not None:
            kwargs["expires"] = expires_at.isoformat()

        if max_age is not None:
            kwargs["maxAge"] = max_age

        if domain is not None:
            kwargs["domain"] = domain

        if secure:
            kwargs["secure"] = True

        self._render(action="set", **kwargs)

    def delete(self, cookie: str, path: str = "/") -> None:
        """Cookieを削除.

        Args:
            cookie: Cookie名
            path: Cookieパス
        """
        if not cookie:
            return

        self._render(action="delete", name=cookie, path=path)

        # ローカルキャッシュからも削除
        self._cookies.pop(cookie, None)

    def get_all(self) -> dict[str, str]:
        """全Cookieを取得.

        Returns:
            全Cookieの辞書
        """
        return self.get_all_from_headers()


def get_cookie_manager(key: str = "cookie_manager") -> CookieManager:
    """CookieManagerインスタンスを取得.

    Args:
        key: コンポーネントインスタンスの一意キー

    Returns:
        CookieManagerインスタンス
    """
    return CookieManager(key=key)
