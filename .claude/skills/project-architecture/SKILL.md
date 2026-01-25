---
name: project-architecture
description: プロジェクト構造とデータフロー。実装、修正、デバッグ時に参照。GitHub API、Vertex AI、Perplexity AI連携。
user-invocable: false
allowed-tools: Read, Grep, Glob
---

# Project Architecture

## Data Flow

```
1. github.py   → GitHubからリポジトリ情報取得 → list[RepoInfo]
2. profile.py  → Geminiでプロファイル生成    → dict
3. research.py → Perplexity AIで求人検索+マッチング分析 → JobSearchResult
```

## Infrastructure (Blue-Green)

```
                              ┌─ /        → GCS静的サイト (ランディングページ)
Internet → Cloud LB (HTTPS) ──┤
                              └─ /app/*   → Cloud Run (job-recommender) [Blue]
                                                  ↓
                                            VPC Connector → Vertex AI / Perplexity AI

Local Dev → IAM認証プロキシ → Cloud Run (job-recommender-green) [Green]
```

| コンポーネント | リソース | 用途 |
|--------------|---------|------|
| ランディングページ | `gs://${project_id}-landing-page` | 静的HTML（Bot対策、CDN有効） |
| アプリ (Blue) | `job-recommender` | 本番環境（LB経由、allUsers） |
| アプリ (Green) | `job-recommender-green` | 検証環境（IAM認証、ローカルプロキシ） |

認証: GitHub OAuth（Blue/Green別アプリ、GreenはローカルCallback）

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI、エントリーポイント |
| `services/github.py` | PyGithub、RepoInfoデータクラス |
| `services/profile.py` | Vertex AI初期化、プロファイル生成 |
| `services/research.py` | Perplexity AI、JobRecommendationデータクラス |
| `terraform/` | インフラ定義 (Cloud Run + LB) |

## Key Resources (Terraform)

| Resource | Purpose |
|----------|---------|
| `google_cloud_run_v2_service.app` | Blue本番（ingress: LB経由のみ、IAM: allUsers） |
| `google_cloud_run_v2_service.green` | Green検証（ingress: ALL、IAM: 制限付き） |
| `google_compute_backend_service.app` | Blue用バックエンド |
| `google_compute_region_network_endpoint_group` | Serverless NEG (Blue用) |
| `google_compute_url_map` | LBルーティング（Blue環境のみ） |
| `google_artifact_registry_repository` | Dockerイメージ保存 |
| `google_cloudbuild_trigger` | main/dev Push時の自動ビルド |

## CI/CD (Cloud Build)

### パイプライン
```
main Push → Cloud Build Trigger → Docker Build → Artifact Registry Push
```

### GitHub接続手順 (2nd gen)

1. **GCP Console で接続作成**
   ```
   Cloud Build → Repositories → 2nd gen → CREATE HOST CONNECTION
   → GitHub選択 → ブラウザで認証
   ```

2. **リポジトリをリンク**
   ```
   接続作成後 → LINK REPOSITORY → リポジトリ選択
   ```

3. **リポジトリIDを取得**
   ```bash
   gcloud builds repositories describe <repo-name> \
     --connection=<connection-name> \
     --region=asia-northeast1 \
     --format="value(name)"
   ```
   形式: `projects/{project}/locations/{region}/connections/{connection}/repositories/{repo}`

4. **terraform.tfvarsに設定**
   ```hcl
   cloudbuild_repository_id = "projects/xxx/locations/asia-northeast1/connections/xxx/repositories/xxx"
   ```

### 重要ポイント
- **service_account必須**: 2nd genリポジトリのTriggerには`service_account`指定が必須（未指定だとエラー400）
- **データソース非対応**: `google_cloudbuildv2_connection`/`google_cloudbuildv2_repository`のデータソースは未サポート → 変数でID指定

## Blue-Green Deployment

### 環境構成
| 環境 | Service名 | アクセス方法 | Ingress | IAM |
|------|----------|-------------|---------|-----|
| Blue | `job-recommender` | LB経由 | INTERNAL_LOAD_BALANCER | allUsers |
| Green | `job-recommender-green` | ローカルプロキシ | ALL | 制限付き |

### デプロイ検証フロー
```
1. devブランチにpush → Cloud BuildでGreen環境にデプロイ
2. Green検証: ./scripts/proxy-green.sh でローカルからIAM認証でアクセス
3. 問題なければmainにマージ → Blue環境にデプロイ
4. 問題時: ./scripts/rollback.sh で前リビジョンに戻す
```

### スクリプト
| スクリプト | 用途 |
|-----------|------|
| `scripts/proxy-green.sh` | ローカルからGreen環境にプロキシ接続（IAM認証） |
| `scripts/rollback.sh` | Blueの前リビジョンにトラフィック切り替え |
