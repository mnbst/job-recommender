"""料金プランページ."""

import streamlit as st

st.title("料金プラン")

st.markdown("""
Job Recommenderでは、クレジット制を採用しています。
プロファイル生成・求人検索・追加表示で共通のクレジットを消費します。
""")

# 無料プラン
st.header("無料プラン")

with st.container(border=True):
    st.metric("初回付与", "5クレジット")
    st.caption("新規登録時に付与されます")

st.divider()

# クレジット消費
st.header("クレジット消費")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.subheader("プロファイル生成")
        st.metric("消費", "1クレジット")
        st.caption("GitHubリポジトリ分析")

with col2:
    with st.container(border=True):
        st.subheader("求人検索")
        st.metric("消費", "1クレジット")
        st.caption("3件の求人を表示")

with col3:
    with st.container(border=True):
        st.subheader("求人追加表示")
        st.metric("消費", "1クレジット")
        st.caption("最大3件を追加表示")

st.divider()

# 有料パック
st.header("クレジット購入")

pack_col1, pack_col2, pack_col3 = st.columns(3)

with pack_col1:
    with st.container(border=True):
        st.subheader("スターター")
        st.metric("5クレジット", "¥500")
        st.caption("¥100 / クレジット")
        st.button("購入", key="buy_starter", disabled=True, use_container_width=True)

with pack_col2:
    with st.container(border=True):
        st.subheader("スタンダード")
        st.metric("15クレジット", "¥1,200")
        st.caption("¥80 / クレジット")
        st.button("購入", key="buy_standard", disabled=True, use_container_width=True)

with pack_col3:
    with st.container(border=True):
        st.subheader("プレミアム")
        st.metric("30クレジット", "¥1,800")
        st.caption("¥60 / クレジット")
        st.button("購入", key="buy_premium", disabled=True, use_container_width=True)

st.info("決済機能は準備中です")
