"""
ファイルのインデックス処理（Chroma DBへの保存）
"""
import os
import shutil
import datetime
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv()
try:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
except ImportError:
    from langchain.document_loaders import PyPDFLoader, TextLoader
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
try:
    from langchain_postgres import PGVector
except ImportError:
    PGVector = None
try:
    from langchain_community.vectorstores import Chroma
except ImportError:
    from langchain.vectorstores import Chroma
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    # フォールバック: langchain_communityを使用
    from langchain_community.embeddings import OpenAIEmbeddings
try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

# 定数定義
# 絶対パスを使用して確実に動作するようにする
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
COLLECTION_NAME = "rag_documents"

# サポートするファイル拡張子
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

# データベース設定（Supabase優先、フォールバックでChroma DB）
USE_SUPABASE = bool(os.getenv("DATABASE_URL"))


def load_documents(docs_dir: str) -> List[Document]:
    """
    docs/ディレクトリ内の全ファイルを読み込む
    
    Args:
        docs_dir: ドキュメントディレクトリのパス
        
    Returns:
        読み込んだDocumentのリスト
    """
    documents = []
    docs_path = Path(docs_dir)
    
    if not docs_path.exists():
        print(f"警告: {docs_dir} ディレクトリが存在しません")
        return documents
    
    # サポートされているファイルを検索
    for file_path in docs_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                print(f"読み込み中: {file_path.name}")
                
                if file_path.suffix.lower() == ".pdf":
                    loader = PyPDFLoader(str(file_path))
                    docs = loader.load()
                elif file_path.suffix.lower() in {".txt", ".md"}:
                    loader = TextLoader(str(file_path), encoding="utf-8")
                    docs = loader.load()
                else:
                    continue
                
                # 各ドキュメントにメタデータを追加（本格的な構造）
                for doc in docs:
                    # 基本メタデータ
                    doc.metadata["source"] = str(file_path)
                    doc.metadata["filename"] = file_path.name
                    doc.metadata["file_type"] = file_path.suffix.lower().replace(".", "")
                    doc.metadata["file_size"] = file_path.stat().st_size
                    
                    # PDFの場合はページ番号を追加
                    if file_path.suffix.lower() == ".pdf" and "page" in doc.metadata:
                        doc.metadata["page"] = doc.metadata["page"]
                    else:
                        doc.metadata["page"] = None
                    
                    # タイムスタンプ
                    doc.metadata["indexed_at"] = datetime.datetime.now().isoformat()
                    doc.metadata["chunk_size"] = len(doc.page_content)
                
                documents.extend(docs)
                print(f"  ✓ {len(docs)} チャンクを読み込みました")
                
            except Exception as e:
                print(f"  ✗ エラー: {file_path.name} - {e}")
                continue
    
    print(f"\n合計 {len(documents)} ドキュメントを読み込みました")
    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    """
    ドキュメントをチャンクに分割
    
    Args:
        documents: 分割前のDocumentリスト
        
    Returns:
        分割後のDocumentリスト
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"{len(chunks)} チャンクに分割しました")
    return chunks


def create_vectorstore(chunks: List[Document], persist_directory: str = None):
    """
    ベクトルストアを作成して保存（Supabase優先、フォールバックでChroma DB）
    
    Args:
        chunks: チャンク化されたDocumentリスト
        persist_directory: Chroma DBの保存ディレクトリ（Supabase使用時は無視）
    """
    if not chunks:
        print("警告: チャンクが空のため、ベクトルストアを作成しませんでした")
        return
    
    # Embeddingモデルの初期化（OpenAI text-embedding-3-small）
    # APIキーは環境変数から自動的に読み込まれる
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL
    )
    
    # Supabaseが利用可能な場合
    if USE_SUPABASE and PGVector:
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL環境変数が設定されていません")
            
            print(f"Supabase + pgvectorに保存します...")
            
            # Supabaseに保存（既存コレクションは自動的に上書き）
            # pre_delete_collection=Trueで既存データを削除してから保存
            vectorstore = PGVector.from_documents(
                documents=chunks,
                embedding=embeddings,  # from_documentsではembedding（単数形）
                connection=database_url,
                collection_name=COLLECTION_NAME,
                pre_delete_collection=True  # 既存コレクションを削除してから保存
            )
            
            print(f"✅ Supabase + pgvectorに保存しました")
            print(f"  {len(chunks)} チャンクを保存しました")
            return
            
        except Exception as e:
            print(f"Supabase保存エラー: {e}")
            print("⚠️ Chroma DBにフォールバックします")
            import traceback
            traceback.print_exc()
    
    # フォールバック: Chroma DBを使用（ローカル開発用）
    if not Chroma:
        raise ValueError("Chroma DBも利用できません。SupabaseまたはChroma DBの設定を確認してください")
    
    persist_directory = os.path.abspath(persist_directory or CHROMA_DB_PATH)
    
    # 既存のDBを削除（確実に削除するため、複数回試行）
    if os.path.exists(persist_directory):
        max_retries = 3
        for retry in range(max_retries):
            try:
                # ディレクトリ内のファイルの権限を変更してから削除
                import stat
                for root, dirs, files in os.walk(persist_directory):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                    for f in files:
                        os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                
                shutil.rmtree(persist_directory)
                print(f"既存のChroma DBを削除しました: {persist_directory}")
                break
            except Exception as e:
                if retry == max_retries - 1:
                    print(f"警告: 既存DBの削除に失敗しました: {e}")
                    # 最後の試行でも失敗した場合は、エラーを出す
                    raise
                import time
                time.sleep(0.5)  # 少し待ってから再試行
    
    # ディレクトリを作成（権限付き）
    try:
        import stat
        os.makedirs(persist_directory, mode=0o777, exist_ok=True)
        # 確実に書き込み権限を付与
        os.chmod(persist_directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        print(f"Chroma DBディレクトリを作成しました: {persist_directory}")
    except Exception as e:
        print(f"エラー: ディレクトリの作成に失敗しました: {e}")
        raise
    
    # 新しいベクトルストアを作成
    if chunks:
        # 一時ディレクトリに作成してから移動する方法を試す
        import tempfile
        temp_dir = None
        try:
            # まず一時ディレクトリに作成
            temp_dir = tempfile.mkdtemp(prefix="chroma_temp_")
            print(f"一時ディレクトリに作成: {temp_dir}")
            
            # 一時ディレクトリにChroma DBを作成（コレクション名とメタデータを設定）
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=temp_dir,
                collection_name="rag_documents",
                collection_metadata={
                    "description": "RAG system document collection",
                    "version": "1.0",
                    "chunk_size": CHUNK_SIZE,
                    "chunk_overlap": CHUNK_OVERLAP,
                    "embedding_model": EMBEDDING_MODEL
                }
            )
            print(f"一時ディレクトリにChroma DBを作成しました（コレクション: rag_documents）")
            
            # 既存のpersist_directoryを削除
            if os.path.exists(persist_directory):
                shutil.rmtree(persist_directory)
            
            # 一時ディレクトリをpersist_directoryに移動
            shutil.move(temp_dir, persist_directory)
            temp_dir = None  # 移動成功したのでNoneに設定
            
            print(f"Chroma DBを作成しました: {persist_directory}")
            print(f"  {len(chunks)} チャンクを保存しました")
            
        except Exception as e:
            print(f"エラー: Chroma DBの作成に失敗しました: {e}")
            # エラーの詳細を表示
            import traceback
            traceback.print_exc()
            
            # 一時ディレクトリのクリーンアップ
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            
            # 直接persist_directoryに作成する方法を試す（フォールバック）
            try:
                print("\nフォールバック: 直接persist_directoryに作成を試みます...")
                # 再度ディレクトリを作成
                import stat
                if os.path.exists(persist_directory):
                    shutil.rmtree(persist_directory)
                os.makedirs(persist_directory, mode=0o777, exist_ok=True)
                os.chmod(persist_directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                
                # Chroma DBを作成（コレクション名とメタデータを設定）
                vectorstore = Chroma.from_documents(
                    documents=chunks,
                    embedding=embeddings,
                    persist_directory=persist_directory,
                    collection_name="rag_documents",
                    collection_metadata={
                        "description": "RAG system document collection",
                        "version": "1.0",
                        "chunk_size": CHUNK_SIZE,
                        "chunk_overlap": CHUNK_OVERLAP,
                        "embedding_model": EMBEDDING_MODEL
                    }
                )
                print(f"フォールバック成功: Chroma DBを作成しました")
                print(f"  {len(chunks)} チャンクを保存しました")
            except Exception as e2:
                print(f"フォールバックも失敗しました: {e2}")
                raise
    else:
        print("警告: チャンクが空のため、Chroma DBを作成しませんでした")


def ingest(docs_dir: str = DOCS_DIR, chroma_db_path: str = None):
    """
    インデックス処理を実行
    
    Args:
        docs_dir: ドキュメントディレクトリのパス
        chroma_db_path: Chroma DBの保存パス（Supabase使用時は無視）
    """
    print("=" * 50)
    print("インデックス処理を開始します...")
    print("=" * 50)
    
    # 1. ドキュメントを読み込む
    documents = load_documents(docs_dir)
    
    if not documents:
        print("警告: 読み込むドキュメントがありません")
        return
    
    # 2. チャンクに分割
    chunks = split_documents(documents)
    
    # 3. Chroma DBを作成
    create_vectorstore(chunks, chroma_db_path)
    
    print("=" * 50)
    print("インデックス処理が完了しました！")
    print("=" * 50)
