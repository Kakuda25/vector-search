#!/usr/bin/env python3
"""
商品の類似度検索スクリプト
Sentence Transformersを使用して、クエリテキストと商品の類似度を計算し、類似商品を検索します。

使用方法:
    python app/scripts/search-similar-products.py "検索クエリ"
    python app/scripts/search-similar-products.py "ハンドピース" --limit 5
    python app/scripts/search-similar-products.py --compare-products --product-id 1
"""

import sys
import os
from pathlib import Path
import numpy as np
from typing import List, Tuple
import argparse

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("エラー: Sentence Transformersライブラリが必要です")
    print("インストール: pip install sentence-transformers")
    sys.exit(1)

from app.utils.database import create_connection
from app.utils.vector_utils import parse_vector_string, ensure_same_dimension


# モデルキャッシュ（グローバル変数）
_model_cache = {}


def get_model(model_name: str = "BAAI/bge-m3") -> SentenceTransformer:
    """モデルを取得（キャッシュから読み込みまたは新規読み込み）"""
    global _model_cache
    if model_name not in _model_cache:
        print(f"モデルを読み込み中: {model_name}...")
        print("（初回のみ時間がかかります）")
        model = SentenceTransformer(model_name)
        _model_cache[model_name] = model
    else:
        model = _model_cache[model_name]
    return model


