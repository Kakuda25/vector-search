-- ============================================
-- ベクトル検索のサンプルクエリ
-- ============================================
-- このファイルは参考用です。実際の検索には使用しません。

-- ============================================
-- 1. コサイン類似度による検索（最も一般的）
-- ============================================
-- クエリベクトルと最も類似した商品を検索
-- 例: 検索クエリ「ワイヤレスイヤホン」のベクトルを[0.1, 0.2, ...]と仮定

/*
SELECT 
    id,
    product_code,
    name,
    description,
    price,
    1 - (embedding <=> '[0.1,0.2,0.3,...]'::vector) AS similarity
FROM products
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1,0.2,0.3,...]'::vector
LIMIT 10;
*/

-- ============================================
-- 2. 距離による検索（ユークリッド距離）
-- ============================================
/*
SELECT 
    id,
    product_code,
    name,
    description,
    price,
    embedding <-> '[0.1,0.2,0.3,...]'::vector AS distance
FROM products
WHERE embedding IS NOT NULL
ORDER BY embedding <-> '[0.1,0.2,0.3,...]'::vector
LIMIT 10;
*/

-- ============================================
-- 3. 内積による検索
-- ============================================
/*
SELECT 
    id,
    product_code,
    name,
    description,
    price,
    embedding <#> '[0.1,0.2,0.3,...]'::vector AS negative_inner_product
FROM products
WHERE embedding IS NOT NULL
ORDER BY embedding <#> '[0.1,0.2,0.3,...]'::vector
LIMIT 10;
*/

-- ============================================
-- 4. 類似度閾値を設定した検索
-- ============================================
-- コサイン類似度が0.7以上の商品のみを取得
/*
SELECT 
    id,
    product_code,
    name,
    description,
    price,
    1 - (embedding <=> '[0.1,0.2,0.3,...]'::vector) AS similarity
FROM products
WHERE embedding IS NOT NULL
  AND 1 - (embedding <=> '[0.1,0.2,0.3,...]'::vector) >= 0.7
ORDER BY embedding <=> '[0.1,0.2,0.3,...]'::vector
LIMIT 10;
*/

-- ============================================
-- 5. ハイブリッド検索（ベクトル検索 + 条件フィルタ）
-- ============================================
-- ベクトル検索と通常の条件を組み合わせ
/*
SELECT 
    id,
    product_code,
    name,
    description,
    price,
    status,
    1 - (embedding <=> '[0.1,0.2,0.3,...]'::vector) AS similarity
FROM products
WHERE embedding IS NOT NULL
  AND status = 'active'
  AND price <= 100000
ORDER BY embedding <=> '[0.1,0.2,0.3,...]'::vector
LIMIT 10;
*/

-- ============================================
-- ベクトル演算子の説明
-- ============================================
-- <=> : コサイン距離（1 - コサイン類似度）
-- <-> : ユークリッド距離（L2距離）
-- <#> : 負の内積（内積の符号を反転）

-- コサイン類似度 = 1 - (embedding <=> query_vector)
-- 距離が小さいほど類似度が高い

