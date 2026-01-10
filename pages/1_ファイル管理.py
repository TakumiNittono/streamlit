"""
ファイル管理画面
"""
import os
import streamlit as st
from pathlib import Path
from ingest import ingest

# 定数定義
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

# ページ設定
st.set_page_config(
    page_title="ファイル管理 - RAG Demo",
    page_icon="📁",
    layout="wide"
)

# セッション状態の初期化
if "indexing_status" not in st.session_state:
    st.session_state.indexing_status = "未実行"


def ensure_docs_dir():
    """docsディレクトリが存在することを確認"""
    Path(DOCS_DIR).mkdir(parents=True, exist_ok=True)


def get_file_list():
    """docs/内のファイル一覧を取得"""
    ensure_docs_dir()
    files = []
    for file_path in Path(DOCS_DIR).iterdir():
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append({
                "name": file_path.name,
                "path": str(file_path),
                "size": file_path.stat().st_size
            })
    return sorted(files, key=lambda x: x["name"])


def delete_file(filename: str):
    """ファイルを削除"""
    try:
        file_path = Path(DOCS_DIR) / filename
        
        # セキュリティチェック: パストラバーサル攻撃を防ぐ
        # ファイル名にパス区切り文字が含まれていないか確認
        if "/" in filename or "\\" in filename or ".." in filename:
            print(f"セキュリティエラー: 無効なファイル名: {filename}")
            return False
        
        # 絶対パスに変換して、DOCS_DIR内にあることを確認
        resolved_path = file_path.resolve()
        resolved_docs_dir = Path(DOCS_DIR).resolve()
        
        try:
            # Python 3.9+ の場合
            if not resolved_path.is_relative_to(resolved_docs_dir):
                print(f"セキュリティエラー: 無効なパス: {filename}")
                return False
        except AttributeError:
            # Python 3.8以前の場合の代替チェック
            try:
                resolved_path.relative_to(resolved_docs_dir)
            except ValueError:
                print(f"セキュリティエラー: 無効なパス: {filename}")
                return False
        
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            print(f"ファイルを削除しました: {filename}")
            return True
        else:
            print(f"ファイルが見つかりません: {filename}")
            return False
    except Exception as e:
        print(f"ファイル削除エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def upload_file(uploaded_file):
    """ファイルをアップロードして保存"""
    ensure_docs_dir()
    file_path = Path(DOCS_DIR) / uploaded_file.name
    
    # 既存ファイルの場合は上書き
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return True


def run_ingest():
    """インデックス処理を実行"""
    try:
        with st.spinner("インデックス処理を実行中..."):
            ingest()
            st.session_state.indexing_status = "完了"
        return True
    except Exception as e:
        st.error(f"インデックス処理エラー: {e}")
        st.session_state.indexing_status = f"エラー: {e}"
        return False


# ==================== メイン画面 ====================
st.title("📁 ファイル管理")

st.markdown("""
このページでは、RAGシステムで使用するドキュメントファイルを管理できます。
PDF、txt、mdファイルをアップロードして、自動的にインデックス処理が実行されます。
""")

st.divider()

# ファイルアップロードセクション
st.subheader("📤 ファイルをアップロード")

uploaded_files = st.file_uploader(
    "PDF、txt、mdファイルを選択（複数選択可能）",
    type=["pdf", "txt", "md"],
    help="サポート形式: PDF, txt, md（複数ファイルを同時に選択できます）",
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    # 複数ファイルが選択された場合
    if len(uploaded_files) > 1:
        st.info(f"**{len(uploaded_files)}件のファイル**が選択されました")
        # ファイル一覧を表示
        with st.expander("選択されたファイル一覧", expanded=True):
            total_size = 0
            for idx, file in enumerate(uploaded_files, 1):
                file_size_mb = file.size / (1024 * 1024)
                if file_size_mb < 1:
                    size_str = f"{file.size:,} bytes"
                else:
                    size_str = f"{file_size_mb:.2f} MB"
                st.write(f"{idx}. **{file.name}** ({size_str})")
                total_size += file.size
            
            total_size_mb = total_size / (1024 * 1024)
            if total_size_mb < 1:
                total_size_str = f"{total_size:,} bytes"
            else:
                total_size_str = f"{total_size_mb:.2f} MB"
            st.caption(f"合計サイズ: {total_size_str}")
    else:
        # 1ファイルのみの場合
        uploaded_file = uploaded_files[0]
        col1, col2 = st.columns([3, 1])
        with col1:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb < 1:
                size_str = f"{uploaded_file.size:,} bytes"
            else:
                size_str = f"{file_size_mb:.2f} MB"
            st.info(f"選択されたファイル: **{uploaded_file.name}** ({size_str})")
    
    # アップロードボタン
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("アップロード", type="primary", use_container_width=True):
            success_count = 0
            error_files = []
            
            with st.spinner("アップロード中..."):
                for uploaded_file in uploaded_files:
                    if upload_file(uploaded_file):
                        success_count += 1
                    else:
                        error_files.append(uploaded_file.name)
            
            # 結果を表示
            if success_count == len(uploaded_files):
                if len(uploaded_files) == 1:
                    st.success(f"✓ {uploaded_files[0].name} をアップロードしました")
                else:
                    st.success(f"✓ {success_count}件のファイルをアップロードしました")
                
                # インデックス処理を実行
                if run_ingest():
                    st.success("✓ インデックス処理が完了しました")
                st.rerun()
            else:
                if error_files:
                    st.error(f"アップロードに失敗したファイル: {', '.join(error_files)}")
                else:
                    st.error("アップロードに失敗しました")

st.divider()

# ファイル一覧セクション
st.subheader("📋 ファイル一覧")

files = get_file_list()

if not files:
    st.info("📭 ファイルがありません。上記からファイルをアップロードしてください。")
else:
    st.write(f"**合計 {len(files)}件のファイル**")
    
    # ファイル一覧をテーブル形式で表示
    for idx, file_info in enumerate(files):
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 4, 2, 1])
            
            with col1:
                st.write(f"**{idx + 1}**")
            
            with col2:
                st.write(f"📄 **{file_info['name']}**")
            
            with col3:
                size_mb = file_info['size'] / (1024 * 1024)
                if size_mb < 1:
                    st.caption(f"{file_info['size']:,} bytes")
                else:
                    st.caption(f"{size_mb:.2f} MB")
            
            with col4:
                if st.button("削除", key=f"delete_{file_info['name']}", type="secondary"):
                    # 削除確認
                    st.session_state[f"confirm_delete_{file_info['name']}"] = True
            
            # 削除確認ダイアログ
            if st.session_state.get(f"confirm_delete_{file_info['name']}", False):
                st.warning(f"⚠️ **{file_info['name']}** を削除しますか？")
                col_yes, col_no, col_space = st.columns([1, 1, 4])
                with col_yes:
                    if st.button("はい", key=f"yes_{file_info['name']}", type="primary"):
                        if delete_file(file_info['name']):
                            st.success(f"✓ {file_info['name']} を削除しました")
                            # インデックス処理を実行
                            if run_ingest():
                                st.success("✓ インデックス処理が完了しました")
                            # セッション状態をリセット
                            st.session_state[f"confirm_delete_{file_info['name']}"] = False
                            st.rerun()
                        else:
                            st.error("削除に失敗しました")
                with col_no:
                    if st.button("いいえ", key=f"no_{file_info['name']}"):
                        st.session_state[f"confirm_delete_{file_info['name']}"] = False
                        st.rerun()
            
            if idx < len(files) - 1:
                st.divider()

