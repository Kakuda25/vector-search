# プロジェクト構造

## ディレクトリ構成

```
PostgreSQL/
├── setup/                          # 環境構築用
│   ├── init-scripts/               # データベース初期化スクリプト
│   │   ├── 01-init.sql            # 拡張機能の有効化
│   │   ├── 02-tables.sql          # テーブル作成
│   │   ├── 03-indexes.sql         # インデックス作成
│   │   ├── 04-seed-data.sql       # サンプルデータ
│   │   ├── 05-vector-migration.sql # 既存DB用マイグレーション
│   │   ├── 06-vector-search-examples.sql # ベクトル検索のサンプルクエリ
│   │   └── 07-add-embeddings.sql  # ベクトルデータ生成状況確認
│   ├── scripts/                    # 環境構築用スクリプト
│   │   ├── setup-venv.ps1         # 仮想環境セットアップ（Windows）
│   │   ├── setup-venv.sh          # 仮想環境セットアップ（Linux/Mac）
│   │   ├── align-postgres-password-with-env.ps1  # .env と DB の postgres パスワードを揃える（Windows）
│   │   ├── setup.sh                # セットアップスクリプト
│   │   ├── load-env.ps1           # 環境変数読み込み
│   │   └── run-example.ps1        # 対話型実行メニュー
│   └── examples/                   # サンプル・検証用スクリプト
│       └── e5-usage-example.py    # multilingual-e5-largeの使用例
│
├── app/                            # アプリケーション用
│   ├── __init__.py                 # パッケージ初期化ファイル
│   ├── scripts/                    # アプリケーション用スクリプト
│   │   ├── generate-embeddings.py  # ベクトル生成スクリプト
│   │   └── search-similar-products.py # 類似商品検索スクリプト
│   └── utils/                      # 共通ユーティリティ
│       ├── __init__.py
│       ├── database.py            # データベース接続
│       ├── env_loader.py          # 環境変数読み込み
│       └── vector_utils.py        # ベクトル処理
│
├── docker-compose.yml              # Docker Compose設定
├── env.template                    # 環境変数テンプレート
├── requirements.txt                # Python依存関係
├── README.md                       # プロジェクト説明
├── FLOW.md                         # プロジェクトフロー
└── order/                          # プロジェクト管理
    ├── description/                # 詳細説明
    ├── PROJECT.md                  # プロジェクト要件
    ├── TODO_README.md              # TODO管理説明
    ├── todo_list.json              # TODOリスト
    └── 初期化.md                    # コーディング規則
```

## ディレクトリの役割

### setup/ - 環境構築用

環境構築・セットアップ・テスト・検証に使用するファイルを格納。

- **init-scripts/**: データベース初期化スクリプト（Docker Compose起動時に自動実行）
- **scripts/**: 環境構築用スクリプト（仮想環境セットアップ、環境変数読み込みなど）
- **examples/**: サンプル・検証用スクリプト（動作確認用）

### app/ - アプリケーション用

アプリケーションで使用するコードを格納。

- **scripts/**: アプリケーション用スクリプト（ベクトル生成、検索など）
- **utils/**: 共通ユーティリティ（データベース接続、ベクトル処理など）

## 使用方法

### 環境構築

```powershell
# 1. 仮想環境セットアップ
.\setup\scripts\setup-venv.ps1

# 2. Docker Compose起動
docker-compose up -d

# 3. ベクトル生成（アプリケーション用スクリプト）
python app/scripts/generate-embeddings.py
```

### アプリケーション開発

```python
# アプリケーションコードから使用
from app.utils.database import create_connection
from app.utils.vector_utils import adjust_dimension
```

## 注意事項

- `setup/`ディレクトリは環境構築・テスト用のみ
- `app/`ディレクトリはアプリケーションで使用するコード
- 両者は明確に分離されているため、デプロイ時は`app/`のみをデプロイ可能

