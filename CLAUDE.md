# Job Recommender

## Writing Style
CLAUDE.md・skills/*.md・agents/*.mdを更新する際は以下を守る：
- **簡潔に**: 箇条書き・表・コードブロック優先。散文は避ける
- **重複排除**: 他ファイルと同じ情報を書かない
- **具体的に**: 曖昧な説明より具体例・コマンド・ファイルパス
- **構造化**: 見出し・表で情報を整理。長文段落は分割

## Stack
Python 3.11+ | Streamlit | Vertex AI (Gemini) | Perplexity AI (求人検索) | Terraform 1.6+ | GCP (Cloud Run + LB + Cloud Build) | GitHub OAuth + Firestore

## Structure
```
app/
  main.py              → Streamlit UIエントリーポイント
  pages/               → Streamlitページ (home, logout, plans, privacy, terms)
  ui/                  → UIコンポーネント (job_search, profile, sidebar, welcome, etc)
  services/            → ドメインロジック (auth, github, profile, research, session, quota, etc)
terraform/
  main.tf              → Cloud Run, Secret Manager, IAM
  load_balancer.tf     → LB, SSL証明書
  cloudbuild.tf        → Cloud Build Trigger (CI/CD)
  firestore.tf         → Firestore Database
  monitoring.tf        → アラート設定
  providers.tf         → Terraformプロバイダー
  variables.tf         → 変数定義
scripts/
  load-env.sh          → GCP認証スクリプト
  pre-terraform-apply.sh → terraform apply前のDockerビルドフック
  proxy-green.sh       → Green環境へのローカルプロキシ
  rollback.sh          → 前リビジョンへのロールバック
Dockerfile             → マルチステージビルド (Python 3.11-slim + uv)
pyproject.toml         → 依存関係管理 (uv)
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
# 依存関係インストール
uv sync              # 開発用（テスト含む）
uv sync --no-dev     # 本番用

# ローカル実行
./scripts/load-env.sh                      # GCP認証（初回のみ）
uv run streamlit run app/main.py           # http://localhost:8501

# テスト・Lint
uv run pytest
uv run ruff check . && uv run ruff format .

# Dockerイメージビルド＆プッシュ (Blue本番)
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/${PROJECT_ID}/job-recommender/app:latest

# Terraform（初回）
cd terraform
terraform init -backend-config="bucket=${PROJECT_ID}-tfstate"

# Terraform適用（自動的にDockerビルド→terraform apply実行）
terraform plan
terraform apply    # pre-terraform-apply.shフックで自動ビルド

# Blue-Green デプロイ
./scripts/proxy-green.sh    # Green環境をローカルで検証（http://localhost:8080）
./scripts/rollback.sh       # Blue環境を前リビジョンにロールバック
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
| Blue | `Job Recommender` | `https://<LB_IP>.nip.io/app` または `https://<CUSTOM_DOMAIN>/app` |
| Green | `Job Recommender Green` | `http://localhost:8080/app`（ローカルプロキシ用） |

**注**: Callback URLのパス `/app` はCloud RunのbaseUrlPathと一致させる必要があります。

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

### CI/CD自動デプロイ
Cloud Build Triggerで `main` ブランチへのpushを検知して自動デプロイ（Blue環境）:
- `terraform/cloudbuild.tf` で定義
- GitHub接続は事前にGCP Consoleで手動設定が必要
- ビルド成功/失敗のアラートはメール通知（`monitoring.tf`）

### Green環境IAM設定
`terraform/terraform.tfvars`:
```hcl
cloud_run_invoker_members = ["user:your-email@gmail.com"]
```

### 手動デプロイフロー
1. Dockerビルド＆プッシュ（Blue環境）
2. `terraform apply` で反映（`pre-terraform-apply.sh` フックで自動ビルド）
3. Green環境のローカル検証: `./scripts/proxy-green.sh`
4. 問題発生時のロールバック: `./scripts/rollback.sh`
