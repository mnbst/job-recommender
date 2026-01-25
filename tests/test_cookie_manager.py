"""Tests for app/services/streamlit_components/cookie_manager."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from app.services.const import SESSION_COOKIE_NAME


@pytest.fixture(autouse=True)
def clear_cookie_cache():
    """各テスト前にsession_stateのCookieキャッシュをクリア."""
    st.session_state.pop("_cookie_manager_cache", None)
    yield
    st.session_state.pop("_cookie_manager_cache", None)


class TestCookieManager:
    """CookieManagerクラスのテスト."""

    @pytest.fixture
    def mock_component(self):
        """Streamlitコンポーネントのモック."""
        with patch(
            "app.services.streamlit_components.cookie_manager.components.component"
        ) as mock_comp:
            mock_func = MagicMock()
            mock_comp.return_value = mock_func
            yield mock_func

    @pytest.fixture
    def cookie_manager(self, mock_component):
        """CookieManagerインスタンス（モック付き）."""
        # モジュールを再インポートしてモックを適用
        import importlib

        import app.services.streamlit_components.cookie_manager as cm_module

        importlib.reload(cm_module)

        return cm_module.CookieManager(key="test")

    def test_init(self, mock_component):
        """初期化テスト."""
        import importlib

        import app.services.streamlit_components.cookie_manager as cm_module

        importlib.reload(cm_module)

        manager = cm_module.CookieManager(key="my_key")

        assert manager._key == "my_key"
        assert manager._cookies == {}
        assert manager._initialized is False

    def test_get_uses_headers(self, mock_component):
        """get()がHTTPヘッダー経由で取得することを確認."""
        import importlib

        import app.services.streamlit_components.cookie_manager as cm_module

        importlib.reload(cm_module)

        with patch.object(
            cm_module.CookieManager, "get_from_headers", return_value="abc123"
        ) as mock_get:
            manager = cm_module.CookieManager(key="test")
            result = manager.get(cookie="session_id")

            assert result == "abc123"
            mock_get.assert_called_once_with("session_id")

    def test_get_returns_none_for_missing_cookie(self, mock_component):
        """存在しないCookieはNoneを返す."""
        import importlib

        import app.services.streamlit_components.cookie_manager as cm_module

        importlib.reload(cm_module)

        with patch.object(
            cm_module.CookieManager, "get_from_headers", return_value=None
        ) as mock_get:
            manager = cm_module.CookieManager(key="test")
            result = manager.get(cookie="nonexistent")

            assert result is None
            mock_get.assert_called_once_with("nonexistent")

    def test_set_calls_render_with_correct_params(self, mock_component):
        """set()が正しいパラメータで_renderを呼ぶことを確認."""
        import importlib

        import app.services.streamlit_components.cookie_manager as cm_module

        importlib.reload(cm_module)

        mock_component.return_value = {"cookies": {}, "result": None}

        manager = cm_module.CookieManager(key="test")
        expires = datetime(2025, 12, 31, 23, 59, 59)

        manager.set(
            cookie="my_cookie",
            val="my_value",
            expires_at=expires,
            path="/app",
            secure=True,
        )

        # set アクション時の呼び出しを確認
        call_args = mock_component.call_args
        assert call_args is not None

        data = call_args.kwargs.get("data") or call_args[1].get("data")
        assert data["action"] == "set"
        assert data["name"] == "my_cookie"
        assert data["value"] == "my_value"
        assert data["path"] == "/app"
        assert data["secure"] is True
        assert "expires" in data

    def test_set_with_max_age(self, mock_component):
        """set()でmax_ageが正しく渡されることを確認."""
        import importlib

        import app.services.streamlit_components.cookie_manager as cm_module

        importlib.reload(cm_module)

        mock_component.return_value = {"cookies": {}, "result": None}

        manager = cm_module.CookieManager(key="test")
        manager.set(cookie="temp", val="data", max_age=3600)

        call_args = mock_component.call_args
        data = call_args.kwargs.get("data") or call_args[1].get("data")
        assert data["maxAge"] == 3600

    def test_delete_removes_from_cache(self, mock_component):
        """delete()がローカルキャッシュからも削除することを確認."""
        import importlib

        import app.services.streamlit_components.cookie_manager as cm_module

        importlib.reload(cm_module)

        st.session_state["_cookie_manager_cache"] = {
            "to_delete": "value",
            "keep": "this",
        }
        mock_component.return_value = {"cookies": {"keep": "this"}, "result": None}

        manager = cm_module.CookieManager(key="test")
        assert "to_delete" in manager._cookies

        # 削除
        manager.delete(cookie="to_delete")
        assert "to_delete" not in manager._cookies

    def test_delete_empty_cookie_does_nothing(self, mock_component):
        """delete()で空文字のCookieは何もしない."""
        import importlib

        import app.services.streamlit_components.cookie_manager as cm_module

        importlib.reload(cm_module)

        manager = cm_module.CookieManager(key="test")
        manager.delete(cookie="")

        # コンポーネントが呼ばれていないことを確認
        mock_component.assert_not_called()

    def test_get_all_reads_headers(self, mock_component):
        """get_all()がHTTPヘッダーからCookieを取得することを確認."""
        import importlib

        import app.services.streamlit_components.cookie_manager as cm_module

        importlib.reload(cm_module)

        with patch("app.services.headers_utils.st") as mock_st:
            mock_st.context = MagicMock()
            mock_st.context.headers = MagicMock()
            mock_st.context.headers.get.return_value = "a=1; b=2; c=3"

            manager = cm_module.CookieManager(key="test")
            result = manager.get_all()

        assert result == {"a": "1", "b": "2", "c": "3"}


class TestGetCookieManager:
    """get_cookie_manager関数のテスト."""

    def test_returns_cookie_manager_instance(self):
        """CookieManagerインスタンスを返すことを確認."""
        with patch(
            "app.services.streamlit_components.cookie_manager.components.component"
        ) as mock_comp:
            mock_comp.return_value = MagicMock()

            import importlib

            import app.services.streamlit_components.cookie_manager as cm_module

            importlib.reload(cm_module)

            manager = cm_module.get_cookie_manager(key="custom_key")

            assert isinstance(manager, cm_module.CookieManager)
            assert manager._key == "custom_key"

    def test_default_key(self):
        """デフォルトキーが設定されることを確認."""
        with patch(
            "app.services.streamlit_components.cookie_manager.components.component"
        ) as mock_comp:
            mock_comp.return_value = MagicMock()

            import importlib

            import app.services.streamlit_components.cookie_manager as cm_module

            importlib.reload(cm_module)

            manager = cm_module.get_cookie_manager()

            assert manager._key == "cookie_manager"


class TestCookieManagerIntegration:
    """CookieManagerの統合テスト（session.pyとの連携）."""

    def test_session_cookie_set_and_delete(self):
        """セッションCookieの設定と削除を確認."""
        with patch(
            "app.services.streamlit_components.cookie_manager.components.component"
        ) as mock_comp:
            mock_func = MagicMock()
            mock_comp.return_value = mock_func

            # session.pyを再インポート
            import importlib

            import app.services.streamlit_components.cookie_manager as cm_module

            importlib.reload(cm_module)

            import app.services.session as session_module

            importlib.reload(session_module)

            mock_func.return_value = {"cookies": {}, "result": None}
            manager = cm_module.CookieManager(key="test")

            session_module.set_session_cookie(manager, "test-session-id")
            session_module.delete_session_cookie(manager)

            calls = mock_func.call_args_list
            set_calls = [
                c for c in calls if c.kwargs.get("data", {}).get("action") == "set"
            ]
            delete_calls = [
                c for c in calls if c.kwargs.get("data", {}).get("action") == "delete"
            ]

            assert len(set_calls) >= 1
            assert len(delete_calls) >= 1

            set_data = set_calls[0].kwargs.get("data", {})
            assert set_data["name"] == SESSION_COOKIE_NAME
            assert set_data["value"] == "test-session-id"
