---
name: project-architecture
description: プロジェクト構造とデータフロー。実装、修正、デバッグ時に参照。GitHub API、Vertex AI、Perplexity AI連携。
allowed-tools: Read, Grep, Glob
---

# Project Architecture

## Data Flow

```
1. github.py   → GitHubからリポジトリ情報取得 → list[RepoInfo]
2. profile.py  → Geminiでプロファイル生成    → dict
3. research.py → Perplexity AIで求人検索+マッチング分析 → JobSearchResult
```

## Infrastructure

```
Internet → Cloud LB (HTTPS) → Serverless NEG → Cloud Run (public)
                                                     ↓
                                               VPC Connector → VPC
                                                     ↓
                                               Vertex AI / Perplexity AI
```

認証: GitHub OAuth（アプリケーションレベル）

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
| `google_cloud_run_v2_service` | 公開ingress、Streamlitコンテナ |
| `google_compute_backend_service` | NEG接続 |
| `google_compute_region_network_endpoint_group` | Serverless NEG |
| `google_vpc_access_connector` | VPC接続 (10.8.0.0/28) |
| `google_artifact_registry_repository` | Dockerイメージ保存 |
| `google_cloudbuild_trigger` | main Push時の自動ビルド |

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
