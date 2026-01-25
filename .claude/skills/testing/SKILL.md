---
name: testing
description: pytest自動テストの規約。テスト作成・実行時に参照。モック、フィクスチャ、Streamlitコンポーネントテストなど。
user-invocable: false
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Testing Standards (pytest)

## 基本ルール

| ルール | 詳細 |
|--------|------|
| フレームワーク | pytest |
| ファイル配置 | `tests/test_*.py` |
| クラス構成 | `class Test機能名:` でグループ化 |
| docstring | 日本語で簡潔に（テスト内容を説明） |
| モック | `unittest.mock.patch`, `MagicMock` |
| フィクスチャ | `@pytest.fixture` で共通セットアップ |

## ディレクトリ構成

```
tests/
  test_profile.py      # services/profile.py のテスト
  test_research.py     # services/research.py のテスト
  test_cookie_manager.py  # コンポーネントのテスト
```

## テスト構成パターン

```python
"""Tests for services/xxx.py."""

from unittest.mock import MagicMock, patch

import pytest


class TestFeatureName:
    """機能名のテスト."""

    @pytest.fixture
    def mock_dependency(self):
        """依存のモック."""
        with patch("services.xxx.dependency") as mock:
            yield mock

    def test_正常系の説明(self, mock_dependency):
        """正常系テスト."""
        mock_dependency.return_value = expected_value
        result = target_function()
        assert result == expected_value

    def test_異常系の説明(self, mock_dependency):
        """異常系テスト."""
        mock_dependency.side_effect = SomeException()
        result = target_function()
        assert result is None
```

## Streamlitコンポーネントのモック

Streamlit components.v2 を使うコンポーネントのテストパターン:

```python
class TestCookieManager:
    """CookieManagerのテスト."""

    @pytest.fixture
    def mock_component(self):
        """Streamlitコンポーネントのモック."""
        with patch(
            "services.components.cookie_manager.components.component"
        ) as mock_comp:
            mock_func = MagicMock()
            mock_comp.return_value = mock_func
            yield mock_func

    def test_get_cookie(self, mock_component):
        """Cookie取得テスト."""
        # モジュールを再インポートしてモック適用
        import importlib
        import services.components.cookie_manager as cm_module
        importlib.reload(cm_module)

        # コンポーネントの戻り値を設定
        mock_component.return_value = {
            "cookies": {"session_id": "abc123"},
            "result": None,
        }

        manager = cm_module.CookieManager(key="test")
        result = manager.get(cookie="session_id")

        assert result == "abc123"
```

### 重要ポイント

- `importlib.reload()` でモック適用後にモジュールを再読み込み
- コンポーネントの戻り値は `dict` 形式で設定
- 各テストで新しいインスタンスを作成

## 外部APIのモック

```python
class TestGitHubAPI:
    """GitHub API呼び出しのテスト."""

    @pytest.fixture
    def mock_httpx(self):
        """httpxクライアントのモック."""
        with patch("services.auth.httpx") as mock:
            yield mock

    def test_api_success(self, mock_httpx):
        """API成功時."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123, "login": "user"}
        mock_httpx.get.return_value = mock_response

        result = get_github_user("token")
        assert result.login == "user"

    def test_api_failure(self, mock_httpx):
        """API失敗時."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_httpx.get.return_value = mock_response

        result = get_github_user("invalid_token")
        assert result is None
```

## Firestoreのモック

```python
@pytest.fixture
def mock_firestore():
    """Firestoreクライアントのモック."""
    with patch("services.session.get_firestore_client") as mock:
        mock_db = MagicMock()
        mock.return_value = mock_db
        yield mock_db

def test_save_session(mock_firestore):
    """セッション保存テスト."""
    mock_doc_ref = MagicMock()
    mock_firestore.collection.return_value.document.return_value = mock_doc_ref

    save_firestore_session("session_id", user, "token")

    mock_doc_ref.set.assert_called_once()
```

## Streamlit AppTestの使用

`streamlit.testing.v1.AppTest`を使った統合テスト:

```python
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

DEFAULT_TIMEOUT = 30  # タイムアウト設定（秒）


def app_test_function():
    """テスト用アプリ関数."""
    # 重要: 関数内でstをインポートする
    import streamlit as st

    from services.xxx import some_function

    st.title("Test App")
    if st.button("Click"):
        st.write("Clicked!")


class TestWithAppTest:
    """AppTestを使ったテスト."""

    @pytest.fixture
    def mock_component(self):
        """カスタムコンポーネントのモック."""
        with patch("services.components.xxx._component") as mock:
            mock.return_value = {"data": "value"}
            yield mock

    def test_app_flow(self, mock_component):
        """アプリフローのテスト."""
        at = AppTest.from_function(app_test_function)
        at.run(timeout=DEFAULT_TIMEOUT)  # タイムアウト必須

        assert not at.exception

        # ボタンクリック
        at.button[0].click().run(timeout=DEFAULT_TIMEOUT)
        assert not at.exception
```

### 注意点

| 項目 | 詳細 |
|------|------|
| **import文の位置** | `from_function`では関数内で`import streamlit as st`が必須 |
| **タイムアウト** | `at.run(timeout=N)`で設定。ハング防止に必須 |
| **カスタムコンポーネント** | v2 APIはAppTestでサポートされない。モック必須 |
| **出力確認** | `at.markdown`, `at.button`などで要素にアクセス |

## 実行コマンド

```bash
# 全テスト実行
uv run pytest

# 詳細出力
uv run pytest -v

# 特定ファイル
uv run pytest tests/test_xxx.py

# 特定テストクラス/メソッド
uv run pytest tests/test_xxx.py::TestClass::test_method

# 失敗時に即停止
uv run pytest -x

# 最後に失敗したテストのみ再実行
uv run pytest --lf
```

## テスト作成チェックリスト

- [ ] 正常系テスト
- [ ] 異常系テスト（エラー、None、空）
- [ ] 境界値テスト
- [ ] 外部依存はモック化
- [ ] docstringで何をテストしているか明記
