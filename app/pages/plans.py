"""料金プランページ."""

import streamlit as st

from app.ui.plans import render_plan_card

st.title("料金プラン")

st.markdown("""
Job Recommenderでは、クレジット制を採用しています。
プロファイル生成・求人検索・追加表示で共通のクレジットを消費します。
""")

# 無料プラン
st.header("無料プラン")

render_plan_card(
    None,
    "初回付与",
    "5クレジット",
    caption="新規登録時に付与されます",
)

st.divider()

# クレジット消費
st.header("クレジット消費")

col1, col2, col3 = st.columns(3)

with col1:
    render_plan_card(
        "プロファイル生成",
        "消費",
        "1クレジット",
        caption="GitHubリポジトリ分析",
    )

with col2:
    render_plan_card(
        "求人検索",
        "消費",
        "1クレジット",
        caption="3件の求人を表示",
    )

with col3:
    render_plan_card(
        "求人追加表示",
        "消費",
        "1クレジット",
        caption="最大3件を追加表示",
    )

st.divider()

# 有料パック
st.header("クレジット購入")

pack_col1, pack_col2, pack_col3 = st.columns(3)

with pack_col1:
    render_plan_card(
        "スターター",
        "5クレジット",
        "¥500",
        caption="¥100 / クレジット",
        button_label="購入",
        button_key="buy_starter",
        button_disabled=True,
    )

with pack_col2:
    render_plan_card(
        "スタンダード",
        "15クレジット",
        "¥1,200",
        caption="¥80 / クレジット",
        button_label="購入",
        button_key="buy_standard",
        button_disabled=True,
    )

with pack_col3:
    render_plan_card(
        "プレミアム",
        "30クレジット",
        "¥1,800",
        caption="¥60 / クレジット",
        button_label="購入",
        button_key="buy_premium",
        button_disabled=True,
    )

st.info("決済機能は準備中です")
