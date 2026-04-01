#!/usr/bin/env python3
"""
商品データのベクトル生成スクリプト
商品名と説明を結合してベクトル化し、PostgreSQLデータベースに更新します。

使用方法:
    python app/scripts/generate-embeddings.py

必要な環境変数:
    - POSTGRES_HOST: PostgreSQLホスト（デフォルト: localhost）
    - POSTGRES_PORT: PostgreSQLポート（デフォルト: 5432）
    - POSTGRES_DB: データベース名（デフォルト: dentaldb）
    - POSTGRES_USER: ユーザー名（デフォルト: postgres）
    - POSTGRES_PASSWORD: パスワード

使用モデル:
    - intfloat/multilingual-e5-large（固定）
"""

import sys
import os
from pathlib import Path
from typing import List

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("エラー: Sentence Transformersライブラリが必要です。")
    print("インストール: pip install sentence-transformers")
    sys.exit(1)

from app.utils.database import create_connection
from app.utils.vector_utils import adjust_dimension, VECTOR_DIMENSION


# モデルキャッシュ（グローバル変数）
_model_cache = None

def get_embedding(text: str, model_name: str = "intfloat/multilingual-e5-large", prefix: str = "passage: ") -> List[float]:
    """Sentence Transformersを使用してベクトルを生成
    
    multilingual-e5-largeモデルは1024次元を出力するが、データベースのvector型は1536次元に設定されているため、
    ゼロパディングで次元数を調整する。
    
    Args:
        text: ベクトル化するテキスト
        model_name: 使用するモデル名
        prefix: テキストに追加するプレフィックス（multilingual-e5-largeでは必須）
    
    Returns:
        ベクトル（リスト形式、1536次元）
    """
    global _model_cache
    
    if _model_cache is None:
        print(f"モデルを読み込み中: {model_name}...")
        print("（初回のみ時間がかかります）")
        _model_cache = SentenceTransformer(model_name)
    
    model = _model_cache
    
    if not text.startswith("query: ") and not text.startswith("passage: "):
        text = prefix + text
    
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    embedding = adjust_dimension(embedding)
    
    return embedding.tolist()


def update_embeddings_in_db(connection, model_name: str = "intfloat/multilingual-e5-large"):
    """データベース内の商品データにベクトルを追加"""
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT id, product_code, name, description 
        FROM products 
        WHERE embedding IS NULL
        ORDER BY id
    """)
    
    products = cursor.fetchall()
    
    if not products:
        print("更新が必要な商品が見つかりませんでした。")
        return
    
    print(f"{len(products)}件の商品データにベクトルを生成します...")
    print(f"モデル: {model_name}")
    
    updated_count = 0
    
    try:
        for product_id, product_code, name, description in products:
            text = f"{name}"
            if description:
                text += f" {description}"
            
            try:
                embedding = get_embedding(text, model_name, prefix="passage: ")
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                
                cursor.execute("""
                    UPDATE products 
                    SET embedding = %s::vector(%s)
                    WHERE id = %s
                """, (embedding_str, VECTOR_DIMENSION, product_id))
                
                updated_count += 1
                print(f"[OK] {product_code}: {name[:30]}...")
                
            except Exception as e:
                print(f"[NG] エラー ({product_code}): {str(e)}")
                connection.rollback()
                continue
        
        connection.commit()
        print(f"\n完了: {updated_count}件の商品データを更新しました。")
    except Exception as e:
        connection.rollback()
        print(f"\nエラー: 処理中にエラーが発生しました。ロールバックしました。{str(e)}")
        raise


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="商品データのベクトル生成スクリプト（intfloat/multilingual-e5-large使用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python app/scripts/generate-embeddings.py
  python app/scripts/generate-embeddings.py --model intfloat/multilingual-e5-large
        """
    )
    parser.add_argument("--model", default="intfloat/multilingual-e5-large", help="使用するモデル名（デフォルト: intfloat/multilingual-e5-large）")
    
    args = parser.parse_args()
    
    connection = create_connection()
    
    try:
        update_embeddings_in_db(connection, args.model)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
