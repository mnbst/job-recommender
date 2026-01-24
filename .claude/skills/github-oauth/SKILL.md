---
name: github-oauth
description: GitHub OAuth認証の仕様。認証フロー、トークン管理、セッション永続化に関する情報。
user-invocable: false
allowed-tools: Read, Grep, Glob
---

# GitHub OAuth

## OAuth App vs GitHub App

| 項目 | OAuth App (このプロジェクト) | GitHub App |
|------|------------------------------|------------|
| トークン有効期限 | **無期限** | 8時間 |
| リフレッシュトークン | なし | あり |
| 無効化条件 | ユーザー取り消し/App削除/revoke API | 期限切れ/取り消し |

## 認証フロー

```
1. ユーザー → GitHub認証ページにリダイレクト
2. GitHub → コールバックURLに `?code=xxx` 付きでリダイレクト
3. `code` をアクセストークンに交換（exchange_code_for_token）
4. セッションをFirestoreに保存、session_idをCookieに設定（7日間有効）
5. 次回アクセス時: Cookieからsession_id取得 → Firestoreからセッション復元
```

## セッション永続化

| 保存先 | 内容 | 有効期限 |
|--------|------|----------|
| Cookie | session_id (UUID) | 7日間 |
| Firestore `sessions` | user_id, access_token, user_data, last_accessed_at | 7日間（last_accessed_at基準） |

### Cookie取得のretry

CookieManagerは非同期で動作するため、初回呼び出しでNoneが返る可能性あり。
`get_session_cookie()`で最大3回retryし、取得できなければ未ログインとして扱う。

## Key Files

| File | Purpose |
|------|---------|
| `services/auth.py` | OAuth認証、トークン交換、セッション復元・永続化 |
| `services/session.py` | Firestore/Cookieセッション管理 |

## トークン無効化条件

- ユーザーがGitHub設定からアプリのアクセスを取り消し
- OAuth App自体が削除された
- `DELETE /applications/{client_id}/token` で明示的に無効化
- **7日間アクセスなし** → Firestoreセッション削除
