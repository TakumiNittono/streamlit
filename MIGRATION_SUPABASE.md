# Chroma DB → Supabase + pgvector 移行ガイド

## 📋 移行の概要

Chroma DBからSupabase + pgvectorへの移行により、Streamlit Cloudでのデータ永続化が可能になります。

## 🔄 変更内容

### 1. 依存関係の追加

`requirements.txt`に以下を追加：
- `langchain-postgres>=1.0.0` - PostgreSQL + pgvectorサポート
- `psycopg2-binary>=2.9.0` - PostgreSQL接続
- `supabase>=2.0.0` - Supabaseクライアント（オプション）

### 2. コードの変更

#### `rag.py`
- `_load_vectorstore()`: Supabase優先、フォールバックでChroma DB
- `DATABASE_URL`環境変数がある場合、自動的にSupabaseを使用

#### `ingest.py`
- `create_vectorstore()`: Supabase優先、フォールバックでChroma DB
- `DATABASE_URL`環境変数がある場合、自動的にSupabaseに保存

### 3. 後方互換性

- `DATABASE_URL`が設定されていない場合、従来通りChroma DBを使用
- ローカル開発環境ではChroma DBを継続使用可能

## 🚀 移行手順

### ステップ1: Supabaseプロジェクトのセットアップ

1. Supabaseアカウント作成: https://supabase.com/
2. 新しいプロジェクトを作成
3. pgvector拡張機能を有効化（`SUPABASE_SETUP.md`を参照）

### ステップ2: 環境変数の設定

#### Streamlit Cloud

1. Streamlit Cloudダッシュボードでアプリを開く
2. **Settings** → **Secrets** を開く
3. 以下を追加：

```toml
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
OPENAI_API_KEY=your-openai-api-key
```

#### ローカル環境（テスト用）

`.env`ファイルに追加：

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
OPENAI_API_KEY=your-openai-api-key
```

### ステップ3: コードのデプロイ

```bash
git add requirements.txt rag.py ingest.py
git commit -m "Migrate to Supabase + pgvector"
git push
```

### ステップ4: 動作確認

1. Streamlit Cloudでアプリを再デプロイ
2. ファイル管理ページでファイルをアップロード
3. インデックス処理が成功するか確認
4. チャットページで検索が動作するか確認

## 🔍 動作確認方法

### Supabaseが使用されているか確認

アプリのログに以下が表示されます：
- `✅ Supabase + pgvectorを使用しています` - Supabase使用中
- `✅ Chroma DBを使用しています（ローカル）` - Chroma DB使用中

### Supabaseダッシュボードで確認

1. Supabaseダッシュボードを開く
2. **Table Editor** → `langchain_pg_embedding` を開く
3. データが保存されているか確認

## ⚠️ 注意事項

### データの移行

既存のChroma DBデータは自動的に移行されません。手動で移行する場合：

1. ローカルでChroma DBからデータをエクスポート
2. Supabaseにインポート

または、Streamlit Cloudで再度ファイルをアップロードしてインデックス処理を実行。

### コスト

- Supabase無料プラン: 500MBストレージ、2GB転送
- 大量のデータを使用する場合は有料プランを検討

### パフォーマンス

- pgvectorは大規模データセットで優れた性能
- インデックス（ivfflat）が自動的に作成される

## 🐛 トラブルシューティング

### 接続エラー

```
Supabase接続エラー: ...
⚠️ Chroma DBにフォールバックします
```

**解決策**:
- `DATABASE_URL`が正しく設定されているか確認
- Supabaseのファイアウォール設定を確認
- Connection Poolingを使用しているか確認

### pgvector拡張機能エラー

```sql
ERROR: extension "vector" does not exist
```

**解決策**:
- Supabase SQL Editorで `CREATE EXTENSION vector;` を実行

### テーブルが存在しない

**解決策**:
- `SUPABASE_SETUP.md`のSQLを実行してテーブルを作成

## 📊 比較表

| 項目 | Chroma DB | Supabase + pgvector |
|------|-----------|---------------------|
| 永続化 | ローカルのみ | ✅ クラウド永続化 |
| Streamlit Cloud | ❌ 再デプロイで消える | ✅ 永続化 |
| スケーラビリティ | 中 | ✅ 高 |
| セットアップ | 簡単 | 中程度 |
| コスト | 無料 | 無料プランあり |

## ✅ 移行チェックリスト

- [ ] Supabaseプロジェクト作成
- [ ] pgvector拡張機能有効化
- [ ] テーブル作成（SQL実行）
- [ ] 環境変数設定（`DATABASE_URL`）
- [ ] コード更新（requirements.txt, rag.py, ingest.py）
- [ ] Git push & デプロイ
- [ ] 動作確認
- [ ] データがSupabaseに保存されているか確認

