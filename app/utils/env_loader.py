"""
環境変数読み込みユーティリティ
.envファイルから環境変数を読み込む共通処理
"""

import os
from typing import Optional


def load_env_file(env_file_path: Optional[str] = None) -> None:
    """環境変数ファイル(.env)から環境変数を読み込む
    
    Args:
        env_file_path: .envファイルのパス（Noneの場合はプロジェクトルートを自動検出）
    """
    if env_file_path is None:
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env_file_path = os.path.join(script_dir, ".env")
    
    if not os.path.exists(env_file_path):
        return
    
    encodings = ['utf-8', 'utf-8-sig', 'shift_jis', 'cp932', 'latin-1']
    content = None
    
    for encoding in encodings:
        try:
            with open(env_file_path, 'r', encoding=encoding) as f:
                content = f.readlines()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if content:
        for line in content:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ.setdefault(key, value)


def get_db_config() -> dict:
    """データベース接続設定を取得
    
    Returns:
        データベース接続設定の辞書
    """
    load_env_file()
    
    return {
        'host': os.getenv("POSTGRES_HOST", "localhost"),
        'port': int(os.getenv("POSTGRES_PORT", "5432")),
        'database': os.getenv("POSTGRES_DB", "vectordb"),
        'user': os.getenv("POSTGRES_USER", "postgres"),
        'password': os.getenv("POSTGRES_PASSWORD")
    }

