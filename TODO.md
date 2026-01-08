# TODO

## Phase 1: マネタイズ基盤（優先）

### Step 1: ユーザー認証
- [x] GitHub OAuth ログイン実装
- [x] ユーザーセッション管理（Streamlit session_state）
- [x] Firestore でユーザー情報保存
- [x] セッション永続化（JWT + Firestore ハイブリッド）
  - JWT Cookie: ユーザーID・ログイン名のみ
  - Firestore: GitHubアクセストークン保存
  - 有効期限1日、Secret Manager に JWT_SECRET 追加済み

### Step 2: フリーミアム機能制限
- [x] 共通クレジット制に統合
  - 初回: 5クレジット
  - 補充: なし
- [x] クレジット消費ポイント
  - プロファイル生成: 1クレジット
  - 求人検索（初回3件）: 1クレジット
  - 求人追加表示（+3件）: 1クレジット

### Step 3: 決済基盤（Stripe）
- [ ] Stripe アカウント作成・設定
- [ ] Checkout Session 実装
- [ ] Webhook で支払い確認
- [ ] 有料パック実装
  - スターター: ¥500 / 5回（¥100/回）
  - スタンダード: ¥1,200 / 15回（¥80/回）
  - プレミアム: ¥1,800 / 30回（¥60/回）

### Step 4: アフィリエイト（並行検討）
- [ ] アフィリエイト提携先調査
  - Green、Wantedly、Findy、Geekly など
- [ ] 求人リンクにアフィリエイトタグ付与
- [ ] クリック・成約トラッキング

---

## Phase 2: 機能拡充

### 分析履歴
- [x] Firestore で分析結果保存（プロファイル・リポジトリキャッシュ）
- [x] ユーザー設定の永続化
- [ ] 過去の分析結果一覧表示
- [ ] 結果の比較機能

### プレミアム機能
- [ ] 詳細スキル分析レポート（PDF出力）
- [ ] 職務経歴書の自動生成
- [ ] 面接対策アドバイス

### リポジトリ絞り込み
- [ ] 分析対象リポジトリの選択機能

### プロファイル生成改善
- [ ] モデル変更検討（gemini-2.5-flash → claude-opus-4 or claude-sonnet-4）
  - コード理解・設計力評価の精度向上
  - Vertex AI Model Garden経由で実装

### 求人詳細ページ取得改善
- [ ] 求人APIの導入検討
  - Jooble API（無料）- 求人アグリゲーター、詳細URL含む
  - SerpAPI（有料$50~/月）- Google Jobs検索、確実性高い
  - Adzuna API（無料枠あり）- UK中心だが日本も一部対応
- [ ] 現状: Perplexityで検索 → 詳細ページ取得が不安定
- [ ] 目標: 企業の募集ページまたは仲介サイトの詳細ページに確実に誘導

### 求人応募サポート
- [ ] 求人へのワンクリック応募
- [ ] 応募状況トラッキング

---

## Phase 3: マーケティング・法務

### マーケティング
- [ ] LP（ランディングページ）作成
- [ ] SEO対策（メタタグ、OGP）
- [ ] SNS展開（Twitter/X、Qiita/Zenn）
- [ ] Google Analytics導入

### 法務
- [ ] 利用規約作成
- [ ] プライバシーポリシー作成
- [ ] 特定商取引法に基づく表記

---

## Phase 4: インフラ改善（後回し）

### ネットワークセキュリティ
- [ ] Cloud Armor 導入（優先度高）
  - WAF（SQLi/XSS防御）- OWASP Top 10 対策
  - レート制限（API乱用・ブルートフォース対策）
  - `google_compute_security_policy` → Backend Service に適用
- [ ] IPアクセス制限（必要に応じて）
  - 特定国/IPレンジのみ許可
- [ ] Bot対策
  - reCAPTCHA Enterprise 統合（Cloud Armor経由）
- [ ] VPC Service Controls（コスト増・複雑化とのトレードオフ）
  - Private Google Access で Vertex AI への内部通信化

### その他インフラ
- [x] 一般公開対応（IAP削除）
- [x] terraform.tfvars の機密情報保護（.gitignoreに追加済み）
- [ ] カスタムドメイン取得・設定
  - ドメイン取得（Google Domains / Cloudflare など）
  - Cloud DNS ゾーン作成
  - SSL証明書（Google-managed）設定
  - Load Balancer にドメイン紐付け
  - GitHub OAuth App の callback URL 更新
- [ ] アラート設定（monitoring.tf）
- [ ] Blue-Green デプロイ対応
- [ ] 構造化ログ実装

---

## 保留: 代替プラン

### B2B（企業向け）
- [ ] GitHubユーザー検索・スカウト機能
- [ ] 候補者リスト作成・エクスポート
- [ ] 月額課金（¥50,000〜/月）

### API提供
- [ ] GitHubプロファイル分析API
- [ ] 求人マッチングAPI
- [ ] 従量課金（¥10/リクエスト）

---

## 完了済み

- [x] Firestore キャッシュ機能（プロファイル・リポジトリ・設定）（2025-12-31）
- [x] ユーザー設定の永続化（2025-12-31）
- [x] GitHub OAuth ログイン実装（2025-12-28）
- [x] ユーザーセッション管理（2025-12-28）
- [x] 求人検索の希望条件機能（JobPreferences）（2025-12-28）
- [x] Cloud Build CI/CD パイプライン構築（2025-12-27）
- [x] GitHub 2nd gen 接続設定（2025-12-27）
- [x] Artifact Registry 自動Push（2025-12-27）
