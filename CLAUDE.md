# Job Recommender

## Memory Bank Rule
**重要**: 仕様変更・設計変更があった場合、関連ファイルを必ず更新：
| 変更内容 | 更新先 |
|---------|--------|
| スタック・構造 | [CLAUDE.md](./CLAUDE.md) |
| コーディング規約 | [.claude/skills/coding-standards/SKILL.md](./.claude/skills/coding-standards/SKILL.md) |
| アーキテクチャ | [.claude/skills/project-architecture/SKILL.md](./.claude/skills/project-architecture/SKILL.md) |
| トラブル対応 | [.claude/skills/troubleshooting/SKILL.md](./.claude/skills/troubleshooting/SKILL.md) |

セッション終了前に必ず反映すること。

## Writing Style
CLAUDE.md・skills/*.md・agents/*.mdを更新する際は以下を守る：
- **簡潔に**: 箇条書き・表・コードブロック優先。散文は避ける
- **重複排除**: 他ファイルと同じ情報を書かない
- **具体的に**: 曖昧な説明より具体例・コマンド・ファイルパス
- **構造化**: 見出し・表で情報を整理。長文段落は分割

## Stack
Python 3.11+ | Streamlit | Vertex AI (Gemini) | Perplexity AI (求人検索) | Terraform 1.6+ | GCP (Cloud Run + IAP + LB)

## Structure
```
app.py           → Streamlit UIエントリーポイント
services/
  github.py      → GitHub API (PyGithub) - RepoInfo取得
  profile.py     → Vertex AI Gemini - プロファイル生成
  research.py    → Perplexity AI - 求人検索 + マッチング分析
terraform/       → インフラ定義 (Cloud Run + LB + IAP)
Dockerfile       → Python 3.11-slim + uv
```

## Flow
```
GitHub API → Vertex AI (プロファイル生成) → Perplexity AI (求人検索 + マッチング分析)
```

## Skills（自動参照）
| Skill | 用途 |
|-------|------|
| [coding-standards](./.claude/skills/coding-standards/SKILL.md) | Python/Terraform コーディング規約 |
| [project-architecture](./.claude/skills/project-architecture/SKILL.md) | データフロー・インフラ構成 |
| [troubleshooting](./.claude/skills/troubleshooting/SKILL.md) | 障害対応・デバッグ |

## Agents（作業実行）
| 作業 | エージェント |
|------|-------------|
| Python実装 | [python-dev](./.claude/agents/python-dev.md) |
| Terraform修正 | [terraform-modifier](./.claude/agents/terraform-modifier.md) |
| デプロイ | [deployer](./.claude/agents/deployer.md) |
| コードレビュー | [code-reviewer](./.claude/agents/code-reviewer.md) |
| テスト | [tester](./.claude/agents/tester.md) |
| ドキュメント | [documenter](./.claude/agents/documenter.md) |
| デバッグ | [debugger](./.claude/agents/debugger.md) |
| 移行 | [migrator](./.claude/agents/migrator.md) |

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
cd terraform
terraform init -backend-config="bucket=${PROJECT_ID}-tfstate"
terraform plan && terraform apply
```

## Environment Variables
Secret Managerで管理（Terraformは参照のみ）:
| シークレット名 | 用途 |
|---------------|------|
| `github_token` | GitHub PAT |
| `perplexity_api_key` | Perplexity APIキー |

Cloud Runに自動注入される環境変数:
- `GITHUB_TOKEN` - Secret Managerから
- `PERPLEXITY_API_KEY` - Secret Managerから
- `GCP_PROJECT_ID` - Terraform変数から
- `GCP_LOCATION` - Terraform変数から
