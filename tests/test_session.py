"""Tests for app/services/session.py - HTTP header cookie functions."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.const import SESSION_COOKIE_NAME


class TestGetSessionCookie:
    """get_session_cookie関数のテスト."""

    @pytest.fixture
    def mock_st_context(self):
        """st.contextのモック."""
        with patch("app.services.headers_utils.st") as mock_st:
            mock_st.context = MagicMock()
            mock_st.context.headers = MagicMock()
            yield mock_st.context.headers

    def test_returns_session_id_when_cookie_exists(self, mock_st_context):
        """セッションCookieが存在する場合にsession_idを返す."""
        from app.services.session import get_session_cookie

        mock_st_context.get.return_value = f"{SESSION_COOKIE_NAME}=abc123"

        result = get_session_cookie()

        assert result == "abc123"

    def test_returns_session_id_with_multiple_cookies(self, mock_st_context):
        """複数のCookieがある場合でもセッションCookieを正しく取得."""
        from app.services.session import get_session_cookie

        cookie_header = (
            f"other=value; {SESSION_COOKIE_NAME}=my-session-id; another=test"
        )
        mock_st_context.get.return_value = cookie_header

        result = get_session_cookie()

        assert result == "my-session-id"

    def test_returns_none_when_no_cookie_header(self, mock_st_context):
        """Cookieヘッダーがない場合はNoneを返す."""
        from app.services.session import get_session_cookie

        mock_st_context.get.return_value = ""

        result = get_session_cookie()

        assert result is None

    def test_returns_none_when_session_cookie_not_found(self, mock_st_context):
        """セッションCookieがない場合はNoneを返す."""
        from app.services.session import get_session_cookie

        mock_st_context.get.return_value = "other_cookie=value; another=test"

        result = get_session_cookie()

        assert result is None

    def test_returns_none_on_exception(self, mock_st_context):
        """例外発生時はNoneを返す."""
        from app.services.session import get_session_cookie

        mock_st_context.get.side_effect = Exception("Test error")

        result = get_session_cookie()

        assert result is None

    def test_handles_whitespace_in_cookie_header(self, mock_st_context):
        """Cookie値の前後の空白を正しく処理する."""
        from app.services.session import get_session_cookie

        cookie_header = (
            f"  other=value ;  {SESSION_COOKIE_NAME}=session-value  ; another=test  "
        )
        mock_st_context.get.return_value = cookie_header

        result = get_session_cookie()

        # strip()でCookieエントリの前後空白が除去される
        assert result == "session-value"

    def test_handles_empty_session_value(self, mock_st_context):
        """セッションCookieの値が空の場合."""
        from app.services.session import get_session_cookie

        cookie_header = f"{SESSION_COOKIE_NAME}="
        mock_st_context.get.return_value = cookie_header

        result = get_session_cookie()

        assert result == ""
