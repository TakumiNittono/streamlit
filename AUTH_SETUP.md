# 認証機能のセットアップ

## 📋 概要

RAG Chatアプリにメールアドレスとパスワードによる認証機能を追加しました。

## 🔐 初回セットアップ

### 1. 環境変数の設定

#### Streamlit Cloudの場合

1. Streamlit Cloudのダッシュボードでアプリを開く
2. **Settings** → **Secrets** を開く
3. 以下を追加：

```toml
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=your-secure-password
```

#### ローカル環境の場合

`.env`ファイルに追加：

```bash
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=your-secure-password
```

### 2. 初回ログイン

1. アプリを起動
2. ログイン画面が表示されます
3. 環境変数で設定したメールアドレスとパスワードでログイン
4. 初回ログイン時に、`.auth_users.json`ファイルが自動的に作成されます

## 📁 ユーザー管理

### ユーザーファイルの場所

- ローカル: `.auth_users.json`（プロジェクトルート）
- Streamlit Cloud: `.auth_users.json`（アプリの作業ディレクトリ）

### ユーザーファイルの構造

```json
{
  "admin@example.com": {
    "email": "admin@example.com",
    "password_hash": "ハッシュ化されたパスワード",
    "is_admin": true
  }
}
```

## 🔒 セキュリティ

### パスワードのハッシュ化

- パスワードはSHA-256でハッシュ化されて保存されます
- 平文のパスワードは保存されません

### 注意事項

⚠️ **本番環境での推奨事項**:

1. **より強力なハッシュ化**: 現在はSHA-256を使用していますが、本番環境では`bcrypt`や`argon2`の使用を推奨します
2. **HTTPS必須**: パスワードの送信はHTTPSで保護してください
3. **セッション管理**: 現在はStreamlitのセッション状態を使用していますが、本番環境ではより堅牢なセッション管理を推奨します
4. **Supabase Auth**: 本番環境ではSupabase Authの使用を推奨します

## 🚀 今後の拡張

### Supabase Authへの移行

より堅牢な認証が必要な場合、Supabase Authへの移行を検討してください：

1. Supabaseプロジェクトで認証を有効化
2. `auth.py`をSupabase Auth対応に変更
3. より安全な認証フローを実装

### 追加機能

- パスワードリセット機能
- ユーザー登録機能
- ロール管理（管理者/一般ユーザー）
- セッションタイムアウト

## 📝 使用方法

### ログイン

1. アプリにアクセス
2. ログイン画面でメールアドレスとパスワードを入力
3. 「ログイン」ボタンをクリック

### ログアウト

1. 右上の「ログアウト」ボタンをクリック
2. ログイン画面に戻ります

## 🐛 トラブルシューティング

### ログインできない

1. 環境変数`ADMIN_EMAIL`と`ADMIN_PASSWORD`が正しく設定されているか確認
2. `.auth_users.json`ファイルが存在するか確認
3. メールアドレスとパスワードが正しいか確認

### ユーザーファイルが作成されない

- 初回ログイン時に自動的に作成されます
- 書き込み権限があるか確認してください

### パスワードを変更したい

現在は手動で`.auth_users.json`を編集するか、環境変数を変更して再ログインしてください。

## 🔧 開発者向け

### ユーザーを追加する

```python
from auth import create_user

# 新しいユーザーを作成
create_user("user@example.com", "password123", is_admin=False)
```

### パスワードを変更する

```python
from auth import change_password

# パスワードを変更
change_password("user@example.com", "old_password", "new_password")
```

