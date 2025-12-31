#!/bin/bash
# GCP 認証スクリプト
# 未認証の場合のみログインを実行

set -e

# 認証済みかチェック、未認証の場合のみログイン
if ! gcloud auth print-access-token &>/dev/null; then
    echo "gcloud auth login..."
    gcloud auth login
else
    echo "gcloud auth: already authenticated"
fi

if ! gcloud auth application-default print-access-token &>/dev/null; then
    echo "gcloud auth application-default login..."
    gcloud auth application-default login
else
    echo "gcloud ADC: already authenticated"
fi

echo "Done."
