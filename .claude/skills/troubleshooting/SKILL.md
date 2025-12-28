---
name: troubleshooting
description: 障害対応・デバッグ時の解決策。エラー、アクセス不可、IAP認証失敗、API制限などの問題発生時に参照。
allowed-tools: Read, Grep, Glob, Bash
---

# Troubleshooting Guide

## Common Issues

### 1. SSL証明書がプロビジョニングされない
- **原因**: DNS未設定 or 時間不足（発行まで15〜60分）
- **確認**:
```bash
# 証明書の状態確認
gcloud compute ssl-certificates describe job-recommender-cert-nipio --global \
  --format="value(managed.status,managed.domainStatus)"
# PROVISIONING=発行中, ACTIVE=完了, FAILED_NOT_VISIBLE=DNS検証失敗
```
- **対処**: ACTIVEになるまで待機。nip.ioドメインならDNS設定不要

### 2. IAP認証失敗 (403)
- **原因**: ユーザーがauthorized_membersにない
- **確認**: terraform.tfvarsの`authorized_members`を確認
- **対処**: Google Groupにユーザーを追加、terraform apply

### 3. Cloud Runにアクセスできない (502/503)
- **原因**: IAP SAがrun.invokerを持っていない
- **確認**: IAP SAがプロビジョニングされているか
```bash
gcloud beta services identity create --service=iap.googleapis.com --project=PROJECT_ID
```
- **対処**: terraform applyで権限付与

### 4. Streamlitが起動しない
- **原因**: ポート設定ミス、依存関係不足
- **確認**: container_portが8501か、Dockerfileの起動コマンド
- **対処**: `--server.port=8501 --server.address=0.0.0.0`を指定

### 5. Vertex AI エラー
- **原因**: 認証エラー、API未有効化
- **確認**:
```bash
gcloud services list --enabled | grep aiplatform
```
- **対処**: APIを有効化、サービスアカウント権限を確認

### 6. GitHub API レート制限
- **原因**: GITHUB_TOKEN未設定 or 無効
- **確認**: Secret Managerの`github_token`を確認
```bash
gcloud secrets versions access latest --secret=github_token
```
- **対処**: 新しいPATを生成してSecret Managerを更新

### 7. Perplexity API エラー
- **原因**: PERPLEXITY_API_KEY未設定 or クォータ超過
- **確認**: Secret Managerの`perplexity_api_key`を確認
```bash
gcloud secrets versions access latest --secret=perplexity_api_key
```
- **対処**: https://www.perplexity.ai でAPIキー確認、クォータ確認
- **注意**: 初回JSON Schemaリクエストは10-30秒かかる可能性あり

### 8. Terraform初回: Cloud Runイメージが見つからない
- **原因**: Artifact Registryにイメージがない状態でterraform apply
- **エラー**: `Image '...app:latest' not found`
- **対処**: 先にイメージをビルド&プッシュ
```bash
# 1. Artifact Registryだけ先に作成
terraform apply -target=google_artifact_registry_repository.app

# 2. イメージをビルド&プッシュ
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/${PROJECT_ID}/job-recommender/app:latest

# 3. 残りのリソースを作成
terraform apply
```

## Useful Commands

```bash
# Cloud Runログ
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# LBログ
gcloud logging read "resource.type=http_load_balancer" --limit=50

# IAP設定確認
gcloud iap web get-iam-policy --resource-type=backend-services --service=<backend-name>

# ローカルテスト
uv run streamlit run app.py
```
