# プロジェクトフロー

## 📊 全体フロー

```
┌─────────────────────────────────────────────────────────────────┐
│                     プロジェクト全体フロー                        │
└─────────────────────────────────────────────────────────────────┘

【セットアップ】
    │
    ├─ 1. 環境変数ファイル作成 (.env)
    │
    ├─ 2. Docker Compose起動
    │   └─ PostgreSQL + pgAdmin コンテナ起動
    │
    ├─ 3. データベース初期化（自動）
    │   ├─ 拡張機能有効化 (pgvector, pg_trgm)
    │   ├─ テーブル作成 (products, product_stocks)
    │   ├─ インデックス作成 (ベクトル検索用含む)
    │   └─ サンプルデータ投入 (42件の商品)
    │
    └─ 4. Python環境セットアップ
        ├─ 仮想環境作成
        └─ ライブラリインストール

【ベクトル生成】
    │
    ├─ 1. 仮想環境有効化
    │
    ├─ 2. 環境変数設定 (.envから自動読み込み)
    │
    ├─ 3. ベクトル生成スクリプト実行
    │   ├─ モデル読み込み (intfloat/multilingual-e5-large)
    │   ├─ 商品データ取得 (embedding IS NULL)
    │   ├─ テキスト準備 (商品名 + 説明)
    │   ├─ プレフィックス追加 ("passage: ")
    │   ├─ ベクトル化 (1024次元 → 1536次元に調整)
    │   └─ データベース更新
    │
    └─ 4. 完了確認

【類似商品検索】
    │
    ├─ 1. 仮想環境有効化
    │
    ├─ 2. 環境変数設定 (.envから自動読み込み)
    │
    ├─ 3. 検索スクリプト実行
    │   ├─ クエリテキスト準備
    │   ├─ プレフィックス追加 ("query: ")
    │   ├─ クエリベクトル化
    │   ├─ 商品ベクトル取得
    │   ├─ コサイン類似度計算
    │   └─ 結果表示
    │
    └─ 4. 検索結果確認
```

## 🚀 セットアップフロー

```
┌─────────────────────────────────────────────────────────────────┐
│                      初回セットアップフロー                       │
└─────────────────────────────────────────────────────────────────┘

【ステップ1: 環境準備】
    │
    ├─ env.template を .env にコピー
    │
    └─ .env ファイルを編集
        ├─ POSTGRES_DB=vectordb
        ├─ POSTGRES_USER=postgres
        ├─ POSTGRES_PASSWORD=your_password
        └─ その他の設定

【ステップ2: データベース起動】
    │
    └─ docker-compose up -d
        │
        ├─ PostgreSQL コンテナ起動
        │   └─ 初期化スクリプト自動実行
        │       ├─ 01-init.sql (拡張機能)
        │       ├─ 02-tables.sql (テーブル)
        │       ├─ 03-indexes.sql (インデックス)
        │       └─ 04-seed-data.sql (サンプルデータ)
        │
        └─ pgAdmin コンテナ起動（オプション）

【ステップ3: Python環境セットアップ】
    │
    └─ .\setup\scripts\setup-venv.ps1 (Windows)
        │
        ├─ Python バージョン確認
        ├─ 仮想環境作成 (venv/)
        ├─ 仮想環境有効化
        ├─ pip アップグレード
        └─ ライブラリインストール
            ├─ sentence-transformers
            ├─ torch
            ├─ psycopg2-binary
            └─ numpy

【ステップ4: 動作確認】
    │
    ├─ データベース接続確認
    │   └─ docker exec -it postgres_db psql -U postgres -d vectordb
    │
    └─ サンプルデータ確認
        └─ SELECT COUNT(*) FROM products;
```

## 🔄 ベクトル生成フロー

