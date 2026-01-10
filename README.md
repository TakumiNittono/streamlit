# RAG Demo with File Manager & Reference Chat

ファイル管理機能と根拠参照付きチャットを統合したRAGアプリケーションの実装手順です。

## 📋 目次

- [前提条件](#前提条件)
- [セットアップ手順](#セットアップ手順)
- [実装手順](#実装手順)
- [実行方法](#実行方法)
- [使用方法](#使用方法)
- [トラブルシューティング](#トラブルシューティング)

## 前提条件

- **Python 3.11または3.12**（推奨）
  - ⚠️ **注意**: Python 3.14は一部パッケージ（onnxruntime、pypikaなど）が未対応のため、Python 3.11または3.12の使用を推奨します
- OpenAI APIキー（オプション：未設定時は検索結果のみ表示）
- 必要なPythonパッケージ（後述）

## セットアップ手順

### 1. プロジェクトディレクトリの作成

```bash
mkdir rag-streamlit
cd rag-streamlit
```

### 2. ディレクトリ構成の作成

以下のディレクトリ構造を作成します：

```bash
mkdir -p docs chroma_db tmp
```

最終的なディレクトリ構成：

```
rag-streamlit/
├ app.py                 # Streamlit UI（チャット＋管理）
├ ingest.py              # 再インデックス処理
├ rag.py                 # 検索・生成ロジック
├ requirements.txt       # 依存関係
├ README.md              # このファイル
├ requirements.md        # 要件定義書
├ docs/                  # アップロードされたファイル
├ chroma_db/             # Chroma 永続DB（自動生成）
└ tmp/                   # アップロード一時保存（任意）
```

### 3. 仮想環境の作成と有効化

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 仮想環境が有効化されているか確認（プロンプトの前に (venv) が表示されます）
```

**注意**: macOSでは`pip`の代わりに`python3 -m pip`を使用するか、仮想環境を有効化してから`pip`を使用してください。

### 4. 依存関係のインストール

仮想環境を有効化した状態で、以下のコマンドを実行します：

```bash
# pipを最新版にアップグレード（推奨）
python3 -m pip install --upgrade pip

# 依存関係をインストール
pip install -r requirements.txt
```

**トラブルシューティング**: 
- `pip`コマンドが見つからない場合は、`python3 -m pip install -r requirements.txt`を使用してください
- インストールに時間がかかる場合があります（特にchromadb）

## 実装手順

### ステップ1: requirements.txt の作成

プロジェクトルートに`requirements.txt`を作成：

```txt
streamlit>=1.28.0
langchain>=0.1.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
pypdf>=3.17.0
openai>=1.0.0
python-dotenv>=1.0.0
```

### ステップ2: rag.py の実装

RAG検索とLLM回答生成のロジックを実装します。

**主な機能：**
- Chroma DBからのベクトル検索（k=4）
- OpenAI APIを使った回答生成
- 参照情報の抽出（ファイル名、ページ番号）

### ステップ3: ingest.py の実装

ファイルのインデックス処理を実装します。

**主な機能：**
- `docs/`内の全ファイルを読み込み
- チャンキング（chunk_size=800, chunk_overlap=120）
- Chroma DBへの保存
- 既存DBの削除と再生成

### ステップ4: app.py の実装

Streamlit UIを実装します。

**主な機能：**
- **サイドバー（ファイル管理）：**
  - ファイルアップロード（PDF/txt/md）
  - ファイル一覧表示
  - ファイル削除（確認付き）
  - アップロード/削除時の自動再インデックス

- **メイン画面（チャット）：**
  - チャット入力欄
  - ユーザー発言とAI回答の表示
  - 参照情報の表示（折りたたみ可能）
  - ファイル名とページ番号の明示

### ステップ5: 環境変数の設定

`.env`ファイルを作成（プロジェクトルートに）：

```bash
OPENAI_API_KEY=your_api_key_here
```

または、環境変数として設定：

```bash
# macOS/Linux:
export OPENAI_API_KEY=your_api_key_here

# Windows:
# set OPENAI_API_KEY=your_api_key_here
```

**注意：** APIキー未設定時は、LLMを使わず検索結果のみを表示します。

## 実行方法

### 1. アプリケーションの起動

```bash
streamlit run app.py
```

### 2. ブラウザでアクセス

自動的にブラウザが開き、`http://localhost:8501`でアプリにアクセスできます。

## 使用方法

### ファイルのアップロード

1. 左サイドバーの「ファイル管理」セクションで「ファイルをアップロード」をクリック
2. PDF、txt、またはmdファイルを選択
3. アップロード後、自動的にChroma DBが再構築されます

### チャットの利用

1. メイン画面のチャット入力欄に質問を入力
2. Enterキーまたは「送信」ボタンをクリック
3. AI回答と参照元情報が表示されます
4. 参照元をクリックすると、該当チャンクの全文が表示されます

### ファイルの削除

1. サイドバーのファイル一覧から削除したいファイルを選択
2. 「削除」ボタンをクリック
3. 確認ダイアログで「はい」を選択
4. 自動的にChroma DBが再構築されます

## トラブルシューティング

### Chroma DBが作成されない

- `docs/`ディレクトリにファイルが存在するか確認
- `chroma_db/`ディレクトリの書き込み権限を確認
- エラーメッセージを確認し、`ingest.py`を手動実行してみる

### OpenAI APIエラー

- 環境変数`OPENAI_API_KEY`が正しく設定されているか確認
- APIキーの有効性を確認
- APIキー未設定時は検索結果のみが表示されます（正常動作）

### ファイルがアップロードできない

- ファイル形式がPDF、txt、mdのいずれかであることを確認
- ファイルサイズが大きすぎないか確認
- `docs/`ディレクトリの書き込み権限を確認

### インデックス処理が遅い

- ファイル数やサイズが大きい場合、処理に時間がかかります
- 小〜中規模ファイル（数十PDF）を想定しています

## 技術スタック

| 役割 | 技術 |
|------|------|
| UI | Streamlit |
| RAG制御 | LangChain |
| Vector DB | Chroma（Persistent / ローカル） |
| Embedding | sentence-transformers（all-MiniLM-L6-v2） |
| LLM | OpenAI API（gpt-4o-mini） |
| ファイル保存 | ローカルファイルシステム |

## 参考資料

- [要件定義書](./requirements.md) - 詳細な要件定義
- [Streamlit公式ドキュメント](https://docs.streamlit.io/)
- [LangChain公式ドキュメント](https://python.langchain.com/)
- [Chroma公式ドキュメント](https://www.trychroma.com/)

## ライセンス

このプロジェクトはデモ用途です。

