#!/usr/bin/env python3
"""
multilingual-e5-largeの正しい使用方法の例
公式ドキュメントに基づいた実装例

参考: https://huggingface.co/intfloat/multilingual-e5-large
"""

import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import numpy as np

print("=" * 80)
print("multilingual-e5-large の使用方法")
print("=" * 80)

# ============================================
# 方法1: transformersライブラリを使用（公式推奨）
# ============================================
print("\n【方法1】transformersライブラリを使用（公式推奨）")
print("-" * 80)

def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    """平均プーリング（attention maskを考慮）"""
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

# 重要: 入力テキストには"query: "または"passage: "プレフィックスが必要
# - 検索クエリ: "query: "を使用
# - 商品説明など: "passage: "を使用
input_texts = [
    'query: ハンドピース',
    'query: ワイヤレスイヤホン',
    "passage: ハンドピース 標準型 高回転・低振動の標準ハンドピース。日常的な切削に最適。",
    "passage: エアータービン 高速型 最高回転数40万回転の高速エアータービン。精密な切削が可能。",
    "passage: コンポジットレジン A2 審美性の高いコンポジットレジン。A2色。"
]

tokenizer = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-large')
model = AutoModel.from_pretrained('intfloat/multilingual-e5-large')

# トークナイズ
batch_dict = tokenizer(input_texts, max_length=512, padding=True, truncation=True, return_tensors='pt')

# 埋め込みを生成
outputs = model(**batch_dict)
embeddings = average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

# 正規化
embeddings = F.normalize(embeddings, p=2, dim=1)

# 類似度スコアを計算（クエリと商品の類似度）
# embeddings[:2] がクエリ、embeddings[2:] が商品
scores = (embeddings[:2] @ embeddings[2:].T) * 100
print(f"\n類似度スコア（100倍）:")
print(scores.tolist())

print("\nクエリ1「ハンドピース」と商品の類似度:")
for i, score in enumerate(scores[0]):
    print(f"  商品{i+1}: {score:.2f}")

print("\nクエリ2「ワイヤレスイヤホン」と商品の類似度:")
for i, score in enumerate(scores[1]):
    print(f"  商品{i+1}: {score:.2f}")

# ============================================
# 方法2: sentence-transformersライブラリを使用（簡易版）
# ============================================
print("\n\n【方法2】sentence-transformersライブラリを使用（簡易版）")
print("-" * 80)

model_st = SentenceTransformer('intfloat/multilingual-e5-large')

# プレフィックスを付けてベクトル化
query_texts = [
    'query: ハンドピース',
    'query: ワイヤレスイヤホン'
]

product_texts = [
    "passage: ハンドピース 標準型 高回転・低振動の標準ハンドピース。日常的な切削に最適。",
    "passage: エアータービン 高速型 最高回転数40万回転の高速エアータービン。精密な切削が可能。",
    "passage: コンポジットレジン A2 審美性の高いコンポジットレジン。A2色。"
]

query_embeddings = model_st.encode(query_texts, normalize_embeddings=True)
product_embeddings = model_st.encode(product_texts, normalize_embeddings=True)

# 類似度を計算（コサイン類似度）
similarities = model_st.similarity(query_embeddings, product_embeddings)

print(f"\n類似度マトリックス（コサイン類似度、0.0～1.0）:")
print(similarities)

print("\nクエリ1「ハンドピース」と商品の類似度:")
for i, similarity in enumerate(similarities[0]):
    print(f"  商品{i+1}: {similarity:.4f}")

print("\nクエリ2「ワイヤレスイヤホン」と商品の類似度:")
for i, similarity in enumerate(similarities[1]):
    print(f"  商品{i+1}: {similarity:.4f}")

# ============================================
# 商品検索の実践例
# ============================================
print("\n\n【実践例】商品検索の実装")
print("-" * 80)

def search_products(query: str, products: list, model: SentenceTransformer, top_k: int = 3):
    """商品を検索する関数"""
    # クエリにプレフィックスを追加
    if not query.startswith("query: "):
        query = "query: " + query
    
    # 商品にプレフィックスを追加
    product_texts = []
    for product in products:
        if not product.startswith("passage: "):
            product_texts.append("passage: " + product)
        else:
            product_texts.append(product)
    
    # ベクトル化
    query_embedding = model.encode([query], normalize_embeddings=True)
    product_embeddings = model.encode(product_texts, normalize_embeddings=True)
    
    # 類似度を計算
    similarities = model.similarity(query_embedding, product_embeddings)[0]
    
    # 上位k件を取得
    top_indices = similarities.argsort()[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append((products[idx], float(similarities[idx])))
    
    return results

# 商品データ
products = [
    "ハンドピース 標準型 高回転・低振動の標準ハンドピース。日常的な切削に最適。",
    "エアータービン 高速型 最高回転数40万回転の高速エアータービン。精密な切削が可能。",
    "コンポジットレジン A2 審美性の高いコンポジットレジン。A2色。",
    "超音波スケーラー 歯石除去に最適な超音波スケーラー。パワー調整可能。",
    "光重合器 LED型 LED式の光重合器。コンポジットレジンの重合に使用。"
]

# 検索クエリ
query = "ワイヤレスイヤホン"

print(f"\n検索クエリ: 「{query}」")
print("\n検索結果（上位3件）:")
results = search_products(query, products, model_st, top_k=3)
for i, (product, similarity) in enumerate(results, 1):
    print(f"{i}. 類似度: {similarity:.4f} | {product[:50]}...")

# ============================================
# 重要な注意事項
# ============================================
print("\n\n【重要な注意事項】")
print("-" * 80)
print("""
1. プレフィックスの使用:
   - 検索クエリ: "query: " を使用
   - 商品説明など: "passage: " を使用
   - プレフィックスを付けないと性能が低下します

2. タスクの種類:
   - 非対称タスク（検索など）: "query: " と "passage: " を使い分ける
   - 対称タスク（類似度計算など）: "query: " を使用
   - 特徴量として使用: "query: " を使用

3. コサイン類似度:
   - 正規化されたベクトル（normalize_embeddings=True）を使用
   - 類似度は0.0～1.0の範囲
   - 値が大きいほど類似している

4. 参考情報:
   - 公式ドキュメント: https://huggingface.co/intfloat/multilingual-e5-large
   - プレフィックスなしでは性能が低下する可能性があります
""")

print("=" * 80)
print("完了")
print("=" * 80)

