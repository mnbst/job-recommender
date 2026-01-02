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
- [ ] 無料プラン制限実装
  - 求人表示: 3件まで
  - 分析回数: 1日3回まで
- [ ] 有料プラン機能
  - 無制限求人表示
  - 詳細スキル分析
  - 履歴書自動生成

### Step 3: 決済基盤（Stripe）
- [ ] Stripe アカウント作成・設定
- [ ] Checkout Session 実装
- [ ] Webhook で支払い確認
- [ ] クレジット購入（回数制）
  - 5回パック: ¥500（¥100/回）
  - 15回パック: ¥1,200（¥80/回）
  - 30回パック: ¥2,000（¥67/回）
- [ ] ヘビーユーザー向け月額プラン: ¥980/月（無制限）

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

### プロファイル生成改善
- [ ] モデル変更検討（gemini-2.5-flash → claude-opus-4 or claude-sonnet-4）
  - コード理解・設計力評価の精度向上
  - Vertex AI Model Garden経由で実装

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

- [ ] 一般公開対応（IAP削除）
  - load_balancer.tf: `iap` ブロック削除
  - load_balancer.tf: `google_iap_web_backend_service_iam_binding` 削除
  - main.tf: `iap_invoker` IAM バインディング削除
  - variables.tf: `iap_oauth2_client_id`, `iap_oauth2_client_secret`, `authorized_members` 削除
  - terraform.tfvars: IAP設定行削除
  - main.tf: `allUsers` に `roles/run.invoker` 付与（LB経由のみ許可）
  - CLAUDE.md 更新
- [ ] カスタムドメイン取得・設定
  - ドメイン取得（Google Domains / Cloudflare など）
  - Cloud DNS ゾーン作成
  - SSL証明書（Google-managed）設定
  - Load Balancer にドメイン紐付け
  - GitHub OAuth App の callback URL 更新
- [ ] terraform.tfvars の機密情報保護
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
