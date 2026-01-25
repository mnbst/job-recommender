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

## 追加調査チェックリスト
- DevToolsで`<meta>`がDOMに残っているか確認
- Response headerの`Content-Security-Policy`で`script-src`/`frame-ancestors`を確認
- 生成HTMLが`<head>`ではなく`<body>`に出ていないか確認
