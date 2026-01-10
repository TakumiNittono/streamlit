# インストールトラブルシューティング

## Python 3.14での問題

Python 3.14を使用している場合、以下のエラーが発生する可能性があります：

### 問題1: onnxruntimeが見つからない

```
ERROR: Could not find a version that satisfies the requirement onnxruntime
```

**原因**: `onnxruntime`がPython 3.14に対応していません。

**解決策**: Python 3.11または3.12を使用してください。

### 問題2: pypikaのビルドエラー

```
AttributeError: module 'ast' has no attribute 'Str'
```

**原因**: `pypika`がPython 3.14の新しいAST APIに対応していません。

**解決策**: Python 3.11または3.12を使用してください。

## 推奨されるPythonバージョン

- **Python 3.11**（最も推奨）
- **Python 3.12**（推奨）
- Python 3.10（動作する可能性あり）
- Python 3.14（非推奨 - 互換性の問題あり）

## Python 3.11または3.12への切り替え方法

### macOS (Homebrew)

```bash
# Python 3.11をインストール
brew install python@3.11

# 仮想環境を作成
python3.11 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

### pyenvを使用する場合

```bash
# Python 3.11をインストール
pyenv install 3.11.9

# プロジェクトディレクトリで使用
pyenv local 3.11.9

# 仮想環境を作成
python -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

## その他のトラブルシューティング

### chromadbの依存関係エラー

`chromadb`を個別にインストールしてから、他のパッケージをインストールする：

```bash
pip install chromadb --no-deps
pip install -r requirements.txt
```

### インストールに時間がかかる

`sentence-transformers`と`torch`のインストールには時間がかかります。しばらくお待ちください。

### メモリ不足エラー

大容量のパッケージ（torch、sentence-transformersなど）をインストールする際にメモリ不足が発生する場合：

```bash
# 一度にインストールせず、個別にインストール
pip install streamlit
pip install langchain langchain-community
pip install sentence-transformers
pip install chromadb
```