```
┌─────────────────────────────────────────────────────────────────┐
│                      ベクトル生成フロー                           │
└─────────────────────────────────────────────────────────────────┘

【実行前準備】
    │
    ├─ 仮想環境有効化
    │   └─ .\venv\Scripts\Activate.ps1
    │
    └─ 環境変数確認
        └─ .envファイルから自動読み込み

【実行】
    │
    └─ python app/scripts/generate-embeddings.py
        │
        ├─ [1] データベース接続
        │   └─ psycopg2.connect(...)
        │
        ├─ [2] 商品データ取得
        │   └─ SELECT id, product_code, name, description
        │       FROM products
        │       WHERE embedding IS NULL
        │
        ├─ [3] モデル読み込み（初回のみ）
        │   └─ SentenceTransformer('intfloat/multilingual-e5-large')
        │       └─ モデルキャッシュに保存
        │
        ├─ [4] 各商品のベクトル生成
        │   │
        │   ├─ テキスト準備
        │   │   └─ "{商品名} {説明}"
        │   │
        │   ├─ プレフィックス追加
        │   │   └─ "passage: {テキスト}"
        │   │
        │   ├─ ベクトル化
        │   │   └─ model.encode(text, normalize_embeddings=True)
        │   │       └─ 1024次元のベクトル
        │   │
        │   ├─ 次元数調整
        │   │   └─ 1024次元 → 1536次元（ゼロパディング）
        │   │
        │   └─ データベース更新
        │       └─ UPDATE products SET embedding = %s::vector(1536)
        │
        └─ [5] 完了
            └─ コミット & 接続クローズ

【実行例】
    │
    └─ 出力例:
        ├─ データベースに接続しました: vectordb
        ├─ モデルを読み込み中: intfloat/multilingual-e5-large...
        ├─ （初回のみ時間がかかります）
        ├─ 42件の商品データにベクトルを生成します...
        ├─ ✓ EQUIP-001: ハンドピース 標準型...
        ├─ ✓ EQUIP-002: エアータービン 高速型...
        ├─ ...
        └─ 完了: 42件の商品データを更新しました。
```

## 🔍 類似商品検索フロー

```
┌─────────────────────────────────────────────────────────────────┐
│                      類似商品検索フロー                           │
└─────────────────────────────────────────────────────────────────┘

【実行前準備】
    │
    ├─ 仮想環境有効化
    │   └─ .\venv\Scripts\Activate.ps1
    │
    └─ 環境変数確認
        └─ .envファイルから自動読み込み

【実行】
    │
    └─ python app/scripts/search-similar-products.py "検索クエリ"
        │
        ├─ [1] データベース接続
        │   └─ psycopg2.connect(...)
        │
        ├─ [2] モデル読み込み（初回のみ）
        │   └─ SentenceTransformer('intfloat/multilingual-e5-large')
        │
        ├─ [3] クエリベクトル化
        │   │
        │   ├─ プレフィックス追加
        │   │   └─ "query: {検索クエリ}"
        │   │
        │   └─ ベクトル化
        │       └─ model.encode(query_text, normalize_embeddings=True)
        │           └─ 1024次元のベクトル → 1536次元に調整
        │
        ├─ [4] 商品ベクトル取得
        │   └─ SELECT id, product_code, name, description, price, embedding
        │       FROM products
        │       WHERE embedding IS NOT NULL
        │
        ├─ [5] 類似度計算
        │   │
        │   ├─ 商品ベクトルを配列に変換
        │   │   └─ PostgreSQL vector型 → numpy array
        │   │
        │   └─ コサイン類似度計算
        │       └─ np.dot(product_embeddings, query_embedding)
        │
        ├─ [6] 結果ソート
        │   └─ 類似度の降順でソート
        │
        └─ [7] 結果表示
            └─ 上位N件を表示（デフォルト: 10件）

【実行例】
    │
    └─ 出力例:
        ├─ データベースに接続しました: vectordb
        ├─ モデルを読み込み中: intfloat/multilingual-e5-large...
        ├─ （初回のみ時間がかかります）
        ├─ 検索中: 42件の商品から類似商品を検索...
        ├─
        ├─ 検索結果: 「ハンドピース」に類似した商品（上位10件）
        ├─ ================================================================================
        ├─ 類似度: 0.8558 | EQUIP-001 | ハンドピース 標準型
        ├─   説明: 高回転・低振動の標準ハンドピース。日常的な切削に最適。...
        ├─   価格: ¥125,000
        └─ ...
```

## 📦 データフロー

