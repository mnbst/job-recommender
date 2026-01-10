#!/bin/bash
# 前のリビジョンにロールバック
#
# Usage: ./scripts/rollback.sh [region]
#
# 現在のトラフィックを受けているリビジョンの1つ前にロールバック

set -euo pipefail

REGION="${1:-asia-northeast1}"
SERVICE_NAME="job-recommender"

echo "Fetching revisions..."

# リビジョン一覧を取得（最新順）
REVISIONS=$(gcloud run revisions list \
  --service="$SERVICE_NAME" \
  --region="$REGION" \
  --format='value(name)' \
  --limit=5)

if [ -z "$REVISIONS" ]; then
  echo "Error: No revisions found"
  exit 1
fi

# 2番目のリビジョン（前のバージョン）を取得
PREV_REVISION=$(echo "$REVISIONS" | sed -n '2p')

if [ -z "$PREV_REVISION" ]; then
  echo "Error: No previous revision found"
  exit 1
fi

echo "Rolling back to: $PREV_REVISION"

# 前のリビジョンにトラフィック100%
gcloud run services update-traffic "$SERVICE_NAME" \
  --region="$REGION" \
  --to-revisions="$PREV_REVISION=100"

echo "Done. Rolled back to $PREV_REVISION"
