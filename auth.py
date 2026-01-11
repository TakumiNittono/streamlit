"""
認証機能
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

# 定数定義
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_FILE = os.path.join(BASE_DIR, ".auth_users.json")

# デフォルトユーザー（初回セットアップ用）
DEFAULT_USER = {
    "email": os.getenv("ADMIN_EMAIL", "admin@example.com"),
    "password_hash": None,  # 初回ログイン時に設定
    "is_admin": True
}


def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()


def load_users() -> Dict[str, Dict]:
    """ユーザー情報を読み込む"""
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"ユーザーファイル読み込みエラー: {e}")
            return {}
    return {}


def save_users(users: Dict[str, Dict]):
    """ユーザー情報を保存"""
    try:
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"ユーザーファイル保存エラー: {e}")


def init_default_user():
    """デフォルトユーザーを初期化"""
    users = load_users()
    default_email = DEFAULT_USER["email"]
    
    # デフォルトユーザーが存在しない場合、環境変数からパスワードを設定
    if default_email not in users:
        default_password = os.getenv("ADMIN_PASSWORD", "admin123")
        users[default_email] = {
            "email": default_email,
            "password_hash": hash_password(default_password),
            "is_admin": True
        }
        save_users(users)
        print(f"デフォルトユーザーを作成しました: {default_email}")


def verify_password(email: str, password: str) -> bool:
    """パスワードを検証"""
    users = load_users()
    
    if email not in users:
        return False
    
    password_hash = hash_password(password)
    return users[email]["password_hash"] == password_hash


def create_user(email: str, password: str, is_admin: bool = False) -> bool:
    """新しいユーザーを作成"""
    users = load_users()
    
    if email in users:
        return False  # 既に存在する
    
    users[email] = {
        "email": email,
        "password_hash": hash_password(password),
        "is_admin": is_admin
    }
    save_users(users)
    return True


def change_password(email: str, old_password: str, new_password: str) -> bool:
    """パスワードを変更"""
    users = load_users()
    
    if email not in users:
        return False
    
    if not verify_password(email, old_password):
        return False
    
    users[email]["password_hash"] = hash_password(new_password)
    save_users(users)
    return True


def is_authenticated(session_state) -> bool:
    """認証済みかどうかを確認"""
    return session_state.get("authenticated", False)


def get_current_user(session_state) -> Optional[str]:
    """現在のユーザーのメールアドレスを取得"""
    if is_authenticated(session_state):
        return session_state.get("user_email")
    return None

