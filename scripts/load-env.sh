#!/bin/bash
# VS Code デバッグ用環境変数ロードスクリプト
# Secret Manager から認証情報を取得して .env.local に書き出す

set -e
gcloud auth login
gcloud auth application-default login 

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# gcloud から設定を取得
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
LOCATION=$(gcloud config get-value compute/region 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "Error: gcloud project が設定されていません"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

LOCATION="${LOCATION:-asia-northeast1}"

echo "Project: $PROJECT_ID"
echo "Location: $LOCATION"

# Secret Manager から認証情報を取得
echo "Fetching secrets from Secret Manager..."

GITHUB_TOKEN=$(gcloud secrets versions access latest --secret="github_token" --project="$PROJECT_ID" 2>/dev/null) || {
    echo "Error: github_token シークレットの取得に失敗しました"
    exit 1
}

PERPLEXITY_API_KEY=$(gcloud secrets versions access latest --secret="perplexity_api_key" --project="$PROJECT_ID") || {
    echo "Error: perplexity_api_key シークレットの取得に失敗しました"
    exit 1
}

# .env.local に書き出し（VS Code envFile形式）
cat > "$PROJECT_ROOT/.env.local" << EOF
GITHUB_TOKEN=${GITHUB_TOKEN}
PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
GCP_PROJECT_ID=${PROJECT_ID}
GCP_LOCATION=${LOCATION}
EOF

echo "Environment saved to .env.local"
