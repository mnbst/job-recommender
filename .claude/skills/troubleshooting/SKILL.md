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

### 2. LB経由で403 Forbidden
- **原因**: Cloud Runのinvoker権限がない
- **確認**: 現在のIAM設定を確認
```bash
gcloud run services get-iam-policy job-recommender --region=asia-northeast1
```
- **対処**: 一般公開する場合は`allUsers`にinvoker権限を付与
```bash
gcloud run services add-iam-policy-binding job-recommender \
  --region=asia-northeast1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

### 3. Cloud Runにアクセスできない (502/503)
- **原因**: LBからCloud Runへの接続問題、NEG設定ミス
- **確認**: Backend ServiceとNEGの設定
```bash
gcloud compute backend-services describe job-recommender-backend --global
```
- **対処**: terraform applyで権限付与、または再デプロイ

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

### 9. Secret Manager更新後も反映されない
- **原因**: Cloud Runは起動時にシークレットを読み込むため、`version = "latest"`でも再デプロイが必要
- **対処**:
```bash
# 新しいリビジョンを強制デプロイ
gcloud run deploy job-recommender --region=asia-northeast1 \
  --image=asia-northeast1-docker.pkg.dev/${PROJECT_ID}/job-recommender/app:latest
```

### 10. Green環境にアクセスできない (403)
- **原因**: Green環境はIAM制限付き
- **確認**:
```bash
gcloud run services get-iam-policy job-recommender-green --region=asia-northeast1
```
- **対処**: `terraform.tfvars`で`cloud_run_invoker_members`にユーザーを追加
```hcl
cloud_run_invoker_members = ["user:your-email@gmail.com"]
```

### 11. Green環境でOAuth認証が失敗
- **原因**: Green用のOAuth Appが未設定、または callback URLが不正
- **確認**: GitHub OAuth App設定で callback URL が `/green` を含むか
- **対処**:
  1. GitHub Developer Settings で Green用 OAuth App 作成
  2. Callback URL: `https://<LB_IP>.nip.io/green`
  3. Secret Manager に登録:
```bash
echo -n "GREEN_CLIENT_ID" | gcloud secrets create green_github_oauth_client_id --data-file=-
echo -n "GREEN_CLIENT_SECRET" | gcloud secrets create green_github_oauth_client_secret --data-file=-
```

### 12. デプロイ後に問題発生、ロールバックしたい
- **対処**: 前リビジョンにトラフィックを切り替え
```bash
./scripts/rollback.sh
# または手動で
gcloud run services update-traffic job-recommender \
  --region=asia-northeast1 \
  --to-revisions=<previous-revision>=100
```

## Useful Commands

```bash
# Cloud Runログ (Blue)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=job-recommender" --limit=50

# Cloud Runログ (Green)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=job-recommender-green" --limit=50

# LBログ
gcloud logging read "resource.type=http_load_balancer" --limit=50

# Green環境にローカルプロキシ
./scripts/proxy-green.sh  # http://localhost:8080 でアクセス

# ロールバック
./scripts/rollback.sh

# リビジョン一覧確認
gcloud run revisions list --service=job-recommender --region=asia-northeast1

# ローカルテスト
uv run streamlit run app.py
```
