# Job Recommender

GitHubプロファイルを分析し、最適な求人をAIがレコメンドするWebアプリケーション。

## 概要

GitHubユーザー名を入力するだけで、リポジトリから技術スタック・得意領域を自動分析し、マッチする求人を提案します。

### 主な機能

1. **GitHubプロファイル分析** - リポジトリ、使用言語、READMEから開発者の技術力を評価
2. **AIプロファイル生成** - 採用担当者目線でスキル・強み・適性を言語化
3. **求人検索・マッチング** - Perplexity AIがWeb検索で求人を発見し、マッチ理由とソースを提示

## アーキテクチャ

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GitHub    │────▶│  Vertex AI  │────▶│  Perplexity │
│     API     │     │  (Gemini)   │     │     AI      │
└─────────────┘     └─────────────┘     └─────────────┘
   リポジトリ取得      プロファイル生成     求人検索+マッチング
```

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| Frontend | Streamlit |
| AI/LLM | Vertex AI (Gemini 2.5 Flash) |
| 求人検索 | Perplexity AI (Sonar Pro) |
| インフラ | GCP (Cloud Run + Load Balancer + IAP) |
| IaC | Terraform |
| 認証 | Identity-Aware Proxy (IAP) |

## 工夫点

### 1. コスト最適化
- **Gemini 2.5 Flash** を採用（GPT-4oの約1/10のコスト）
- 1ユーザーあたり約0.5円未満で分析可能

### 2. セキュリティ
- **IAP認証** によりアプリ全体を保護
- シークレットは **Secret Manager** で一元管理（Terraformでは参照のみ）
- Cloud Runは **Internal Load Balancer** 経由のみアクセス可能

### 3. AIの効率的な活用
- **Vertex AI (Gemini)**: GitHubデータからプロファイル生成
- **Perplexity AI**: Web検索 + マッチング分析を1回のAPI呼び出しで完結

### 4. Infrastructure as Code
- Terraform で全インフラをコード化
- Secret Manager の既存シークレットを参照する設計（機密情報をコードに含めない）

## セットアップ

### 必要条件

- Python 3.11+
- uv
- GCP プロジェクト
- Terraform 1.6+

### シークレット設定

Secret Manager に以下のシークレットを作成:

```bash
# GitHub Personal Access Token
gcloud secrets create github_token --replication-policy="automatic"
echo -n "ghp_xxxxx" | gcloud secrets versions add github_token --data-file=-

# Perplexity API Key
gcloud secrets create perplexity_api_key --replication-policy="automatic"
echo -n "pplx-xxxxx" | gcloud secrets versions add perplexity_api_key --data-file=-
```

### ローカル実行

```bash
# 依存関係インストール
uv sync

# GCP 認証（未認証の場合のみ実行される）
./scripts/load-env.sh

# 環境変数設定（.env.local を作成）
cp .env.local.example .env.local
# .env.local を編集して各種APIキーを設定

# 起動
uv run streamlit run app.py
# http://localhost:8501
```

### デプロイ

```bash
# Docker イメージビルド & プッシュ
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/${PROJECT_ID}/job-recommender/app:latest

# Terraform 適用
cd terraform
terraform init
terraform plan
terraform apply
```

## ディレクトリ構成

```
.
├── app.py                 # Streamlit エントリーポイント
├── services/
│   ├── github.py          # GitHub API連携
│   ├── profile.py         # プロファイル生成
│   └── research.py        # Perplexity AI 求人検索+マッチング
├── scripts/
│   └── load-env.sh        # GCP認証スクリプト
├── terraform/             # インフラ定義
│   ├── main.tf            # Cloud Run, Secret Manager, IAM
│   ├── load_balancer.tf   # LB, IAP, SSL証明書
│   └── variables.tf       # 変数定義
├── updates/               # 開発日誌
├── Dockerfile
├── pyproject.toml
└── README.md
```

## 開発日誌

日々の作業内容と学びを記録しています。

<details>
<summary>日誌一覧</summary>

- [2026-01-12](./updates/2026-01-12.md)
- [2026-01-11](./updates/2026-01-11.md)
- [2026-01-09](./updates/2026-01-09.md)
- [2026-01-03](./updates/2026-01-03.md)
- [2026-01-01](./updates/2026-01-01.md)
- [2025-12-31](./updates/2025-12-31.md)
- [2025-12-28](./updates/2025-12-28.md)
- [2025-12-27](./updates/2025-12-27.md)
- [2025-12-25](./updates/2025-12-25.md)
- [2025-12-24](./updates/2025-12-24.md)
- [2025-12-17](./updates/2025-12-17.md)
- [2025-12-09](./updates/2025-12-09.md)
- [2025-12-07](./updates/2025-12-07.md)
- [2025-12-06](./updates/2025-12-06.md)

</details>

## ライセンス

MIT
