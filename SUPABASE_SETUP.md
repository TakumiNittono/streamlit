# Supabase + pgvector セットアップガイド

## 📋 前提条件

1. Supabaseアカウント（無料プランでOK）
2. Supabaseプロジェクトの作成
3. pgvector拡張機能の有効化

## 🚀 セットアップ手順

### 1. Supabaseプロジェクトの作成

1. https://supabase.com/ にアクセス
2. 「New Project」をクリック
3. プロジェクト名、データベースパスワードを設定
4. リージョンを選択（日本: Tokyo）
5. プロジェクトを作成

### 2. pgvector拡張機能の有効化

Supabaseダッシュボードで：

1. **SQL Editor**を開く
2. 以下のSQLを実行：

**重要**: `langchain_postgres`パッケージは、初回実行時に自動的にテーブルを作成します。手動で作成する必要はありませんが、事前に作成することも可能です。

#### オプションA: 自動テーブル作成（推奨）

テーブルは自動的に作成されるため、以下のSQLのみ実行してください：

```sql
-- pgvector拡張機能を有効化（これだけ実行すればOK）
CREATE EXTENSION IF NOT EXISTS vector;
```

#### オプションB: 手動でテーブルを作成する場合

事前にテーブルを作成したい場合は、以下のSQLを**順番に**実行してください：

```sql
-- pgvector拡張機能を有効化
CREATE EXTENSION IF NOT EXISTS vector;

-- コレクション管理用テーブル（先に作成）
CREATE TABLE IF NOT EXISTS langchain_pg_collection (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    cmetadata JSONB
);

-- ベクトルストア用のテーブル（コレクションテーブルの後に作成）
CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID,
    embedding vector(1536),  -- OpenAI text-embedding-3-smallは1536次元
    document TEXT,
    cmetadata JSONB,
    custom_id VARCHAR,
    CONSTRAINT langchain_pg_embedding_collection_id_fkey 
        FOREIGN KEY (collection_id) 
        REFERENCES langchain_pg_collection(uuid) 
        ON DELETE CASCADE
);

-- インデックスを作成（検索性能向上）
-- 注意: データが少ない場合はivfflatインデックスの作成に失敗する可能性があります
-- データを追加してからインデックスを作成することを推奨
CREATE INDEX IF NOT EXISTS langchain_pg_embedding_embedding_idx 
ON langchain_pg_embedding 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ユニークインデックス（custom_idがNULLでない場合のみ）
CREATE UNIQUE INDEX IF NOT EXISTS langchain_pg_embedding_custom_id_idx 
ON langchain_pg_embedding (collection_id, custom_id)
WHERE custom_id IS NOT NULL;

-- コレクション名のユニークインデックス
CREATE UNIQUE INDEX IF NOT EXISTS langchain_pg_collection_name_idx 
ON langchain_pg_collection (name);
```

**注意**: 実際には、`langchain_postgres`の`PGVector.from_documents()`を呼び出すと、これらのテーブルが自動的に作成されます。手動で作成する必要はありませんが、事前に作成しておくことも可能です。

### 3. 接続情報の取得

Supabaseダッシュボードで：

1. **Settings** → **Database** を開く
2. **Connection string** の **URI** をコピー
   - 形式: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`
   - または **Connection pooling** のURI（推奨）

### 4. 環境変数の設定

#### Streamlit Cloudの場合

1. Streamlit Cloudのダッシュボードでアプリを開く
2. **Settings** → **Secrets** を開く
3. 以下の形式で追加：

```toml
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
OPENAI_API_KEY=your-openai-api-key
```

#### ローカル環境の場合

`.env`ファイルに追加：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-publishable-key
DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
OPENAI_API_KEY=your-openai-api-key
```

### 5. 接続テスト

```python
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PGVector(
    connection=os.getenv("DATABASE_URL"),
    embedding_function=embeddings,
    collection_name="rag_documents"
)

print("✅ Supabase接続成功！")
print("✅ テーブルは自動的に作成されます")
```

**重要**: `PGVector`を初回作成する際に、必要なテーブル（`langchain_pg_collection`と`langchain_pg_embedding`）が自動的に作成されます。手動でテーブルを作成する必要はありません。
```

## 📊 データ構造

### langchain_pg_collection
- `uuid`: コレクションID
- `name`: コレクション名（例: "rag_documents"）
- `cmetadata`: メタデータ（JSON）

### langchain_pg_embedding
- `id`: エンベディングID
- `collection_id`: コレクションへの参照
- `embedding`: ベクトル（1536次元）
- `document`: チャンクのテキスト
- `cmetadata`: メタデータ（ファイル名、ページ番号など）
- `custom_id`: カスタムID

## 🔍 検索クエリの例

```sql
-- 類似度検索の例
SELECT 
    document,
    cmetadata,
    1 - (embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM langchain_pg_embedding
WHERE collection_id = (
    SELECT uuid FROM langchain_pg_collection WHERE name = 'rag_documents'
)
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 4;
```

## ⚙️ 設定の確認

### 必要な環境変数

- `SUPABASE_URL`: SupabaseプロジェクトのURL
- `SUPABASE_KEY`: Supabaseのanon key（オプション、Supabaseクライアント使用時）
- `DATABASE_URL`: PostgreSQL接続文字列（必須）
- `OPENAI_API_KEY`: OpenAI APIキー（必須）

### 接続文字列の形式

```
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

または、Connection Poolingを使用：

```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

## 🚨 トラブルシューティング

### pgvector拡張機能が有効にならない

```sql
-- 拡張機能の確認
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 手動で有効化
CREATE EXTENSION vector;
```

### 接続エラー

- ファイアウォール設定を確認
- Connection Poolingを使用しているか確認
- パスワードが正しいか確認

### ベクトル次元の不一致

- OpenAI `text-embedding-3-small` は **1536次元**
- テーブル定義で `vector(1536)` を指定

## 📝 移行チェックリスト

- [ ] Supabaseプロジェクト作成
- [ ] pgvector拡張機能有効化
- [ ] テーブル作成（SQL実行）
- [ ] 接続情報取得
- [ ] 環境変数設定
- [ ] 接続テスト
- [ ] コード更新（rag.py, ingest.py）
- [ ] 動作確認

