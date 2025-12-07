#!/bin/bash
# ローカル開発用起動スクリプト
# Secret Manager から認証情報を取得して Streamlit を起動

set -e

# gcloud から設定を取得
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
LOCATION=$(gcloud config get-value compute/region 2>/dev/null)

# 未設定の場合はエラー
if [ -z "$PROJECT_ID" ]; then
    echo "Error: gcloud project が設定されていません"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

# リージョンが未設定の場合はデフォルト値
LOCATION="${LOCATION:-asia-northeast1}"

echo "Project: $PROJECT_ID"
echo "Location: $LOCATION"
echo ""

# Secret Manager から認証情報を取得
echo "Fetching secrets from Secret Manager..."

export GITHUB_TOKEN=$(gcloud secrets versions access latest --secret="github_token" --project="$PROJECT_ID" 2>/dev/null) || {
    echo "Error: github_token シークレットの取得に失敗しました"
    echo "シークレットが存在するか確認: gcloud secrets list --project=$PROJECT_ID"
    exit 1
}

export SERPAPI_API_KEY=$(gcloud secrets versions access latest --secret="serp_api_key" --project="$PROJECT_ID" 2>/dev/null) || {
    echo "Error: serp_api_key シークレットの取得に失敗しました"
    exit 1
}

export GCP_PROJECT_ID="$PROJECT_ID"
export GCP_LOCATION="$LOCATION"

echo "Secrets loaded successfully"
echo ""

# Streamlit 起動
echo "Starting Streamlit..."
poetry run streamlit run app.py "$@"
