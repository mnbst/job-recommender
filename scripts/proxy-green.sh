#!/bin/bash
# Green環境にローカルからプロキシ経由でアクセス
#
# Usage: ./scripts/proxy-green.sh [port] [region]
#
# ブラウザで http://localhost:8080 を開いてgreen環境を検証

set -euo pipefail

PORT="${1:-8080}"
REGION="${2:-asia-northeast1}"
SERVICE_NAME="job-recommender-green"

echo "Starting proxy to green environment..."
echo "Access at: http://localhost:$PORT"
echo "Press Ctrl+C to stop"
echo ""

gcloud run services proxy "$SERVICE_NAME" \
  --region="$REGION" \
  --port="$PORT"
