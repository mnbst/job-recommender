"""プライバシーポリシーページ."""

import streamlit as st

st.title("プライバシーポリシー")

st.markdown("最終更新日: 2025年1月")

st.divider()

# 収集する情報
st.header("1. 収集する情報")

st.markdown("""
本サービスでは、GitHub Appの認可を通じて以下の情報を取得します。
""")

with st.container(border=True):
    st.subheader("GitHub アカウント情報")
    st.markdown("""
    - ユーザーID・ログイン名
    - 表示名・メールアドレス（公開設定時のみ）
    - アバター画像URL
    - 公開リポジトリ情報（名前、説明、使用言語、README等）
    """)
    st.caption("GitHub App権限: Contents（Read-only, Public repositories only）")

st.divider()

# データの保存
st.header("2. データの保存")

st.markdown("取得したデータは Google Cloud Firestore に保存されます。")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("セッション情報")
        st.metric("保存期間", "7日間")
        st.caption("ログイン状態の維持に使用")

with col2:
    with st.container(border=True):
        st.subheader("プロファイル・キャッシュ")
        st.metric("保存期間", "30日間")
        st.caption("分析結果の再利用に使用")

st.divider()

# 第三者サービスへの送信
st.header("3. 第三者サービスへのデータ送信")

st.markdown("""
本サービスでは、機能提供のため以下の第三者サービスにデータを送信します。
""")

with st.container(border=True):
    st.subheader("Google Vertex AI (Gemini)")
    st.markdown("""
    **用途**: プロファイル生成（GitHubリポジトリの分析）

    **送信データ**:
    - リポジトリ名・説明・使用言語
    - README（一部）・ファイル構造
    - 依存関係ファイル・コードサンプル（一部）
    """)

with st.container(border=True):
    st.subheader("Perplexity AI")
    st.markdown("""
    **用途**: 求人検索

    **送信データ**:
    - 生成されたプロファイル（技術スタック、スキル等）
    - 求人検索条件（勤務地、職種等）
    """)

st.divider()

# データの削除
st.header("4. データの削除")

st.markdown("""
- **ログアウト時**: セッション情報は即座に削除されます
- **自動削除**: プロファイル・キャッシュは30日後に自動削除されます
- **手動削除**: データ削除をご希望の場合はお問い合わせください
""")

st.divider()

# Cookie
st.header("5. Cookieの使用")

st.markdown("""
本サービスでは、セッション管理のためにCookieを使用しています。
Cookieにはセッション識別子のみが保存され、7日間有効です。
""")

st.divider()

# お問い合わせ
st.header("6. お問い合わせ")

st.markdown("""
プライバシーに関するお問い合わせは、GitHubリポジトリのIssueにてお願いします。
""")
