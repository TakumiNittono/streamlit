"""
Streamlit UI（チャット画面）
"""
import os
import streamlit as st
from pathlib import Path
from rag import get_rag_system

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


def init_rag_system():
    """RAGシステムを初期化"""
    if st.session_state.rag_system is None:
        st.session_state.rag_system = get_rag_system()


# ==================== ヘッダー ====================
st.title("💬 RAG Chat")

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