```
┌─────────────────────────────────────────────────────────────────┐
│                        データフロー                               │
└─────────────────────────────────────────────────────────────────┘

【商品データの流れ】
    │
    ├─ [初期データ]
    │   └─ setup/init-scripts/04-seed-data.sql
    │       └─ INSERT INTO products (...)
    │           └─ embedding = NULL
    │
    ├─ [ベクトル生成]
    │   └─ app/scripts/generate-embeddings.py
    │       ├─ 商品データ取得 (embedding IS NULL)
    │       ├─ テキスト準備: "{商品名} {説明}"
    │       ├─ プレフィックス追加: "passage: {テキスト}"
    │       ├─ ベクトル化: 1024次元
    │       ├─ 次元調整: 1536次元
    │       └─ UPDATE products SET embedding = vector(1536)
    │
    └─ [検索]
        └─ app/scripts/search-similar-products.py
            ├─ クエリ: "ハンドピース"
            ├─ プレフィックス追加: "query: ハンドピース"
            ├─ クエリベクトル化: 1024次元 → 1536次元
            ├─ 商品ベクトル取得: SELECT embedding FROM products
            ├─ 類似度計算: コサイン類似度
            └─ 結果: 類似度の高い順に表示

【ベクトルの変換】
    │
    ├─ テキスト
    │   └─ "ハンドピース 標準型 高回転・低振動..."
    │
    ├─ プレフィックス追加
    │   └─ "passage: ハンドピース 標準型 高回転・低振動..."
    │
    ├─ ベクトル化 (intfloat/multilingual-e5-large)
    │   └─ [0.123, -0.456, 0.789, ...] (1024次元)
    │
    ├─ 次元調整
    │   └─ [0.123, -0.456, 0.789, ..., 0.0, 0.0, 0.0] (1536次元)
    │
    └─ PostgreSQL vector型
        └─ "[0.123,-0.456,0.789,...]" (文字列形式)
```

## 🔄 日常的な使用フロー

```
┌─────────────────────────────────────────────────────────────────┐
│                    日常的な使用フロー                             │
└─────────────────────────────────────────────────────────────────┘

【新規商品追加時】
    │
    ├─ 1. 商品データをデータベースに追加
    │   └─ INSERT INTO products (product_code, name, description, ...)
    │
    ├─ 2. ベクトル生成
    │   └─ python app/scripts/generate-embeddings.py
    │       └─ embedding IS NULL の商品のみ処理
    │
    └─ 3. 完了

【商品検索時】
    │
    ├─ 1. 仮想環境有効化
    │   └─ .\venv\Scripts\Activate.ps1
    │
    ├─ 2. 検索実行
    │   └─ python app/scripts/search-similar-products.py "検索クエリ"
    │
    └─ 3. 結果確認

【バッチ処理（全商品再生成）】
    │
    ├─ 1. 既存ベクトルをクリア（オプション）
    │   └─ UPDATE products SET embedding = NULL;
    │
    ├─ 2. ベクトル再生成
    │   └─ python app/scripts/generate-embeddings.py
    │
    └─ 3. 完了
```

## 🛠️ トラブルシューティングフロー

```
┌─────────────────────────────────────────────────────────────────┐
│                  トラブルシューティングフロー                       │
└─────────────────────────────────────────────────────────────────┘

【問題: データベースに接続できない】
    │
    ├─ 1. Dockerコンテナの状態確認
    │   └─ docker ps
    │
    ├─ 2. コンテナが起動していない場合
    │   └─ docker-compose up -d
    │
    ├─ 3. 環境変数の確認
    │   └─ .envファイルのPOSTGRES_PASSWORDを確認
    │
    └─ 4. 接続テスト
        └─ docker exec -it postgres_db psql -U postgres -d vectordb

【問題: ベクトル生成が失敗する】
    │
    ├─ 1. モデルのダウンロード確認
    │   └─ ~/.cache/huggingface/ を確認
    │
    ├─ 2. メモリ不足の場合
    │   └─ システムのメモリ使用量を確認
    │
    ├─ 3. インターネット接続確認
    │   └─ 初回はモデルダウンロードが必要
    │
    └─ 4. ログ確認
        └─ エラーメッセージを確認

【問題: 検索結果が期待と異なる】
    │
    ├─ 1. ベクトルが生成されているか確認
    │   └─ SELECT COUNT(*) FROM products WHERE embedding IS NOT NULL;
    │
    ├─ 2. プレフィックスの確認
    │   └─ クエリには"query: "、商品には"passage: "が必要
    │
    └─ 3. 類似度の閾値調整
        └─ --min-similarity オプションで調整
```

## 📋 クイックリファレンス

### セットアップ（初回のみ）
```powershell
# 1. 環境変数ファイル作成
cp env.template .env
# .envを編集

# 2. データベース起動
docker-compose up -d

# 3. Python環境セットアップ
.\setup\scripts\setup-venv.ps1
```

### 日常的な使用
```powershell
# 1. 仮想環境有効化
.\venv\Scripts\Activate.ps1

# 2. ベクトル生成（新規商品追加時）
python app/scripts/generate-embeddings.py

# 3. 類似商品検索
python app/scripts/search-similar-products.py "ハンドピース"
```

### 対話型メニュー
```powershell
# 仮想環境有効化後
.\setup\scripts\run-example.ps1
```

