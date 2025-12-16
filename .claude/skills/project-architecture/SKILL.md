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
Internet → Cloud LB (HTTPS) → IAP → Serverless NEG → Cloud Run (private)
                                                          ↓
                                                    VPC Connector → VPC
                                                          ↓
                                                    Vertex AI / Perplexity AI
```

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI、エントリーポイント |
| `services/github.py` | PyGithub、RepoInfoデータクラス |
| `services/profile.py` | Vertex AI初期化、プロファイル生成 |
| `services/research.py` | Perplexity AI、JobRecommendationデータクラス |
| `terraform/` | インフラ定義 (Cloud Run + LB + IAP) |

## Key Resources (Terraform)

| Resource | Purpose |
|----------|---------|
| `google_cloud_run_v2_service` | プライベートingress、Streamlitコンテナ |
| `google_compute_backend_service` | IAP有効、NEG接続 |
| `google_compute_region_network_endpoint_group` | Serverless NEG |
| `google_vpc_access_connector` | VPC接続 (10.8.0.0/28) |
| `google_artifact_registry_repository` | Dockerイメージ保存 |
