# Job Recommender

GitHubプロファイルを分析し、最適な求人をAIがレコメンドするWebアプリケーション。

## 概要

GitHubユーザー名を入力するだけで、リポジトリから技術スタック・得意領域を自動分析し、マッチする求人を提案します。

### 主な機能

1. **GitHubプロファイル分析** - リポジトリ、使用言語、READMEから開発者の技術力を評価
2. **AIプロファイル生成** - 採用担当者目線でスキル・強み・適性を言語化
3. **求人検索** - プロファイルに基づいてGoogle Jobsから求人を検索
4. **マッチング分析** - 各求人との適合度をAIがスコアリング・理由付け

## アーキテクチャ

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GitHub    │────▶│  Vertex AI  │────▶│   SerpAPI   │────▶│  Vertex AI  │
│     API     │     │  (Gemini)   │     │ Google Jobs │     │  (Gemini)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
   リポジトリ取得      プロファイル生成        求人検索          マッチング分析
```

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| Frontend | Streamlit |
| AI/LLM | Vertex AI (Gemini 2.5 Flash) |
| 求人検索 | SerpAPI (Google Jobs API) |
| インフラ | GCP (Cloud Run + Load Balancer + IAP) |
| IaC | Terraform |
| 認証 | Identity-Aware Proxy (IAP) |

## 工夫点

### 1. コスト最適化
- **Gemini 2.5 Flash** を採用（GPT-4oの約1/10のコスト）
- 1ユーザーあたり約0.5円未満で分析可能
- SerpAPI無料枠（月100検索）で小規模運用可能

### 2. セキュリティ
- **IAP認証** によりアプリ全体を保護
- シークレットは **Secret Manager** で一元管理（Terraformでは参照のみ）
- Cloud Runは **Internal Load Balancer** 経由のみアクセス可能

### 3. AIの2段階活用
- **第1段階**: GitHubデータからプロファイル生成（構造化された評価を生成）
- **第2段階**: 求人とのマッチング分析（スコアリング + 理由の説明）

### 4. Infrastructure as Code
- Terraform で全インフラをコード化
- Secret Manager の既存シークレットを参照する設計（機密情報をコードに含めない）

## セットアップ

### 必要条件

- Python 3.11+
- Poetry
- GCP プロジェクト
- Terraform 1.6+

### シークレット設定

Secret Manager に以下のシークレットを作成:

```bash
# GitHub Personal Access Token
gcloud secrets create github_token --replication-policy="automatic"
echo -n "ghp_xxxxx" | gcloud secrets versions add github_token --data-file=-

# SerpAPI API Key
gcloud secrets create serp_api_key --replication-policy="automatic"
echo -n "xxxxx" | gcloud secrets versions add serp_api_key --data-file=-
```

### ローカル実行

```bash
# 依存関係インストール
poetry install

# GCP 認証（初回のみ）
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# 環境変数読み込み
source ./scripts/load-env.sh

# 起動
poetry run streamlit run app.py
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
│   ├── profile.py         # プロファイル生成 & マッチング分析
│   └── research.py        # SerpAPI 求人検索
├── scripts/
│   └── load-env.sh        # 環境変数読み込みスクリプト
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

- [2025-12-09](./updates/2025-12-09.md)
- [2025-12-07](./updates/2025-12-07.md)
- [2025-12-06](./updates/2025-12-06.md)

</details>

## ライセンス

MIT
