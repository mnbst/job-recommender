---
name: streamlit-redirects
description: Streamlitで外部URLへ同一タブ遷移したい時の手順と、st.markdownのリダイレクトが本番で効かない原因/対策。
user-invocable: false
allowed-tools: Read, Grep, Glob, Bash
---

# Streamlit Redirects

## Markdown redirectが失敗しやすい理由
- `st.markdown(..., unsafe_allow_html=True)` はDOMPurifyで`<meta>`や`<script>`が除去されることがある
- `<meta http-equiv="refresh">`は`<head>`配下でないと効かないブラウザが多い
- 本番環境のCSPやReact再描画で副作用が無視されることがある

## 推奨ルート
| 目的 | 方法 |
| --- | --- |
| アプリ内ページ遷移 | `st.switch_page("pages/xxx.py")` |
| 外部URL・同一タブ | components.v2の自作リダイレクト |
| 外部URL・新規タブ | `st.link_button` / `st.page_link` |

## このリポジトリの実装
- コンポーネント: `services/components/redirect`
- JS: `window.parent.location.href = url`

```python
from services.components.redirect import redirect

if st.button("トップへ戻る", type="primary"):
    redirect("https://job-recommender.com/")
```

## クリックが2回必要になる場合
- **原因**: v2コンポーネントの描画タイミングが遅く、ボタン押下と同一レンダリング内でJSが走らない
- **対策**: クリック状態を`st.session_state`に保持して次のレンダリングでも`redirect()`を呼ぶ

```python
from services.components.redirect import redirect

if st.button("トップへ戻る", type="tertiary"):
    st.session_state["redirect_to_lp"] = True
if st.session_state.get("redirect_to_lp"):
    redirect("https://job-recommender.com/")
```

## リダイレクト時のCookie削除

`redirect()`には`delete_cookie`オプションがある：

```python
redirect("https://example.com/", delete_cookie=True)
```

### なぜCookieManagerではなくredirect内で削除するか

| 方法 | 動作 |
|------|------|
| `CookieManager.delete()` | コンポーネントレンダリング → 削除 → 次rerunで反映 |
| `redirect(..., delete_cookie=True)` | 削除 → 即リダイレクト（同期的） |

`CookieManager.delete()` → `redirect()` の順だと、Cookie削除完了前にリダイレクトが実行される可能性がある。`redirect.js`内で同期的に削除することで確実性を担保。

CookieManagerに統一する場合は2段階処理が必要（UX的にちらつく可能性あり）：
```python
cookie_manager.delete("job_recommender_session")
st.rerun()  # 削除を反映
# 次のrerunでリダイレクト
```

## 追加調査チェックリスト
- DevToolsで`<meta>`がDOMに残っているか確認
- Response headerの`Content-Security-Policy`で`script-src`/`frame-ancestors`を確認
- 生成HTMLが`<head>`ではなく`<body>`に出ていないか確認
