"""
RAG検索とLLM回答生成のロジック
"""
import os
from typing import List, Dict, Tuple, Optional
try:
    from langchain_postgres import PGVector
except ImportError:
    # フォールバック: Chroma DBを使用（ローカル開発用）
    try:
        from langchain_community.vectorstores import Chroma
    except ImportError:
        from langchain.vectorstores import Chroma
    PGVector = None
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    # フォールバック: langchain_communityを使用
    from langchain_community.embeddings import OpenAIEmbeddings
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 定数定義
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")
EMBEDDING_MODEL = "text-embedding-3-small"
K_SEARCH_RESULTS = 4
COLLECTION_NAME = "rag_documents"

# データベース設定（Supabase優先、フォールバックでChroma DB）
USE_SUPABASE = bool(os.getenv("DATABASE_URL"))

# プロンプトテンプレート
PROMPT_TEMPLATE = """あなたは業務アシスタントです。
以下の「参照情報」に基づいてのみ回答してください。
参照情報に書かれていない内容は「分かりません」と答えてください。

【参照情報】
{context}

【質問】
{question}
"""


class RAGSystem:
    """RAG検索とLLM回答生成を管理するクラス"""
    
    def __init__(self):
        """初期化"""
        # Embeddingモデルの初期化（OpenAI text-embedding-3-small）
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL
        )
        
        # Chroma DBの初期化
        self.vectorstore = None
        self._load_vectorstore()
        
        # OpenAIクライアントの初期化（APIキーがある場合のみ）
        self.openai_client = None
        self._init_openai_client()
    
    def _load_vectorstore(self):
        """ベクトルストアを読み込む（Supabase優先、フォールバックでChroma DB）"""
        # Supabaseが利用可能な場合
        if USE_SUPABASE and PGVector:
            try:
                database_url = os.getenv("DATABASE_URL")
                if database_url:
                    self.vectorstore = PGVector(
                        connection=database_url,
                        embeddings=self.embeddings,  # embedding_functionではなくembeddings
                        collection_name=COLLECTION_NAME
                    )
                    print("✅ Supabase + pgvectorを使用しています")
                    return
            except Exception as e:
                print(f"Supabase接続エラー: {e}")
                print("⚠️ Chroma DBにフォールバックします")
        
        # フォールバック: Chroma DBを使用（ローカル開発用）
        try:
            from langchain_community.vectorstores import Chroma
        except ImportError:
            try:
                from langchain.vectorstores import Chroma
            except ImportError:
                Chroma = None
        
        if Chroma:
            chroma_path = os.path.abspath(CHROMA_DB_PATH)
            if os.path.exists(chroma_path) and os.listdir(chroma_path):
                try:
                    self.vectorstore = Chroma(
                        persist_directory=chroma_path,
                        embedding_function=self.embeddings,
                        collection_name=COLLECTION_NAME
                    )
                    print("✅ Chroma DBを使用しています（ローカル）")
                except Exception as e:
                    print(f"Chroma DBの読み込みエラー: {e}")
                    # コレクション名なしで再試行（後方互換性）
                    try:
                        self.vectorstore = Chroma(
                            persist_directory=chroma_path,
                            embedding_function=self.embeddings
                        )
                        print("✅ Chroma DBを使用しています（フォールバック）")
                    except Exception as e2:
                        print(f"Chroma DBの読み込みエラー（フォールバック）: {e2}")
                        self.vectorstore = None
            else:
                self.vectorstore = None
        else:
            self.vectorstore = None
    
    def _init_openai_client(self):
        """OpenAIクライアントを初期化"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                self.openai_client = OpenAI(api_key=api_key)
            except Exception as e:
                print(f"OpenAIクライアントの初期化エラー: {e}")
                self.openai_client = None
    
    def search(self, query: str, k: int = K_SEARCH_RESULTS) -> List[Dict]:
        """
        ベクトル検索を実行
        
        Args:
            query: 検索クエリ
            k: 取得する検索結果数
            
        Returns:
            検索結果のリスト（ファイル名、ページ番号、チャンクを含む）
        """
        if not self.vectorstore:
            return []
        
        try:
            # ベクトル検索を実行
            docs = self.vectorstore.similarity_search_with_score(query, k=k)
            
            results = []
            for i, (doc, score) in enumerate(docs, 1):
                # メタデータからファイル名とページ番号を取得
                metadata = doc.metadata
                source = metadata.get("source", "unknown")
                page = metadata.get("page", None)
                
                # ファイル名のみを抽出（パスから）
                if isinstance(source, str):
                    filename = os.path.basename(source)
                else:
                    filename = str(source)
                
                results.append({
                    "index": i,
                    "filename": filename,
                    "page": page,
                    "chunk": doc.page_content,
                    "score": float(score),
                    "source": source
                })
            
            return results
        except Exception as e:
            print(f"検索エラー: {e}")
            return []
    
    def generate_answer(self, question: str, context_results: List[Dict]) -> Tuple[str, bool]:
        """
        LLMを使って回答を生成
        
        Args:
            question: 質問
            context_results: 検索結果のリスト
            
        Returns:
            (回答テキスト, LLM使用フラグ)のタプル
        """
        # 検索結果がない場合
        if not context_results:
            return "参照情報が見つかりませんでした。", False
        
        # コンテキストを構築
        context_parts = []
        for result in context_results:
            filename = result["filename"]
            page = result["page"]
            chunk = result["chunk"]
            
            page_info = f" (page {page})" if page is not None else ""
            context_parts.append(f"[{filename}{page_info}]\n{chunk}")
        
        context = "\n\n".join(context_parts)
        
        # OpenAI APIが利用可能な場合
        if self.openai_client:
            try:
                prompt = PROMPT_TEMPLATE.format(
                    context=context,
                    question=question
                )
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "あなたは業務アシスタントです。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                
                answer = response.choices[0].message.content.strip()
                return answer, True
            except Exception as e:
                print(f"OpenAI APIエラー: {e}")
                # フォールバック: 検索結果を返す
                return self._format_fallback_answer(context_results), False
        else:
            # APIキー未設定時: 検索結果を返す
            return self._format_fallback_answer(context_results), False
    
    def _format_fallback_answer(self, context_results: List[Dict]) -> str:
        """
        APIキー未設定時のフォールバック回答を生成
        
        Args:
            context_results: 検索結果のリスト
            
        Returns:
            フォーマットされた回答テキスト
        """
        if not context_results:
            return "参照情報が見つかりませんでした。"
        
        answer_parts = ["以下の参照情報が見つかりました：\n"]
        for result in context_results:
            filename = result["filename"]
            page = result["page"]
            chunk = result["chunk"]
            
            page_info = f" (page {page})" if page is not None else ""
            answer_parts.append(f"[{result['index']}] {filename}{page_info}")
            answer_parts.append(f"{chunk}\n")
        
        return "\n".join(answer_parts)
    
    def query(self, question: str) -> Tuple[str, List[Dict], bool]:
        """
        質問に対して検索と回答生成を実行
        
        Args:
            question: 質問
            
        Returns:
            (回答テキスト, 検索結果リスト, LLM使用フラグ)のタプル
        """
        # 検索実行
        search_results = self.search(question)
        
        # 回答生成
        answer, used_llm = self.generate_answer(question, search_results)
        
        return answer, search_results, used_llm


# グローバルインスタンス（必要に応じて）
_rag_system = None


def get_rag_system() -> RAGSystem:
    """RAGシステムのシングルトンインスタンスを取得"""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
    return _rag_system
