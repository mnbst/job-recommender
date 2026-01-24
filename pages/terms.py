"""利用規約ページ."""

import streamlit as st

from components.legal import (
    render_page_header,
    render_section,
    render_section_divider,
)

render_page_header("利用規約", "2025年1月")

# サービス概要
render_section("1. サービス概要")

st.markdown("""
本サービスは、GitHubの公開リポジトリ情報を分析し、
AIを活用して求人情報を提案するサービスです。
""")

render_section_divider()

# 免責事項
render_section("2. 免責事項")

with st.container(border=True):
    st.subheader("AI生成コンテンツについて")
    st.markdown("""
    - プロファイル分析結果はAI（Google Gemini）により生成されます
    - 求人情報はAI（Perplexity AI）による検索結果です
    - **生成内容の正確性・完全性は保証されません**
    - 重要な判断の際は、必ずご自身で情報を確認してください
    """)

with st.container(border=True):
    st.subheader("求人情報について")
    st.markdown("""
    - 表示される求人情報は外部サイトからの検索結果です
    - 求人の存在・内容・条件の正確性は保証されません
    - 応募の際は、必ず掲載元サイトで最新情報をご確認ください
    """)

with st.container(border=True):
    st.subheader("サービス利用について")
    st.markdown("""
    - 本サービスの利用により生じた損害について、運営者は責任を負いません
    - サービスの内容は予告なく変更・終了する場合があります
    """)

render_section_divider()

# クレジット制度
render_section("3. クレジット制度")

st.markdown("""
- 新規登録時に無料クレジットが付与されます
- クレジットは各機能の利用時に消費されます
- 購入済みクレジットの払い戻しはできません
- クレジットの有効期限はありません
""")

st.info("決済機能は現在準備中です")

render_section_divider()

# 禁止事項
render_section("4. 禁止事項")

st.markdown("""
以下の行為を禁止します。

- サービスへの不正アクセス・攻撃行為
- 自動化ツールによる大量リクエスト
- 取得した情報の商用利用・再配布
- 他のユーザーになりすます行為
- その他、運営者が不適切と判断する行為
""")

render_section_divider()

# 知的財産
render_section("5. 知的財産")

st.markdown("""
- ユーザーのGitHubリポジトリの著作権はユーザーに帰属します
- AI生成コンテンツの利用権はユーザーに付与されます
- サービス自体の著作権は運営者に帰属します
""")

render_section_divider()

# 準拠法
render_section("6. 準拠法")

st.markdown("""
本規約は日本法に準拠し、解釈されるものとします。
""")