st.divider()

# インデックス状態セクション
st.subheader("🔧 インデックス管理")

col1, col2 = st.columns([2, 1])

with col1:
    status_color = "🟢" if st.session_state.indexing_status == "完了" else "🟡" if "エラー" not in st.session_state.indexing_status else "🔴"
    st.write(f"**状態**: {status_color} {st.session_state.indexing_status}")

with col2:
    if st.button("🔄 手動で再インデックス", help="Chroma DBを再構築します", use_container_width=True):
        if run_ingest():
            st.success("✓ 再インデックスが完了しました")
            st.rerun()

# フッター情報
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"📁 ファイル数: {len(files)}")
with col2:
    chroma_exists = os.path.exists("./chroma_db") and os.listdir("./chroma_db")
    st.caption(f"🗄️ Chroma DB: {'存在' if chroma_exists else '未作成'}")
with col3:
    api_key_set = bool(os.getenv("OPENAI_API_KEY"))
    st.caption(f"🔑 OpenAI API: {'設定済み' if api_key_set else '未設定'}")

# サイドバーにナビゲーション情報
with st.sidebar:
    st.title("📚 RAG Demo")
    st.markdown("---")
    st.markdown("### ナビゲーション")
    st.markdown("""
    - **💬 RAG チャット** - チャット機能
    - **📁 ファイル管理** - 現在のページ
    """)
    st.markdown("---")
    st.markdown("### 使い方")
    st.markdown("""
    1. このページでドキュメントをアップロード
    2. 自動的にインデックス処理が実行されます
    3. **RAG チャット**ページで質問を入力
    """)
