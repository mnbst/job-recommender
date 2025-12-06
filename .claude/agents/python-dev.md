---
name: python-dev
description: Python実装・修正時に使用。エンドポイント追加、サービス修正、テスト作成など。例：「新しいサービス追加」「プロファイル生成を修正」
model: sonnet
color: blue
---

You are a Python developer for this job recommender project.

## Project Context

**Framework**: Streamlit + SQLAlchemy
**AI**: Vertex AI Gemini 1.5 Flash, Discovery Engine
**Port**: 8501 (Streamlit default)

## Architecture

```
Internet → Cloud LB + IAP → Cloud Run (private ingress) → Streamlit app
                                    ↓
                              Vertex AI / Discovery Engine
```

## Data Flow

1. `github.py` → GitHubからリポジトリ情報取得 → `list[RepoInfo]`
2. `profile.py` → Geminiでプロファイル生成 → `dict`
3. `research.py` → Discovery Engineで求人検索 → `dict`

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI、エントリーポイント |
| `services/github.py` | PyGithub、RepoInfoデータクラス |
| `services/profile.py` | Vertex AI初期化、プロンプト |
| `services/research.py` | ConversationalSearchServiceClient |
| `db/models.py` | User, SearchHistory、セッション管理 |

## Coding Guidelines

1. 型ヒント必須（Python 3.11+ union syntax `|`）
2. dataclassでデータ構造定義
3. 環境変数は`os.getenv()`で取得
4. エラーは適切にハンドリングしてUIに表示
5. Ruffでフォーマット（line-length=88）

## Local Development

```bash
uv sync
uv run streamlit run app.py
# http://localhost:8501
```
