"""AppTestを使ったCookieManagerのテスト.

streamlit.testing.v1.AppTest.from_function()を使用。
"""

from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

# AppTestのデフォルトタイムアウト（秒）
DEFAULT_TIMEOUT = 30


def app_get_cookie():
    """Cookieを取得するテスト用アプリ."""
    import streamlit as st

    from app.services.streamlit_components.cookie_manager import get_cookie_manager

    st.title("Cookie Test")
    manager = get_cookie_manager(key="test")
    session_id = manager.get(cookie="session_id")
    st.write(f"Session: {session_id}")


def app_set_cookie():
    """Cookieを設定するテスト用アプリ."""
    import streamlit as st

    from app.services.streamlit_components.cookie_manager import get_cookie_manager

    st.title("Cookie Set Test")
    manager = get_cookie_manager(key="set_test")

    if st.button("Set Cookie"):
        manager.set(cookie="user_pref", val="dark_mode")
        st.success("Cookie set!")


def app_delete_cookie():
    """Cookieを削除するテスト用アプリ."""
    import streamlit as st

    from app.services.streamlit_components.cookie_manager import get_cookie_manager

    st.title("Cookie Delete Test")
    manager = get_cookie_manager(key="delete_test")

    if st.button("Delete Cookie"):
        manager.delete(cookie="to_delete")
        st.success("Cookie deleted!")


def app_session_flow():
    """セッションフローのテスト用アプリ."""
    import streamlit as st

    from app.services.session import get_session_cookie, set_session_cookie
    from app.services.streamlit_components.cookie_manager import get_cookie_manager

    st.title("Session Flow Test")
    manager = get_cookie_manager(key="session_test")

    session_id = get_session_cookie()

    if session_id:
        st.write(f"Logged in: {session_id}")
    else:
        st.write("Not logged in")
        if st.button("Login"):
            set_session_cookie(manager, "new-session-id")
            st.success("Logged in!")


class TestCookieManagerWithAppTest:
    """AppTestを使ったCookieManagerテスト."""

    @pytest.fixture
    def mock_cookie_component(self):
        """カスタムコンポーネントのモック."""
        with patch("app.services.streamlit_components.cookie_manager._cookie_component") as mock:
            mock.return_value = {"cookies": {}, "result": None}
            yield mock

    def test_get_cookie_in_app(self, mock_cookie_component):
        """AppTest内でCookieを取得."""
        with patch(
            "app.services.streamlit_components.cookie_manager.CookieManager.get_from_headers",
            return_value="test-session-123",
        ):
            at = AppTest.from_function(app_get_cookie)
            at.run(timeout=DEFAULT_TIMEOUT)

        assert not at.exception
        output_texts = [m.value for m in at.markdown]
        assert any("test-session-123" in str(t) for t in output_texts)

    def test_set_cookie_in_app(self, mock_cookie_component):
        """AppTest内でCookieを設定."""
        at = AppTest.from_function(app_set_cookie)
        at.run(timeout=DEFAULT_TIMEOUT)

        assert not at.exception

        at.button[0].click().run(timeout=DEFAULT_TIMEOUT)

        assert not at.exception
        calls = mock_cookie_component.call_args_list
        set_calls = [
            c for c in calls if c.kwargs.get("data", {}).get("action") == "set"
        ]
        assert len(set_calls) >= 1

    def test_delete_cookie_in_app(self, mock_cookie_component):
        """AppTest内でCookieを削除."""
        mock_cookie_component.return_value = {
            "cookies": {"to_delete": "some_value"},
            "result": None,
        }

        at = AppTest.from_function(app_delete_cookie)
        at.run(timeout=DEFAULT_TIMEOUT)

        at.button[0].click().run(timeout=DEFAULT_TIMEOUT)

        assert not at.exception
        calls = mock_cookie_component.call_args_list
        delete_calls = [
            c for c in calls if c.kwargs.get("data", {}).get("action") == "delete"
        ]
        assert len(delete_calls) >= 1


class TestSessionIntegrationWithAppTest:
    """session.pyとの統合テスト（AppTest使用）."""

    @pytest.fixture
    def mock_cookie_component(self):
        """カスタムコンポーネントのモック."""
        with patch("app.services.streamlit_components.cookie_manager._cookie_component") as mock:
            mock.return_value = {"cookies": {}, "result": None}
            yield mock

    def test_session_flow_with_apptest(self, mock_cookie_component):
        """セッションフロー全体のテスト."""
        mock_cookie_component.return_value = {
            "cookies": {},
            "result": None,
        }

        at = AppTest.from_function(app_session_flow)
        at.run(timeout=DEFAULT_TIMEOUT)

        assert not at.exception
        assert any("Not logged in" in str(m.value) for m in at.markdown)

        at.button[0].click().run(timeout=DEFAULT_TIMEOUT)

        calls = mock_cookie_component.call_args_list
        set_calls = [
            c for c in calls if c.kwargs.get("data", {}).get("action") == "set"
        ]
        assert len(set_calls) >= 1
