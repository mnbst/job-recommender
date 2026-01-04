"""クレジット制説明ページ."""

import streamlit as st

st.title("クレジット制について")

st.markdown("""
Job Recommenderでは、クレジット制を採用しています。
新規登録時に初期クレジットが付与され、使用するごとに消費されます。
""")

# 初期クレジット
st.header("初期クレジット")

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("プロファイル生成", "3回分")
    with col2:
        st.metric("求人検索", "3回分")

st.caption("クレジットがなくなった場合は、追加購入が可能です（準備中）")

st.divider()

# 機能詳細
st.header("機能と消費クレジット")

with st.container(border=True):
    st.subheader("プロファイル生成")
    st.markdown("""
GitHubのリポジトリを分析し、技術スタック・スキル評価・得意領域などを自動生成します。

- 直近の公開リポジトリを分析
- 使用言語・フレームワーク・インフラを抽出
- 採用担当者目線での総合評価を生成
    """)
    st.info("消費: 1クレジット / 回")

with st.container(border=True):
    st.subheader("求人検索")
    st.markdown("""
生成したプロファイルと希望条件に基づいて、マッチする求人を検索します。

- Perplexity AIによるリアルタイム検索
- マッチング理由とソースを表示
- 勤務地・年収・働き方などでフィルタリング
    """)
    st.info("消費: 1クレジット / 回")
