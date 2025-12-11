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
Python 3.11+ | Streamlit | Vertex AI (Gemini) | SerpAPI (Google Jobs) | Terraform 1.6+ | GCP (Cloud Run + IAP + LB)

## Structure
```
app.py           → Streamlit UIエントリーポイント
services/
  github.py      → GitHub API (PyGithub) - RepoInfo取得
  profile.py     → Vertex AI Gemini - プロファイル生成 + 求人マッチング分析
  research.py    → SerpAPI Google Jobs - 求人検索
terraform/       → インフラ定義 (Cloud Run + LB + IAP)
Dockerfile       → Python 3.11-slim + uv
```

## Flow
```
GitHub API → Vertex AI (プロファイル生成) → SerpAPI (求人検索) → Vertex AI (マッチング分析)
```

## Agents（作業別）
| 作業 | エージェント |
|------|-------------|
| Python実装 | [python-dev](./.claude/agents/python-dev.md) |
| Terraform修正 | [terraform-modifier](./.claude/agents/terraform-modifier.md) |
| デプロイ | [deployer](./.claude/agents/deployer.md) |
| 障害対応 | [troubleshooter](./.claude/agents/troubleshooter.md) |

## Quick Commands
```bash
# 依存関係インストール（本番用）
uv sync --no-dev

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
Secret Managerで管理（Terraformは参照のみ）:
| シークレット名 | 用途 |
|---------------|------|
| `github_token` | GitHub PAT |
| `serp_api_key` | SerpAPI APIキー |

Cloud Runに自動注入される環境変数:
- `GITHUB_TOKEN` - Secret Managerから
- `SERPAPI_API_KEY` - Secret Managerから
- `GCP_PROJECT_ID` - Terraform変数から
- `GCP_LOCATION` - Terraform変数から