def search_similar_products(
    connection,
    query_text: str,
    model: SentenceTransformer,
    limit: int = 10,
    min_similarity: float = 0.0,
    model_name: str = "BAAI/bge-m3"
) -> List[Tuple]:
    """クエリテキストと類似した商品を検索"""
    cursor = connection.cursor()

    query_embedding = model.encode(query_text, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
    
    cursor.execute("""
        SELECT id, product_code, name, description, price, embedding
        FROM products
        WHERE embedding IS NOT NULL
        ORDER BY id
    """)
    
    products = cursor.fetchall()
    
    if not products:
        print("ベクトルが設定されている商品が見つかりませんでした。")
        print("先に app/scripts/generate-embeddings.py を実行してベクトルを生成してください。")
        return []
    
    print(f"検索中: {len(products)}件の商品から類似商品を検索...")
    
    product_embeddings = []
    product_data = []
    
    for product_id, product_code, name, description, price, embedding_str in products:
        if embedding_str is None:
            continue
        
        embedding = parse_vector_string(embedding_str)
        embedding, query_embedding = ensure_same_dimension(embedding, query_embedding)
        
        product_embeddings.append(embedding)
        product_data.append((product_id, product_code, name, description, price))
    
    if len(product_embeddings) == 0:
        print("商品のベクトルが見つかりませんでした。")
        return []
    
    product_embeddings = np.array(product_embeddings, dtype=np.float32)
    query_embedding = query_embedding.astype(np.float32)
    
    # 正規化されたベクトルなので、内積でコサイン類似度が計算できる
    similarities = np.dot(product_embeddings, query_embedding)
    
    # 類似度でソート
    sorted_indices = np.argsort(similarities)[::-1]  # 降順
    
    # 結果を返す
    results = []
    for idx in sorted_indices:
        similarity = float(similarities[idx])
        if similarity >= min_similarity:
            product_id, product_code, name, description, price = product_data[idx]
            results.append((product_id, product_code, name, description, price, similarity))
            if len(results) >= limit:
                break
    
    return results


def compare_products(
    connection,
    product_id: int,
    model: SentenceTransformer,
    limit: int = 10
) -> List[Tuple]:
    """指定した商品と類似した商品を検索"""
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT id, product_code, name, description, price, embedding
        FROM products
        WHERE id = %s AND embedding IS NOT NULL
    """, (product_id,))
    
    product = cursor.fetchone()
    
    if not product:
        print(f"商品ID {product_id} が見つからないか、ベクトルが設定されていません。")
        return []
    
    product_id, product_code, name, description, price, embedding_str = product
    print(f"基準商品: {product_code} - {name}")
    
    query_embedding = parse_vector_string(embedding_str)
    
    cursor.execute("""
        SELECT id, product_code, name, description, price, embedding
        FROM products
        WHERE id != %s AND embedding IS NOT NULL
        ORDER BY id
    """, (product_id,))
    
    products = cursor.fetchall()
    
    if not products:
        print("比較対象の商品が見つかりませんでした。")
        return []
    
    product_embeddings = []
    product_data = []
    
    for pid, pcode, pname, pdesc, pprice, pembedding in products:
        if pembedding is None:
            continue
        
        embedding = parse_vector_string(pembedding)
        embedding, query_embedding = ensure_same_dimension(embedding, query_embedding)
        
        product_embeddings.append(embedding)
        product_data.append((pid, pcode, pname, pdesc, pprice))
    
    if len(product_embeddings) == 0:
        print("商品のベクトルが見つかりませんでした。")
        return []
    
    product_embeddings = np.array(product_embeddings, dtype=np.float32)
    query_embedding = query_embedding.astype(np.float32)
    
    # 正規化されたベクトルなので、内積でコサイン類似度が計算できる
    similarities = np.dot(product_embeddings, query_embedding)
    
    # 類似度でソート
    sorted_indices = np.argsort(similarities)[::-1]
    
    # 結果を返す
    results = []
    for idx in sorted_indices[:limit]:
        similarity = float(similarities[idx])
        pid, pcode, pname, pdesc, pprice = product_data[idx]
        results.append((pid, pcode, pname, pdesc, pprice, similarity))
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="商品の類似度検索スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # テキストクエリで検索
  python app/scripts/search-similar-products.py "ハンドピース"
  
  # 商品IDで類似商品を検索
  python app/scripts/search-similar-products.py --compare-products --product-id 1
  
  # 最小類似度を指定
  python app/scripts/search-similar-products.py "ワイヤレスイヤホン" --min-similarity 0.7
        """
    )
    parser.add_argument("query", nargs="?", help="検索クエリテキスト")
    parser.add_argument("--compare-products", action="store_true", help="商品同士の類似度を比較")
    parser.add_argument("--product-id", type=int, help="比較する商品ID（--compare-products使用時）")
    parser.add_argument("--limit", type=int, default=10, help="結果の最大件数（デフォルト: 10）")
    parser.add_argument("--min-similarity", type=float, default=0.0, help="最小類似度（デフォルト: 0.0）")
    parser.add_argument("--model", default="BAAI/bge-m3", help="使用するモデル名")
    
    args = parser.parse_args()
    
    connection = create_connection()
    model = get_model(args.model)
    
    try:
        if args.compare_products:
            # 商品同士の類似度を比較
            if not args.product_id:
                print("エラー: --compare-products を使用する場合は --product-id を指定してください。")
                sys.exit(1)
            
            results = compare_products(connection, args.product_id, model, args.limit)
            
            if results:
                print(f"\n類似商品（上位{len(results)}件）:")
                print("-" * 80)
                for pid, pcode, pname, pdesc, pprice, similarity in results:
                    print(f"類似度: {similarity:.4f} | {pcode} | {pname}")
                    if pdesc:
                        print(f"  説明: {pdesc[:60]}...")
                    print(f"  価格: ¥{pprice:,.0f}")
                    print()
        else:
            # テキストクエリで検索
            if not args.query:
                print("エラー: 検索クエリを指定してください。")
                parser.print_help()
                sys.exit(1)
            
            results = search_similar_products(
                connection, args.query, model, args.limit, args.min_similarity, args.model
            )
            
            if results:
                print(f"\n検索結果: 「{args.query}」に類似した商品（上位{len(results)}件）")
                print("=" * 80)
                for pid, pcode, pname, pdesc, pprice, similarity in results:
                    print(f"類似度: {similarity:.4f} | {pcode} | {pname}")
                    if pdesc:
                        print(f"  説明: {pdesc[:60]}...")
                    print(f"  価格: ¥{pprice:,.0f}")
                    print()
            else:
                print("類似商品が見つかりませんでした。")
    
    finally:
        connection.close()


if __name__ == "__main__":
    main()

