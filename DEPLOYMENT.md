# StreamlitアプリのURL共有方法

Streamlitアプリを遠くの人と共有する方法を説明します。

## 🚀 方法1: ngrok（一時的な共有・最も簡単）

### 手順

1. **ngrokをインストール**
   ```bash
   # macOS
   brew install ngrok
   
   # または公式サイトからダウンロード
   # https://ngrok.com/download
   ```

2. **ngrokアカウントを作成（無料）**
   - https://ngrok.com/ にアクセス
   - アカウント作成後、認証トークンを取得

3. **ngrokを認証**
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

4. **Streamlitアプリを起動**
   ```bash
   cd /Users/takuminittono/Desktop/ragstudy/streamlit
   source venv/bin/activate
   streamlit run app.py
   ```
   （通常は`http://localhost:8501`で起動）

5. **別のターミナルでngrokを起動**
   ```bash
   ngrok http 8501
   ```

6. **共有URLを取得**
   - ngrokのターミナルに表示されるURL（例: `https://xxxx-xx-xx-xx-xx.ngrok-free.app`）を共有
   - このURLはngrokを停止するまで有効

### 注意点
- ngrokの無料プランでは、URLが毎回変わる
- セッションが切れるとURLが無効になる
- 本番環境には不向き

---

## ☁️ 方法2: Streamlit Cloud（推奨・永続的）

### 手順

1. **GitHubにリポジトリを作成**
   ```bash
   cd /Users/takuminittono/Desktop/ragstudy/streamlit
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/rag-streamlit.git
   git push -u origin main
   ```

2. **Streamlit Cloudにサインアップ**
   - https://streamlit.io/cloud にアクセス
   - GitHubアカウントでサインアップ

3. **アプリをデプロイ**
   - Streamlit Cloudのダッシュボードで「New app」をクリック
   - GitHubリポジトリを選択
   - 設定：
     - **Main file path**: `app.py`
     - **Python version**: `3.11`
     - **Secrets**: OpenAI APIキーを設定
       ```
       OPENAI_API_KEY=your_api_key_here
       ```

4. **デプロイ完了**
   - `https://YOUR_APP_NAME.streamlit.app` のURLが生成される
   - このURLを共有

### メリット
- 永続的なURL
- 無料プランあり
- 自動デプロイ（GitHubにpushするだけで更新）
- HTTPS対応

### 注意点
- `.env`ファイルはGitに含めない（`.gitignore`に追加済み）
- SecretsでAPIキーを設定する必要がある
- ファイルサイズ制限あり

---

## 🖥️ 方法3: 自前サーバーにデプロイ

### 前提条件
- VPSやクラウドサーバー（AWS EC2、Google Cloud、Azure等）
- ドメイン（オプション）

### 手順

1. **サーバーにSSH接続**
   ```bash
   ssh user@your-server-ip
   ```

2. **必要なソフトウェアをインストール**
   ```bash
   # Python 3.11をインストール
   sudo apt update
   sudo apt install python3.11 python3.11-venv
   
   # プロジェクトをクローン
   git clone https://github.com/YOUR_USERNAME/rag-streamlit.git
   cd rag-streamlit
   ```

3. **仮想環境をセットアップ**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **環境変数を設定**
   ```bash
   # .envファイルを作成
   nano .env
   # OPENAI_API_KEY=your_api_key_here を追加
   ```

5. **Streamlitを起動**
   ```bash
   # バックグラウンドで起動
   nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
   ```

6. **Nginxでリバースプロキシ設定（推奨）**
   ```bash
   sudo apt install nginx
   sudo nano /etc/nginx/sites-available/streamlit
   ```
   
   設定内容：
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   
   ```bash
   sudo ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

7. **SSL証明書を設定（Let's Encrypt）**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## 🔒 セキュリティ考慮事項

### 共有前に確認すべきこと

1. **APIキーの保護**
   - `.env`ファイルがGitに含まれていないか確認
   - Streamlit CloudのSecretsを使用

2. **ファイルアクセスの制限**
   - 現在は認証なしでアクセス可能
   - 本番環境では認証を追加推奨

3. **レート制限**
   - OpenAI APIの使用量に注意
   - 必要に応じてレート制限を実装

---

## 📝 クイックスタート（ngrok）

最も簡単に共有する方法：

```bash
# 1. ngrokをインストール（初回のみ）
brew install ngrok

# 2. ngrokアカウント作成後、認証トークンを設定
ngrok config add-authtoken YOUR_TOKEN

# 3. Streamlitアプリを起動
cd /Users/takuminittono/Desktop/ragstudy/streamlit
source venv/bin/activate
streamlit run app.py

# 4. 別のターミナルでngrokを起動
ngrok http 8501

# 5. 表示されたURL（例: https://xxxx.ngrok-free.app）を共有
```

---

## 🎯 推奨方法

- **一時的な共有・デモ**: ngrok
- **永続的な共有・本番**: Streamlit Cloud
- **カスタマイズが必要**: 自前サーバー

