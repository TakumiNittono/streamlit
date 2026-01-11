"""
Streamlit UI（チャット画面）
"""
import os
import streamlit as st
from pathlib import Path
from rag import get_rag_system
from auth import (
    init_default_user,
    verify_password,
    is_authenticated,
    get_current_user
)

# 定数定義
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# ページ設定
st.set_page_config(
    page_title="RAG Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_system" not in st.session_state:
    st.session_state.rag_system = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# デフォルトユーザーの初期化
init_default_user()


def init_rag_system():
    """RAGシステムを初期化"""
    if st.session_state.rag_system is None:
        st.session_state.rag_system = get_rag_system()


# ==================== 認証チェック ====================
if not is_authenticated(st.session_state):
    st.title("🔐 ログイン")
    st.markdown("---")
    
    with st.form("login_form"):
        email = st.text_input("メールアドレス", placeholder="example@example.com")
        password = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
        submit_button = st.form_submit_button("ログイン", type="primary", use_container_width=True)
        
        if submit_button:
            if email and password:
                if verify_password(email, password):
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.success("ログインに成功しました！")
                    st.rerun()
                else:
                    st.error("メールアドレスまたはパスワードが正しくありません。")
            else:
                st.warning("メールアドレスとパスワードを入力してください。")
    
    st.markdown("---")
    st.info("💡 初回ログイン: 環境変数 `ADMIN_EMAIL` と `ADMIN_PASSWORD` で設定されたアカウントでログインできます。")
    st.stop()

# ==================== ヘッダー ====================
col1, col2 = st.columns([5, 1])
with col1:
    st.title("💬 RAG Chat")
with col2:
    st.write("")
    st.write("")
    current_user = get_current_user(st.session_state)
    if current_user:
        st.caption(f"👤 {current_user}")
    if st.button("🚪 ログアウト", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.messages = []
        st.rerun()

# RAGシステムの初期化
init_rag_system()

# ==================== チャット履歴 ====================
# 初回表示時のウェルカムメッセージ
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("こんにちは！ドキュメントについて何でも質問してください。")

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # 参照情報の表示（アシスタントメッセージのみ）
        if message["role"] == "assistant" and "references" in message and message["references"]:
            st.markdown("---")
            with st.expander("📚 参照元", expanded=False):
                for ref in message["references"]:
                    page_info = f" (p.{ref['page']})" if ref.get("page") else ""
                    st.markdown(f"**[{ref['index']}] {ref['filename']}{page_info}**")
                    st.caption(f"類似度スコア: {ref['score']:.4f}")
                    with st.expander(f"詳細を見る", expanded=False):
                        st.text(ref["chunk"])
                    st.divider()

# ==================== チャット入力 ====================
if prompt := st.chat_input("質問を入力してください..."):
    # ユーザーメッセージを追加
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # ユーザーメッセージを表示
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI回答を生成
    with st.chat_message("assistant"):
        with st.spinner("考え中..."):
            rag_system = st.session_state.rag_system
            
            # RAG検索と回答生成
            answer, search_results, used_llm = rag_system.query(prompt)
            
            # 回答を表示
            st.markdown(answer)
            
            # 参照情報を表示（最初は畳まれている）
            if search_results:
                st.markdown("---")
                with st.expander("📚 参照元", expanded=False):
                    for ref in search_results:
                        page_info = f" (p.{ref['page']})" if ref.get("page") else ""
                        st.markdown(f"**[{ref['index']}] {ref['filename']}{page_info}**")
                        st.caption(f"類似度スコア: {ref['score']:.4f}")
                        with st.expander(f"詳細を見る", expanded=False):
                            st.text(ref["chunk"])
                        st.divider()
        
        # アシスタントメッセージを追加
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "references": search_results
        })

# ==================== サイドバー ====================
with st.sidebar:
    st.title("⚙️ 設定")
    
    # ファイル情報（サポートされている拡張子のみカウント）
    files = []
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}
    if Path(DOCS_DIR).exists():
        for file_path in Path(DOCS_DIR).iterdir():
            # .gitkeepやその他の隠しファイルを除外し、サポートされている拡張子のみをカウント
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(file_path.name)
    
    st.metric("📁 ファイル数", len(files))
    
    st.markdown("---")
    if st.button("🗑️ チャット履歴をクリア"):
        st.session_state.messages = []
        st.rerun()
