"""プラン・制限説明ページ."""

import streamlit as st

st.set_page_config(
    page_title="プラン - Job Recommender",
    page_icon="📋",
    layout="wide",
)

st.title("プラン・利用制限")

st.markdown("""
Job Recommenderでは、クレジット制を採用しています。
新規登録時に初期クレジットが付与され、使用するごとに消費されます。
""")

# プラン比較表
st.header("プラン比較")

col1, col2 = st.columns(2)

with col1:
    st.subheader("無料プラン")
    st.markdown("""
    **初期クレジット**
    - プロファイル生成: 3回分
    - 求人検索: 3回分

    **求人表示**
    - 1回の検索で3件まで表示

    **補充**
    - クレジット購入で追加可能（準備中）
    """)

with col2:
    st.subheader("プレミアムプラン")
    st.markdown("""
    **利用制限**
    - プロファイル生成: 無制限
    - 求人検索: 無制限

    **求人表示**
    - すべての求人を表示
    """)
    st.info("プレミアムプランは準備中です")

st.divider()

# 詳細説明
st.header("機能詳細")

st.subheader("プロファイル生成")
st.markdown("""
GitHubのリポジトリを分析し、技術スタック・スキル評価・得意領域などを自動生成します。

- 直近の公開リポジトリを分析
- 使用言語・フレームワーク・インフラを抽出
- 採用担当者目線での総合評価を生成

**消費クレジット:** 1回につき1クレジット
""")

st.subheader("求人検索")
st.markdown("""
生成したプロファイルと希望条件に基づいて、マッチする求人を検索します。

- Perplexity AIによるリアルタイム検索
- マッチング理由とソースを表示
- 勤務地・年収・働き方などでフィルタリング

**消費クレジット:** 1回につき1クレジット
""")
