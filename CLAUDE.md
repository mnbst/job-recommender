# Job Recommender

## Writing Style
CLAUDE.md・skills/*.md・agents/*.mdを更新する際は以下を守る：
- **簡潔に**: 箇条書き・表・コードブロック優先。散文は避ける
- **重複排除**: 他ファイルと同じ情報を書かない
- **具体的に**: 曖昧な説明より具体例・コマンド・ファイルパス
- **構造化**: 見出し・表で情報を整理。長文段落は分割

## Stack
Python 3.11+ | Streamlit | Vertex AI (Gemini) | Perplexity AI (求人検索) | Terraform 1.6+ | GCP (Cloud Run + LB)

## Structure
```
app/
  main.py        → Streamlit UIエントリーポイント
  pages/         → Streamlitページ
  ui/            → UIコンポーネント
  services/      → ドメインロジック
terraform/       → インフラ定義 (Cloud Run + LB + Blue-Green)
scripts/
  proxy-green.sh → Green環境へのローカルプロキシ
  rollback.sh    → 前リビジョンへのロールバック
Dockerfile       → Python 3.11-slim + uv
```

## Flow
```
GitHub API → Vertex AI (プロファイル生成) → Perplexity AI (求人検索 + マッチング分析)
```

## Skills（必要時に参照）
以下のスキルはClaudeが作業内容に応じて自動で参照します：

| Skill | 参照タイミング |
|-------|---------------|
| [coding-standards](./.claude/skills/coding-standards/SKILL.md) | コード作成・修正・レビュー時 |
| [project-architecture](./.claude/skills/project-architecture/SKILL.md) | 実装方針検討・デバッグ時 |
| [troubleshooting](./.claude/skills/troubleshooting/SKILL.md) | 障害対応・エラー調査時 |
| [streamlit-redirects](./.claude/skills/streamlit-redirects/SKILL.md) | Streamlitの外部遷移・同一タブ遷移の調査/実装時 |
| [github-oauth](./.claude/skills/github-oauth/SKILL.md) | OAuth認証関連の作業時 |
| [testing](./.claude/skills/testing/SKILL.md) | テスト作成・実行時 |

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
uv run streamlit run app/main.py

# テスト・Lint
uv run pytest
uv run ruff check . && uv run ruff format .

# デプロイ (Blue本番)
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/${PROJECT_ID}/job-recommender/app:latest

# Terraform
cd terraform
terraform init -backend-config="bucket=${PROJECT_ID}-tfstate"
terraform plan && terraform apply

# Blue-Green デプロイ
./scripts/proxy-green.sh              # Green環境をローカルで検証
./scripts/rollback.sh                 # 前リビジョンにロールバック
```

## Environment Variables
Secret Managerで管理（Terraformは参照のみ）:
| シークレット名 | 用途 |
|---------------|------|
| `github_token` | GitHub PAT（リポジトリ取得用） |
| `perplexity_api_key` | Perplexity APIキー |
| `github_oauth_client_id` | Blue用 OAuth App Client ID |
| `github_oauth_client_secret` | Blue用 OAuth App Client Secret |
| `green_github_oauth_client_id` | Green用 OAuth App Client ID |
| `green_github_oauth_client_secret` | Green用 OAuth App Client Secret |

Cloud Runに自動注入される環境変数（Blue/Green共通）:
- `GITHUB_TOKEN`, `PERPLEXITY_API_KEY` - Secret Managerから
- `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET` - 各環境用を注入
- `OAUTH_REDIRECT_URI` - LB URLから自動生成
- `GCP_PROJECT_ID`, `GCP_LOCATION` - Terraform変数から

## GitHub OAuth App 設定
Blue/Green環境それぞれに別のOAuth Appが必要（callback URLが異なるため）:

| 環境 | Application name | Callback URL |
|------|------------------|--------------|
| Blue | `Job Recommender` | `https://<LB_IP>.nip.io` |
| Green | `Job Recommender Green` | `http://localhost:8080`（ローカルプロキシ用） |

Secret Manager登録:
```bash
# Blue用
echo -n "CLIENT_ID" | gcloud secrets create github_oauth_client_id --data-file=-
echo -n "CLIENT_SECRET" | gcloud secrets create github_oauth_client_secret --data-file=-

# Green用
echo -n "GREEN_CLIENT_ID" | gcloud secrets create green_github_oauth_client_id --data-file=-
echo -n "GREEN_CLIENT_SECRET" | gcloud secrets create green_github_oauth_client_secret --data-file=-
```

## Blue-Green Deployment
詳細は [project-architecture](./.claude/skills/project-architecture/SKILL.md) を参照。

**Green環境IAM設定** (`terraform.tfvars`):
```hcl
cloud_run_invoker_members = ["user:your-email@gmail.com"]
```
