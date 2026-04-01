# PostgreSQL Docker環境（サンプルアプリ）

歯科医院向け商品マスタのサンプルアプリケーション用PostgreSQL環境です。

## 📋 目次

- [機能](#機能)
- [プロジェクト構造](#プロジェクト構造)
- [クイックスタート](#クイックスタート)
- [セットアップ](#セットアップ)
- [使用方法](#使用方法)
  - [基本的な操作](#基本的な操作)
  - [ベクトル検索のセットアップ](#ベクトル検索のセットアップ)
  - [データベースのバックアップとリストア](#データベースのバックアップとリストア)
  - [初期化スクリプト](#初期化スクリプト)
- [データベーススキーマ](#データベーススキーマ)
- [トラブルシューティング](#トラブルシューティング)

## ✨ 機能

- ✅ PostgreSQL 16 with pgvector - AIベクトル検索対応
- ✅ データの永続化（ボリューム）
- ✅ 初期化スクリプト対応
- ✅ pgAdmin 4（オプション）
- ✅ リソース制限設定
- ✅ ログローテーション
- ✅ セキュアな環境変数管理
- ✅ ベクトル検索（AI埋め込みベクトルによる類似度検索）

## 📁 プロジェクト構造

```
PostgreSQL/
├── docker-compose.yml          # Docker Compose設定ファイル
├── env.template                # 環境変数テンプレート
├── requirements.txt            # Python依存関係
├── README.md                   # このファイル
├── .gitignore                  # Git除外設定
│
├── setup/                      # 環境構築用
│   ├── init-scripts/           # データベース初期化スクリプト（自動実行順）
│   │   ├── 01-init.sql        # 拡張機能の有効化（pg_trgm, pgvector）
│   │   ├── 02-tables.sql      # テーブル作成（embeddingカラム含む）
│   │   ├── 03-indexes.sql     # インデックス作成（ベクトル検索用含む）
│   │   ├── 04-seed-data.sql   # サンプルデータ（42件の商品データ）
│   │   ├── 05-vector-migration.sql # 既存DB用マイグレーション（初回起動時は不要）
│   │   ├── 06-vector-search-examples.sql # ベクトル検索のサンプルクエリ（参考用）
│   │   └── 07-add-embeddings.sql # ベクトルデータ生成状況確認
│   ├── scripts/                # 環境構築用スクリプト
│   │   ├── setup-venv.ps1     # 仮想環境セットアップ（Windows PowerShell）
│   │   ├── setup-venv.sh      # 仮想環境セットアップ（Linux/Mac）
│   │   ├── setup.sh            # セットアップスクリプト
│   │   ├── load-env.ps1       # 環境変数読み込みヘルパー（PowerShell）
│   │   └── run-example.ps1    # 対話型実行メニュー（PowerShell）
│   └── examples/               # サンプル・検証用スクリプト
│       └── e5-usage-example.py # multilingual-e5-largeの使用例
│
└── app/                        # アプリケーション用
    ├── __init__.py             # パッケージ初期化ファイル
    ├── scripts/                # アプリケーション用スクリプト
    │   ├── generate-embeddings.py # ベクトル生成スクリプト
    │   └── search-similar-products.py # 類似商品検索スクリプト
    └── utils/                  # 共通ユーティリティ
        ├── __init__.py
        ├── database.py        # データベース接続
        ├── env_loader.py      # 環境変数読み込み
        └── vector_utils.py    # ベクトル処理
```

詳細は [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) を参照してください。

## 🚀 クイックスタート

**最短でベクトル検索を開始する方法:**

```powershell
# 1. 環境変数ファイルの作成
cp env.template .env
# .envファイルを編集してパスワードを設定

# 2. Docker Composeでデータベースを起動
docker-compose up -d

# 3. 仮想環境のセットアップ（初回のみ）
.\setup\scripts\setup-venv.ps1

# 4. 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# 5. ベクトルを生成
python app/scripts/generate-embeddings.py

# 6. 類似商品を検索
python app/scripts/search-similar-products.py "ハンドピース"

# 7. Web UIを起動
$env:POSTGRES_PASSWORD = "your_password"
python app/scripts/run-web-ui.py
# ブラウザで http://localhost:8000 を開く
```

## 🚀 セットアップ

### 1. 環境変数ファイルの作成

```bash
cp env.template .env
```

`.env`ファイルを編集して、パスワードなどの機密情報を設定してください。

```env
POSTGRES_DB=vectordb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432
```

### 2. Docker Composeで起動

```bash
docker-compose up -d
```

### 3. 動作確認

```bash
# データベースに直接接続
docker exec -it postgres_db psql -U postgres -d vectordb
```

### 4. Python環境のセットアップ（ベクトル生成用）

**Windows PowerShell:**

```powershell
# 仮想環境のセットアップ（初回のみ）
.\setup\scripts\setup-venv.ps1

# 仮想環境を有効化（毎回実行）
.\venv\Scripts\Activate.ps1

# 環境変数を設定
$env:POSTGRES_PASSWORD = "your_password"

# または、.envファイルから読み込む
Get-Content .env | ForEach-Object {
    if ($_ -match "^POSTGRES_PASSWORD=(.+)$") {
        $env:POSTGRES_PASSWORD = $matches[1]
    }
}
```

**Linux/Mac:**

```bash
# 仮想環境のセットアップ（初回のみ）
bash setup/scripts/setup-venv.sh

# 仮想環境を有効化（毎回実行）
source venv/bin/activate

# 環境変数を設定
export POSTGRES_PASSWORD="your_password"

# または、.envファイルから読み込む
export $(grep -v '^#' .env | xargs)
```

**注意**: 実行ポリシーのエラーが出る場合（Windows PowerShell）:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5. Web UI/APIの起動

Web管理画面（ダッシュボード/商品管理/類似検索/Embedding運用）を利用する場合は、以下を実行してください。

**Windows PowerShell:**

```powershell
# 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# DBパスワードを環境変数に設定（.envを使う場合は読み込みでも可）
$env:POSTGRES_PASSWORD = "your_password"

# Web UIサーバーを起動
python app/scripts/run-web-ui.py

# アクセス先
# http://localhost:8000
# 画面ルート例:
#   http://localhost:8000/#/dashboard
#   http://localhost:8000/#/products
#   http://localhost:8000/#/search
#   http://localhost:8000/#/operations
```

**Linux/Mac:**

```bash
# 仮想環境を有効化
source venv/bin/activate

# DBパスワードを環境変数に設定
export POSTGRES_PASSWORD="your_password"

# Web UIサーバーを起動
python app/scripts/run-web-ui.py

# アクセス先
# http://localhost:8000
```

**ベクトル検索機能の確認:**

```sql
-- 1. 拡張機能の確認
SELECT * FROM pg_extension WHERE extname IN ('vector', 'pg_trgm');

-- 2. productsテーブルの構造確認（embeddingカラムが存在することを確認）
\d products

-- 3. サンプルデータの確認
SELECT id, product_code, name, price FROM products LIMIT 5;

-- 4. ベクトルカラムの存在確認
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'products' AND column_name = 'embedding';

-- 5. ベクトル検索用インデックスの確認
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'products' AND indexname LIKE '%embedding%';
```

**期待される結果:**
- `vector`拡張機能が有効になっている
- `products`テーブルに`embedding vector(1536)`カラムが存在する
- ベクトル検索用のインデックス（`idx_products_embedding_hnsw`）が作成されている
- サンプルデータ（42件の商品、歯列矯正関連商品15件含む）が登録されている

## 📖 使用方法

### 基本的な操作

```bash
# コンテナの起動
docker-compose up -d

# コンテナの停止
docker-compose stop

# コンテナの停止と削除（データは保持）
docker-compose down

# コンテナの停止と削除（データも削除）
docker-compose down -v

# ログの確認
docker-compose logs -f postgres
```

### データベースのバックアップとリストア

#### バックアップ（手動）

**SQL形式（推奨）:**
```powershell
# .envファイルから環境変数を読み込む（PowerShell）
$env:PGPASSWORD = (Get-Content .env | Select-String "POSTGRES_PASSWORD" | ForEach-Object { $_.Line.Split('=')[1] })
$dbName = (Get-Content .env | Select-String "POSTGRES_DB" | ForEach-Object { $_.Line.Split('=')[1] }) -replace "vectordb", "vectordb"
if (-not $dbName) { $dbName = "vectordb" }
$user = (Get-Content .env | Select-String "POSTGRES_USER" | ForEach-Object { $_.Line.Split('=')[1] }) -replace "postgres", "postgres"
if (-not $user) { $user = "postgres" }

# バックアップ実行
docker exec -e PGPASSWORD=$env:PGPASSWORD postgres_db pg_dump -U $user -d $dbName --clean --if-exists --create > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
```

**カスタム形式（圧縮）:**
```powershell
# バックアップ実行
docker exec -e PGPASSWORD=$env:PGPASSWORD postgres_db pg_dump -U $user -d $dbName --format=custom --compress=9 --file=/tmp/backup.dump

# コンテナからホストにコピー
docker cp postgres_db:/tmp/backup.dump backup_$(Get-Date -Format "yyyyMMdd_HHmmss").dump

# コンテナ内の一時ファイルを削除
docker exec postgres_db rm -f /tmp/backup.dump
```

#### リストア（手動）

**⚠️ 警告: リストア操作は既存のデータベースを上書きします**

**SQL形式のリストア:**
```powershell
# .envファイルから環境変数を読み込む
$env:PGPASSWORD = (Get-Content .env | Select-String "POSTGRES_PASSWORD" | ForEach-Object { $_.Line.Split('=')[1] })
$user = (Get-Content .env | Select-String "POSTGRES_USER" | ForEach-Object { $_.Line.Split('=')[1] })
if (-not $user) { $user = "postgres" }

# バックアップファイルを指定（例: backup_20241209_120000.sql）
$backupFile = "backup_20241209_120000.sql"

# リストア実行
Get-Content $backupFile | docker exec -i -e PGPASSWORD=$env:PGPASSWORD postgres_db psql -U $user -d postgres
```

**圧縮SQL形式（.sql.gz）のリストア:**
```powershell
# バックアップファイルを指定（例: backup_20241209_120000.sql.gz）
$backupFile = "backup_20241209_120000.sql.gz"

# 解凍してリストア（gzipが必要な場合、WSLやGit Bashを使用）
# WSLを使用する場合:
wsl gunzip -c $backupFile | docker exec -i -e PGPASSWORD=$env:PGPASSWORD postgres_db psql -U $user -d postgres

# または、事前に解凍してから:
# gunzip $backupFile  # WSL/Git Bashで実行
# その後、上記のSQL形式のリストア手順を実行
```

**カスタム形式（.dump）のリストア:**
```powershell
# バックアップファイルを指定（例: backup_20241209_120000.dump）
$backupFile = "backup_20241209_120000.dump"

# コンテナにバックアップファイルをコピー
docker cp $backupFile postgres_db:/tmp/restore.dump

# リストア実行
docker exec -e PGPASSWORD=$env:PGPASSWORD postgres_db pg_restore -U $user --clean --if-exists --create --dbname=postgres /tmp/restore.dump

# または、既存のデータベースに直接リストアする場合:
docker exec -e PGPASSWORD=$env:PGPASSWORD postgres_db pg_restore -U $user --clean --if-exists --dbname=vectordb /tmp/restore.dump

# 一時ファイルを削除
docker exec postgres_db rm -f /tmp/restore.dump
```

**簡易版（環境変数が.envに正しく設定されている場合）:**
```powershell
# 1. コンテナが起動していることを確認
docker ps | Select-String "postgres_db"

# 2. バックアップファイルのパスを指定
$backupFile = "C:\path\to\your\backup.sql"  # 実際のパスに置き換え

# 3. リストア実行（POSTGRES_PASSWORDとPOSTGRES_USERを直接指定）
docker exec -i -e PGPASSWORD="your_password_here" postgres_db psql -U postgres -d postgres < $backupFile
```

**注意事項:**
- リストア前に既存のデータベースのバックアップを取ることを推奨します
- リストア中はデータベースへの接続を避けてください
- 大きなバックアップファイルの場合は、処理に時間がかかる場合があります

### 初期化スクリプト

`setup/init-scripts/` ディレクトリに `.sql` ファイルを配置すると、コンテナの初回起動時に自動実行されます。

- ファイル名は実行順序に影響します（01-init.sql → 02-tables.sql → 03-indexes.sql → 04-seed-data.sql）
- 既存のデータベースには実行されません（初回のみ）

**現在の構成:**
- `01-init.sql`: 拡張機能の有効化（pg_trgm, pgvector）
- `02-tables.sql`: 商品マスタテーブルと在庫テーブルの作成（embeddingカラム含む）
- `03-indexes.sql`: パフォーマンス最適化用インデックス（ベクトル検索用インデックス含む）
- `04-seed-data.sql`: サンプルデータ（歯科医院向け商品データ、歯列矯正関連商品含む）
- `05-vector-migration.sql`: ベクトル検索対応マイグレーション（既存DB用、初回起動時は不要）
- `06-vector-search-examples.sql`: ベクトル検索のサンプルクエリ（参考用）
- `07-add-embeddings.sql`: ベクトルデータ追加の説明と確認用スクリプト

**既存データベースにサンプルデータを投入する場合:**

初期化スクリプトは初回起動時のみ実行されるため、既存のデータベースにサンプルデータを投入する場合は手動で実行してください：

**方法1: ファイルをコンテナにコピーして実行（推奨・文字エンコーディング問題を回避）**
```powershell
# パスワードを設定（.envから読み込むか直接指定）
$password = (Get-Content .env | Select-String "POSTGRES_PASSWORD" | ForEach-Object { $_.Line.Split('=')[1] })
# または直接指定: $password = "your_password_here"

$dbName = (Get-Content .env | Select-String "POSTGRES_DB" | ForEach-Object { $_.Line.Split('=')[1] })
if (-not $dbName) { $dbName = "vectordb" }

# データベースの存在確認と作成（存在しない場合）
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d postgres -c "SELECT 1 FROM pg_database WHERE datname='$dbName'" | Select-String -Pattern "1" -Quiet
if (-not $?) {
    Write-Host "データベース '$dbName' が存在しないため、作成します..."
    docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d postgres -c "CREATE DATABASE $dbName;"
}

# テーブルが存在しない場合は作成（01-init.sql, 02-tables.sql, 03-indexes.sqlを順に実行）
Write-Host "テーブルを作成中..."
docker cp setup\init-scripts\01-init.sql postgres_db:/tmp/01-init.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/01-init.sql

docker cp setup\init-scripts\02-tables.sql postgres_db:/tmp/02-tables.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/02-tables.sql

docker cp setup\init-scripts\03-indexes.sql postgres_db:/tmp/03-indexes.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/03-indexes.sql

# サンプルデータを投入
Write-Host "サンプルデータを投入中..."
docker cp setup\init-scripts\04-seed-data.sql postgres_db:/tmp/seed-data.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/seed-data.sql

# 一時ファイルを削除
docker exec postgres_db rm -f /tmp/01-init.sql /tmp/02-tables.sql /tmp/03-indexes.sql /tmp/seed-data.sql

Write-Host "完了しました！"
```

**方法2: UTF-8エンコーディングを明示的に指定**
```powershell
# パスワードを設定
$password = (Get-Content .env | Select-String "POSTGRES_PASSWORD" | ForEach-Object { $_.Line.Split('=')[1] })
$dbName = (Get-Content .env | Select-String "POSTGRES_DB" | ForEach-Object { $_.Line.Split('=')[1] })
if (-not $dbName) { $dbName = "vectordb" }

# UTF-8エンコーディングを明示的に指定して実行
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-Content setup\init-scripts\04-seed-data.sql -Encoding UTF8 | docker exec -i -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName
```

**方法3: パスワードを直接指定（最も簡単）**
```powershell
# パスワードとデータベース名を設定
$password = "masterkey"
$dbName = "vectordb"

# データベースの存在確認と作成（存在しない場合）
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d postgres -c "SELECT 1 FROM pg_database WHERE datname='$dbName'" | Select-String -Pattern "1" -Quiet
if (-not $?) {
    Write-Host "データベース '$dbName' が存在しないため、作成します..."
    docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d postgres -c "CREATE DATABASE $dbName;"
}

# テーブルが存在しない場合は作成
Write-Host "テーブルを作成中..."
docker cp setup\init-scripts\01-init.sql postgres_db:/tmp/01-init.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/01-init.sql

docker cp setup\init-scripts\02-tables.sql postgres_db:/tmp/02-tables.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/02-tables.sql

docker cp setup\init-scripts\03-indexes.sql postgres_db:/tmp/03-indexes.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/03-indexes.sql

# サンプルデータを投入
Write-Host "サンプルデータを投入中..."
docker cp setup\init-scripts\04-seed-data.sql postgres_db:/tmp/seed-data.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/seed-data.sql

# 一時ファイルを削除
docker exec postgres_db rm -f /tmp/01-init.sql /tmp/02-tables.sql /tmp/03-indexes.sql /tmp/seed-data.sql

Write-Host "完了しました！"
```

## 📊 データベーススキーマ

### テーブル構成

**products（商品マスタ）**
- 商品コード、商品名、説明、価格、ステータスなど
- `embedding` カラム: AIで生成したベクトル（1536次元、デフォルト）

**product_stocks（在庫テーブル）**
- 商品ごとの在庫数を管理

### サンプルデータ

歯科医院向けの商品データ（42件）が初期データとして登録されます。
- 医療器具（ハンドピース、エアータービンなど）
- 材料（コンポジットレジン、印象材など）
- 薬品（消毒液、麻酔薬など）
- 消耗品（グローブ、マスクなど）
- 診療用品、X線関連用品
- **歯列矯正関連商品（15件）**
  - ブラケット（メタル、セラミック）
  - アーチワイヤー（ニッケルチタン、ステンレス）
  - リテーナー（ハーレー型、クリアリテーナー）
  - エラスティック、バンド
  - 矯正用セメント
  - インビザライン、ヘッドギアなど

## 🔍 ベクトル検索（AI検索）

### 概要

pgvector拡張機能を使用して、AIで生成した埋め込みベクトルによる類似度検索が可能です。商品名や説明文をベクトル化し、意味的な類似性に基づいた検索ができます。

**✅ 初回起動時からベクトル検索対応済み**

`docker-compose up -d`で起動すると、自動的に以下が設定されます：
- `vector`拡張機能の有効化
- `products`テーブルに`embedding vector(1536)`カラムの作成
- ベクトル検索用インデックス（HNSW）の作成

### スクリプトの説明

#### 主要スクリプト

| スクリプト名 | 説明 | 使用方法 |
|------------|------|---------|
| `generate-embeddings.py` | 商品データのベクトル生成 | `python app/scripts/generate-embeddings.py` |
| `search-similar-products.py` | 類似商品検索 | `python app/scripts/search-similar-products.py "検索クエリ"` |
| `run-web-ui.py` | Web UI/APIサーバー起動 | `python app/scripts/run-web-ui.py` |
| `e5-usage-example.py` | multilingual-e5-largeの使用例 | `python setup/examples/e5-usage-example.py` |

#### セットアップスクリプト

| スクリプト名 | 説明 | 使用方法 |
|------------|------|---------|
| `setup-venv.ps1` | 仮想環境セットアップ（Windows） | `.\setup\scripts\setup-venv.ps1` |
| `setup-venv.sh` | 仮想環境セットアップ（Linux/Mac） | `bash setup/scripts/setup-venv.sh` |
| `load-env.ps1` | 環境変数読み込み（PowerShell） | `. .\setup\scripts\load-env.ps1` |
| `run-example.ps1` | 対話型実行メニュー | `.\setup\scripts\run-example.ps1` |

### セットアップ

**既存データベースにベクトルカラムを追加する場合:**

既存のデータベースにベクトル検索機能を追加する場合は、`05-vector-migration.sql`を使用してください：

```powershell
$password = "masterkey"
$dbName = "vectordb"

# ベクトル拡張機能の有効化とマイグレーション
docker cp setup\init-scripts\05-vector-migration.sql postgres_db:/tmp/vector-migration.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/vector-migration.sql

# ベクトル検索用インデックスの作成（03-indexes.sqlに含まれています）
docker cp setup\init-scripts\03-indexes.sql postgres_db:/tmp/03-indexes.sql
docker exec -e PGPASSWORD=$password postgres_db psql -U postgres -d $dbName -f /tmp/03-indexes.sql

docker exec postgres_db rm -f /tmp/vector-migration.sql /tmp/03-indexes.sql
```

**ベクトルデータの生成と投入:**

商品名と説明を`intfloat/multilingual-e5-large`でベクトル化し、`embedding`カラムに保存します。

### 使用モデル

**intfloat/multilingual-e5-large**
- 次元数: 1024（1536次元に自動調整）
- 特徴: 高精度、多言語対応、日本語に強い
- JMTEB平均スコア: 70.90（2024-2025評価）
- 100以上の言語をサポートし、日本語を含む多言語テキスト埋め込みに適しています
- 商品検索のような実用的な用途において、現時点で最適な選択肢と評価されています

**注意**: 
- モデルの出力は1024次元ですが、スクリプトは自動的に1536次元に調整します
- 最適な結果を得るには、テーブルの`embedding`カラムの次元数を1024に変更することを推奨します

### クイックスタート（Sentence Transformers）

**最短で始める方法（Windows PowerShell）:**

```powershell
# 1. 仮想環境のセットアップとライブラリのインストール
.\setup\scripts\setup-venv.ps1

# 2. 環境変数を設定（.envファイルから読み込む場合）
Get-Content .env | ForEach-Object {
    if ($_ -match "^POSTGRES_PASSWORD=(.+)$") {
        $env:POSTGRES_PASSWORD = $matches[1]
    }
}

# または直接設定
$env:POSTGRES_PASSWORD = "your_password"

# 3. ベクトルを生成（最推奨モデル）
python scripts/generate-embeddings.py --sentence-transformers --sentence-model intfloat/multilingual-e5-large
```

**最短で始める方法（Linux/Mac）:**

```bash
# 1. 仮想環境のセットアップとライブラリのインストール
bash setup/scripts/setup-venv.sh

# 2. 環境変数を設定
export POSTGRES_PASSWORD="your_password"

# 3. ベクトルを生成（最推奨モデル）
python app/scripts/generate-embeddings.py --model intfloat/multilingual-e5-large
```

**対話型メニューで実行（Windows PowerShell）:**

```powershell
# 仮想環境のセットアップ（初回のみ）
.\setup\scripts\setup-venv.ps1

# 実行メニューを起動
.\setup\scripts\run-example.ps1
```

これだけで、すべての商品データにベクトルが生成されます！

### ベクトル生成方法

#### セットアップ

```bash
# 1. 必要なライブラリをインストール
pip install -r requirements.txt

# または個別にインストール
pip install sentence-transformers torch psycopg2-binary numpy

# 2. 環境変数を設定（.envファイルから読み込むか、直接設定）
export POSTGRES_PASSWORD="your_password"
# オプション: 他の接続情報を設定（デフォルト値を使用する場合は不要）
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="vectordb"
export POSTGRES_USER="postgres"
```

#### 基本的な使用方法

```bash
# ベクトルを生成（intfloat/multilingual-e5-largeを使用）
python app/scripts/generate-embeddings.py
```

#### 実行の流れ

1. **初回実行時**: モデルが自動的にダウンロードされます（数分かかる場合があります）
   - モデルは `~/.cache/huggingface/` に保存されます
   - 2回目以降はキャッシュから読み込まれるため高速です

2. **ベクトル生成**: 商品データを読み込み、各商品の名前と説明をベクトル化します

3. **データベース更新**: 生成したベクトルを`products`テーブルの`embedding`カラムに保存します

#### 実行例

```bash
# 実行例
$ python app/scripts/generate-embeddings.py

データベースに接続しました: vectordb
モデルを読み込み中: intfloat/multilingual-e5-large...
（初回のみ時間がかかります）
42件の商品データにベクトルを生成します...
✓ EQUIP-001: ハンドピース 標準型...
✓ EQUIP-002: エアータービン 高速型...
...
完了: 42件の商品データを更新しました。
```

#### トラブルシューティング

**問題1: モデルのダウンロードが遅い**
- 初回のみ時間がかかります（数GBのモデルファイルをダウンロード）
- インターネット接続を確認してください
- モデルは一度ダウンロードするとキャッシュされます

**問題2: メモリ不足エラー**
- システムのメモリを確認してください
- 必要に応じて、バッチサイズを調整（スクリプトを修正）

**問題3: 次元数の不一致**
- モデルの出力は1024次元ですが、スクリプトは自動的に1536次元に調整します
- 最適な結果を得るには、テーブルの`embedding`カラムの次元数を1024に変更することを推奨

**テーブルの次元数を変更する方法:**

```sql
-- 1024次元に変更（multilingual-e5-large用）
ALTER TABLE products 
ALTER COLUMN embedding TYPE vector(1024);
```

**注意**: 次元数を変更する前に、既存のベクトルデータをバックアップすることを推奨します。

**問題4: データベース接続エラー**
- `.env`ファイルまたは環境変数で`POSTGRES_PASSWORD`が正しく設定されているか確認
- Dockerコンテナが起動しているか確認: `docker ps`
- 接続情報（ホスト、ポート、データベース名）を確認

**問題5: ModuleNotFoundError: No module named 'app'**
- スクリプトは自動的にプロジェクトルートをPythonパスに追加するため、通常は発生しません
- プロジェクトルートから実行していることを確認してください
- それでもエラーが発生する場合は、`app/__init__.py`が存在することを確認してください

#### PowerShellでの実行

```powershell
# 環境変数を設定
$env:POSTGRES_PASSWORD = "your_password"

# ベクトルを生成
python app/scripts/generate-embeddings.py
```

| 用途 | 推奨モデル | 理由 |
|------|-----------|------|
| **最高精度が必要** | `intfloat/multilingual-e5-large` | 日本語に強く、高精度（JMTEB 70.90、2024-2025評価） |
| **日本語特化** | `pkshatech/GLuCoSE-base-ja` | 日本語専用に最適化 |
| **軽量・高速** | `paraphrase-multilingual-MiniLM-L12-v2` | メモリ使用量が少ない |
| **バランス重視** | `intfloat/multilingual-e5-large` | 精度と速度のバランスが良い（2024-2025評価） |
| **商品検索用途** | `intfloat/multilingual-e5-large` | 実用的な用途で最適（推奨） |

#### カスタムモデルの使用

Hugging Faceで公開されている他のSentence Transformersモデルも使用可能です：

```bash
# カスタムモデルを指定
python app/scripts/generate-embeddings.py --model "your-model-name"
```

モデルはHugging Face Hubから自動的にダウンロードされます。

#### Pythonコードで直接使用する方法

スクリプトを使わずに、Pythonコードから直接Sentence Transformersを使用することも可能です：

**基本的な使用例:**

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# モデルを読み込み
model = SentenceTransformer('intfloat/multilingual-e5-large')

# ⚠️ 重要: multilingual-e5-largeを使用する場合、プレフィックスが必要です
# - 検索クエリ: "query: " を使用
# - 商品説明など: "passage: " を使用
sentences = [
    "query: ハンドピース",  # 検索クエリ
    "passage: ハンドピース 標準型 高回転・低振動の標準ハンドピース。日常的な切削に最適。",
    "passage: エアータービン 高速型 最高回転数40万回転の高速エアータービン。精密な切削が可能。",
    "passage: コンポジットレジン A2 審美性の高いコンポジットレジン。A2色。"
]

embeddings = model.encode(sentences, normalize_embeddings=True)

# 類似度を計算（コサイン類似度）
similarities = model.similarity(embeddings, embeddings)
print(similarities.shape)  # [4, 4] - 4x4の類似度マトリックス

# 類似度マトリックスの表示
print(similarities)
# 対角成分は1.0（自分自身との類似度）
# 非対角成分は商品間の類似度（0.0～1.0の値）
```

**公式ドキュメントの方法（transformersライブラリを使用）:**

```python
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel

def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

# プレフィックスを付けたテキスト
input_texts = [
    'query: ハンドピース',
    'query: 歯科用の切削器具',
    "passage: ハンドピース 標準型 高回転・低振動の標準ハンドピース。日常的な切削に最適。",
    "passage: エアータービン 高速型 最高回転数40万回転の高速エアータービン。精密な切削が可能。"
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
scores = (embeddings[:2] @ embeddings[2:].T) * 100
print(scores.tolist())
```

**プレフィックスの使い分け:**

| タスクの種類 | プレフィックス | 使用例 |
|------------|--------------|--------|
| **検索クエリ** | `query: ` | `"query: ハンドピース"` |
| **商品説明など** | `passage: ` | `"passage: ハンドピース 標準型..."` |
| **類似度計算（対称）** | `query: ` | 両方に`query: `を使用 |
| **特徴量として使用** | `query: ` | `"query: 商品名 説明"` |

**注意**: プレフィックスを付けないと性能が低下します。詳細は[公式ドキュメント](https://huggingface.co/intfloat/multilingual-e5-large)を参照してください。

**クエリと商品の類似度計算（正しい方法）:**

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('intfloat/multilingual-e5-large')

# 検索クエリ（query: プレフィックスを追加）
query = "query: 歯科用の切削器具"

# 商品データ（passage: プレフィックスを追加）
products = [
    "passage: ハンドピース 標準型 高回転・低振動の標準ハンドピース。日常的な切削に最適。",
    "passage: エアータービン 高速型 最高回転数40万回転の高速エアータービン。精密な切削が可能。",
    "passage: コンポジットレジン A2 審美性の高いコンポジットレジン。A2色。"
]

# ベクトル化
query_embedding = model.encode([query], normalize_embeddings=True)
product_embeddings = model.encode(products, normalize_embeddings=True)

# 類似度を計算
similarities = model.similarity(query_embedding, product_embeddings)[0]

# 結果を表示
for i, (product, similarity) in enumerate(zip(products, similarities)):
    # プレフィックスを除いて表示
    product_name = product.replace("passage: ", "")
    print(f"{i+1}. 類似度: {similarity:.4f} | {product_name[:50]}...")
```

**詳細な使用例:**

```bash
# 公式ドキュメントに基づいた完全な例を実行
python setup/examples/e5-usage-example.py
```

**データベースに保存する例:**

```python
from sentence_transformers import SentenceTransformer
import psycopg2

# モデルを読み込み
model = SentenceTransformer('intfloat/multilingual-e5-large')

# テキストをベクトル化
text = "ハンドピース 標準型 高回転・低振動の標準ハンドピース。日常的な切削に最適。"
embedding = model.encode(text, normalize_embeddings=True)

# データベースに接続
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="vectordb",
    user="postgres",
    password="your_password"
)

# ベクトルをデータベースに保存
cursor = conn.cursor()
embedding_str = "[" + ",".join(map(str, embedding)) + "]"
cursor.execute("""
    UPDATE products 
    SET embedding = %s::vector(1024)
    WHERE product_code = 'EQUIP-001'
""", (embedding_str,))
conn.commit()
```

**実践的な使用例:**

詳細な使用例は `setup/examples/e5-usage-example.py` を参照してください：

```bash
python setup/examples/e5-usage-example.py
```

#### バッチ処理の最適化

大量の商品データを処理する場合、バッチ処理で高速化できます：

```python
from sentence_transformers import SentenceTransformer
import psycopg2

model = SentenceTransformer('intfloat/multilingual-e5-large')
conn = psycopg2.connect(...)
cursor = conn.cursor()

# 商品データを取得
cursor.execute("SELECT id, name, description FROM products WHERE embedding IS NULL")
products = cursor.fetchall()

# テキストを準備
texts = [f"{name} {description or ''}" for _, name, description in products]

# バッチでベクトル化（高速）
embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

# データベースに一括更新
for (product_id, _, _), embedding in zip(products, embeddings):
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    cursor.execute("""
        UPDATE products 
        SET embedding = %s::vector(1024)
        WHERE id = %s
    """, (embedding_str, product_id))

conn.commit()
```


**方法2: 手動でベクトルを更新**

```sql
-- 例: ベクトルを更新
UPDATE products 
SET embedding = '[0.1,0.2,0.3,...]'::vector(1536)
WHERE id = 1;
```

**方法3: アプリケーション側で生成**

商品名と説明を結合したテキストをAIモデルでベクトル化し、アプリケーション側で`UPDATE`文を実行して`embedding`カラムを更新します。

### 類似度検索の実行

ベクトルが生成されたら、類似商品を検索できます：

**方法1: 検索スクリプトを使用（推奨）**

```bash
# テキストクエリで類似商品を検索
python app/scripts/search-similar-products.py "ハンドピース"

# 結果数を指定
python app/scripts/search-similar-products.py "歯科用器具" --limit 5

# 最小類似度を指定
python app/scripts/search-similar-products.py "切削器具" --min-similarity 0.7

# 特定の商品と類似した商品を検索
python app/scripts/search-similar-products.py --compare-products --product-id 1
```

**方法2: Pythonコードで直接使用**

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('intfloat/multilingual-e5-large')

# クエリと商品のベクトルを取得
query = "歯科用の切削器具"
products = ["ハンドピース...", "エアータービン...", ...]

query_embedding = model.encode([query], normalize_embeddings=True)
product_embeddings = model.encode(products, normalize_embeddings=True)

# 類似度を計算
similarities = model.similarity(query_embedding, product_embeddings)[0]

# 類似度でソート
sorted_indices = similarities.argsort()[::-1]
for idx in sorted_indices[:5]:  # 上位5件
    print(f"類似度: {similarities[idx]:.4f} | {products[idx]}")
```

詳細な使用例は `setup/examples/e5-usage-example.py` を参照してください。

### ベクトル検索の使用例

**1. コサイン類似度による検索（推奨）:**

```sql
-- クエリベクトルと最も類似した商品を検索
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
```

**2. 類似度閾値を設定した検索:**

```sql
-- コサイン類似度が0.7以上の商品のみを取得
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
```

**3. ハイブリッド検索（ベクトル検索 + 条件フィルタ）:**

```sql
-- ベクトル検索と通常の条件を組み合わせ
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
```

### ベクトル演算子

- `<=>` : コサイン距離（1 - コサイン類似度）
- `<->` : ユークリッド距離（L2距離）
- `<#>` : 負の内積（内積の符号を反転）

**コサイン類似度の計算:**
```sql
-- コサイン類似度 = 1 - (embedding <=> query_vector)
-- 距離が小さいほど類似度が高い
```

### ベクトル次元数の変更

デフォルトは1536次元（OpenAI text-embedding-ada-002など）ですが、使用するAIモデルに応じて変更できます：

```sql
-- 例: 768次元に変更（多くの多言語モデルで使用）
ALTER TABLE products 
ALTER COLUMN embedding TYPE vector(768);
```

### 参考

- [pgvector公式ドキュメント](https://github.com/pgvector/pgvector)
- サンプルクエリ: `setup/init-scripts/06-vector-search-examples.sql` を参照

## 🔧 トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs postgres

# コンテナの状態を確認
docker ps -a
```

### データベースに接続できない

```bash
# コンテナ内で直接確認
docker exec -it postgres_db psql -U postgres

# または接続確認
docker exec postgres_db pg_isready -U postgres
```

### ホスト（Python/pgAdmin）から `password authentication failed` になる

既存の `postgres_data` ボリュームがある場合、データディレクトリ作成時に設定された `postgres` ユーザのパスワードが、現在の `.env` の `POSTGRES_PASSWORD` と一致しないことがあります。コンテナ内の `psql` は `trust` などでパスワードなしでも通ることがあり、気づきにくいです。

**対処（推奨）:** プロジェクトルートで PowerShell を開き、次を実行します。

```powershell
.\setup\scripts\align-postgres-password-with-env.ps1
```

**手動で揃える例:**

```bash
docker exec postgres_db psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD 'your_password_here';"
```

（`your_password_here` は `.env` の `POSTGRES_PASSWORD` と同じ値にしてください。）

### コンテナ名 `postgres_db` が既に使われている

別の Compose や古いコンテナが残っていると `Conflict. The container name "/postgres_db" is already in use` になります。不要なコンテナを削除するか、`docker compose down` などで整理してから再度 `docker compose up -d` してください。

### `volume ... already exists but was created for project "..."` と表示される

名前付きボリュームを過去の Compose プロジェクトで作成したことが原因です。データを維持したまま使う場合は、警告のみで動作に問題がないことが多いです。本リポジトリの `docker-compose.yml` 先頭に `name: vector-search` を指定し、プロジェクト名を固定しています。

### パスワードを忘れた

```bash
# コンテナを停止
docker-compose down

# ボリュームを削除（⚠️ データが失われます）
docker volume rm postgres_data

# .envファイルのパスワードを更新
# コンテナを再起動
docker-compose up -d
```

### ディスク容量の問題

```bash
# ボリュームのサイズ確認
docker system df -v

# 不要なリソースの削除
docker system prune -a --volumes
```

## 📚 参考リンク

- [PostgreSQL公式ドキュメント](https://www.postgresql.org/docs/)
- [Docker Compose公式ドキュメント](https://docs.docker.com/compose/)
- [pgvector公式ドキュメント](https://github.com/pgvector/pgvector)
- [multilingual-e5-large (Hugging Face)](https://huggingface.co/intfloat/multilingual-e5-large)
- [Sentence Transformers公式ドキュメント](https://www.sbert.net/)

## 📝 関連ドキュメント

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - プロジェクト構造の詳細
- [FLOW.md](FLOW.md) - プロジェクトフロー（セットアップ、実行、データフロー）

