# Job Recommender

## Memory Bank Rule
**重要**: 仕様変更・設計変更があった場合、関連ファイルを必ず更新：
| 変更内容 | 更新先 |
|---------|--------|
| スタック・構造 | [CLAUDE.md](./CLAUDE.md) |
| Python実装詳細 | [.claude/agents/python-dev.md](./.claude/agents/python-dev.md) |
| Terraform詳細 | [.claude/agents/terraform-modifier.md](./.claude/agents/terraform-modifier.md) |
| デプロイ手順 | [.claude/agents/deployer.md](./.claude/agents/deployer.md) |
| トラブル対応 | [.claude/agents/troubleshooter.md](./.claude/agents/troubleshooter.md) |

セッション終了前に必ず反映すること。

## Writing Style
CLAUDE.md・agents/*.mdを更新する際は以下を守る：
- **簡潔に**: 箇条書き・表・コードブロック優先。散文は避ける
- **重複排除**: 他ファイルと同じ情報を書かない
- **具体的に**: 曖昧な説明より具体例・コマンド・ファイルパス
- **構造化**: 見出し・表で情報を整理。長文段落は分割

## Stack
Python 3.11+ | Streamlit | Vertex AI (Gemini) | Discovery Engine | Terraform 1.6+ | GCP (Cloud Run + IAP + LB)

## Structure
```
app.py           → Streamlit UIエントリーポイント
services/
  github.py      → GitHub API (PyGithub) - RepoInfo取得
  profile.py     → Vertex AI Gemini - プロファイル生成
  research.py    → Discovery Engine - Deep Research求人検索
db/              → SQLAlchemyモデル（現在アプリから未使用）
  models.py      → User, SearchHistory
terraform/       → インフラ定義 (Cloud Run + LB + IAP)
Dockerfile       → Python 3.11-slim + uv
```

## Agents（作業別）
| 作業 | エージェント |
|------|-------------|
| Python実装 | python-dev |
| Terraform修正 | terraform-modifier |
| デプロイ | deployer |
| 障害対応 | troubleshooter |

## Quick Commands
```bash
# 依存関係インストール
uv sync

# ローカル実行
uv run streamlit run app.py

# テスト・Lint
uv run pytest
uv run ruff check . && uv run ruff format .

# デプロイ
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/${PROJECT_ID}/job-recommender/app:latest

# Terraform
cd terraform && terraform plan && terraform apply
```

## Environment Variables
`.env`に設定:
- `GITHUB_TOKEN` - GitHub PAT
- `GCP_PROJECT_ID` - GCPプロジェクトID
- `GCP_LOCATION` - Vertex AIリージョン (default: asia-northeast1)
- `DATABASE_URL` - DB接続文字列（現状アプリから未使用。未設定時SQLiteフォールバックだがCloud Runでは揮発的）
- `DISCOVERY_ENGINE_APP_ID` - Deep Research用アプリID
