# RAGシステム設計書

## 📐 アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI Layer                      │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  ファイル管理画面  │         │   チャット画面    │          │
│  │  (pages/1_...)   │         │    (app.py)      │          │
│  └────────┬─────────┘         └────────┬─────────┘          │
└───────────┼────────────────────────────┼─────────────────────┘
            │                            │
            ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   ingest.py       │         │    rag.py         │          │
│  │   (インデックス処理) │         │  (検索・生成)      │          │
│  └────────┬─────────┘         └────────┬─────────┘          │
└───────────┼────────────────────────────┼─────────────────────┘
            │                            │
            ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data & Model Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Chroma DB   │  │  Embedding   │  │  OpenAI API │        │
│  │ (Vector DB)  │  │   Model      │  │   (LLM)     │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 処理フロー

### 1. インデックス処理フロー（ingest.py）

```
ファイルアップロード/削除
    │
    ▼
load_documents()
    ├─ PDF → PyPDFLoader
    ├─ TXT → TextLoader
    └─ MD  → TextLoader
    │
    ▼
split_documents()
    ├─ chunk_size: 800文字
    ├─ chunk_overlap: 120文字
    └─ RecursiveCharacterTextSplitter
    │
    ▼
create_vectorstore()
    ├─ HuggingFaceEmbeddings
    │  └─ model: all-MiniLM-L6-v2
    ├─ 各チャンクをベクトル化
    └─ Chroma DBに保存
    │
    ▼
Chroma DB (chroma_db/)
    ├─ コレクション名: rag_documents
    ├─ メタデータ:
    │  ├─ filename
    │  ├─ file_type
    │  ├─ file_size
    │  ├─ page (PDFの場合)
    │  ├─ indexed_at
    │  └─ chunk_size
    └─ ベクトルデータ
```

### 2. 検索・回答生成フロー（rag.py）

```
ユーザー質問
    │
    ▼
RAGSystem.query()
    │
    ├─→ search()
    │   ├─ 質問をベクトル化 (Embedding)
    │   ├─ Chroma DBで類似度検索
    │   ├─ k=4件の結果を取得
    │   └─ メタデータ付きで返却
    │
    ▼
generate_answer()
    │
    ├─ 検索結果がない場合
    │  └─ "参照情報が見つかりませんでした。"
    │
    ├─ OpenAI API利用可能な場合
    │  ├─ プロンプト構築
    │  │  ├─ 参照情報（検索結果）
    │  │  └─ 質問
    │  ├─ gpt-4o-miniで回答生成
    │  └─ temperature=0.0（一貫性重視）
    │
    └─ API未設定の場合
       └─ 検索結果をフォーマットして返却
    │
    ▼
回答 + 参照情報
```

## 🧩 コンポーネント詳細

### 1. ingest.py - インデックス処理

**役割**: ドキュメントを読み込み、チャンク化し、ベクトルDBに保存

**主要関数**:
- `load_documents()`: ファイルを読み込み
- `split_documents()`: テキストをチャンクに分割
- `create_vectorstore()`: Chroma DBを作成・保存
- `ingest()`: 全体のインデックス処理を実行

**設定値**:
- `CHUNK_SIZE`: 800文字
- `CHUNK_OVERLAP`: 120文字
- `EMBEDDING_MODEL`: `sentence-transformers/all-MiniLM-L6-v2`

### 2. rag.py - RAG検索・生成

**役割**: ベクトル検索とLLM回答生成

**主要クラス**: `RAGSystem`

**主要メソッド**:
- `search()`: ベクトル検索（k=4件）
- `generate_answer()`: LLMで回答生成
- `query()`: 検索→生成の統合処理

**設定値**:
- `K_SEARCH_RESULTS`: 4件
- `MODEL`: `gpt-4o-mini`
- `TEMPERATURE`: 0.0

### 3. Chroma DB構造

**コレクション名**: `rag_documents`

**メタデータ構造**:
```python
{
    "filename": "example.txt",
    "file_type": "txt",
    "file_size": 1024,
    "page": None,  # PDFの場合はページ番号
    "indexed_at": "2026-01-10T12:00:00",
    "chunk_size": 800,
    "source": "/path/to/file"
}
```

**コレクションメタデータ**:
```python
{
    "description": "RAG system document collection",
    "version": "1.0",
    "chunk_size": 800,
    "chunk_overlap": 120,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

## 🔍 検索アルゴリズム

### ベクトル検索（Similarity Search）

1. **質問のベクトル化**
   - HuggingFace Embeddingsで質問文をベクトル化
   - 384次元のベクトルに変換

2. **類似度計算**
   - Chroma DB内の全ベクトルとコサイン類似度を計算
   - 類似度が高い順にソート

3. **結果取得**
   - 上位k件（デフォルト4件）を取得
   - メタデータと共に返却

### 検索結果の構造

```python
{
    "index": 1,
    "filename": "example.txt",
    "page": None,
    "chunk": "チャンクのテキスト内容...",
    "score": 0.8234,  # 類似度スコア
    "source": "/path/to/file"
}
```

## 💬 LLM回答生成

### プロンプトテンプレート

```
あなたは業務アシスタントです。
以下の「参照情報」に基づいてのみ回答してください。
参照情報に書かれていない内容は「分かりません」と答えてください。

【参照情報】
[filename1 (page 1)]
チャンク1の内容...

[filename2]
チャンク2の内容...

【質問】
{question}
```

### フォールバック処理

OpenAI APIが利用できない場合:
- 検索結果を整形して返却
- 参照情報の一覧を表示

## 🔐 セキュリティ考慮事項

1. **ファイル削除時のパストラバーサル対策**
   - ファイル名に`/`、`\`、`..`が含まれていないかチェック
   - 絶対パスでDOCS_DIR内にあることを確認

2. **APIキー管理**
   - `.env`ファイルで管理
   - `.gitignore`に追加

## 📊 パフォーマンス特性

- **インデックス処理**: O(n) - nはドキュメント数
- **検索処理**: O(log n) - Chroma DBのインデックス使用
- **回答生成**: API呼び出し時間に依存（通常1-3秒）

## 🚀 拡張性

### 将来の拡張ポイント

1. **検索アルゴリズム**
   - ハイブリッド検索（キーワード+ベクトル）
   - リランキング

2. **LLM**
   - 他のLLMプロバイダー対応
   - ローカルLLM対応

3. **メタデータ検索**
   - ファイルタイプでフィルタ
   - 日付範囲でフィルタ

4. **チャンク戦略**
   - セマンティックチャンキング
   - 階層的チャンキング

