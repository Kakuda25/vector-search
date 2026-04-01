# UI設計（PostgreSQL Vector Search 管理画面）

## 1. 目的

- CLI中心の現行運用を、ブラウザ上で完結できる運用UIに置き換える。
- 商品データ管理、Embedding生成、類似検索、障害切り分けを単一UIで提供する。
- PC/タブレット対応を前提とし、`1400px` 付近でもレイアウト崩れなく運用できる画面設計にする。

## 2. 対象範囲（MVP）

- 商品一覧/詳細表示（`products`）
- Embedding状態の確認・生成ジョブ起動・進捗確認
- 類似検索（商品起点 / 自由テキスト起点）
- システムヘルス確認（DB接続、pgvector有効性、API稼働）

## 3. 情報設計（IA）

1. ダッシュボード
2. 商品管理
3. 類似検索
4. Embedding運用
5. システム状態

将来拡張:
- 権限管理
- 監査ログ
- 検索結果保存
- 品質評価データセット管理

## 4. 主要ユーザーフロー

### フローA: 商品起点の類似検索

1. 商品一覧で対象商品を選択
2. 類似検索画面へ遷移し、商品IDを引き継ぎ
3. `topK` と `scoreThreshold` を調整して実行
4. 候補比較後、必要に応じてEmbedding再生成へ遷移

### フローB: 未生成Embeddingの復旧

1. ダッシュボードで未生成件数を確認
2. Embedding運用で「未生成のみ生成」を実行
3. 失敗一覧を確認し、個別再実行

### フローC: 自由テキストで検証検索

1. 類似検索でクエリ文字列を入力
2. 検索条件を設定して実行
3. 結果確認と条件再調整を繰り返す

## 5. 画面別設計

## 5.1 ダッシュボード

- 目的: 現在の運用状態を短時間で把握
- 主要要素:
  - KPIカード（総商品数、Embedding生成済み、未生成、直近ジョブ結果）
  - 直近ジョブ進捗
  - クイックアクション（未生成のみ生成、類似検索へ）
- 状態設計:
  - ロード: スケルトン表示
  - 空: 初回導入メッセージ
  - エラー: 接続失敗 + 再試行

## 5.2 商品管理

- 目的: 商品データとEmbedding状態を保守
- 主要要素:
  - テーブル（ID、商品コード、商品名、カテゴリ、Embedding状態、更新日時）
  - フィルタ（全件/生成済み/未生成/失敗）
  - 詳細パネル（右ペインまたは下段）
  - 行アクション（詳細、再生成）
- 状態設計:
  - ロード: 行スケルトン
  - 空: 該当0件メッセージ + 条件解除導線
  - エラー: 取得失敗 + 再読込

## 5.3 類似検索

- 目的: 類似候補比較と業務判断支援
- 主要要素:
  - 入力タブ（商品選択 / 自由テキスト）
  - 条件（`topK`, `scoreThreshold`, `category`）
  - 結果リスト（rank、score、商品名、カテゴリ、説明）
  - 比較ビュー（2件比較）
- 状態設計:
  - ロード: 結果スケルトン
  - 空: 閾値見直し案内
  - エラー: 実行内容保持 + 再試行

## 5.4 Embedding運用

- 目的: 生成処理を安全に運用
- 主要要素:
  - 実行フォーム（全件/未生成のみ/失敗のみ）
  - ジョブ進捗（成功・失敗・残件）
  - 失敗一覧（理由、再試行）
- 状態設計:
  - ロード: 履歴読込表示
  - 空: ジョブ未実行案内
  - エラー: 起動失敗/進捗取得失敗の分離表示

## 5.5 システム状態

- 目的: 障害切り分けをUIで完結
- 主要要素:
  - DB接続状態
  - pgvector有効状態
  - APIヘルス
  - requestId表示つきエラー詳細

## 6. レイアウト・レスポンシブ

- ブレークポイント:
  - `>= 1400px`: 高密度2カラム（一覧 + 詳細）
  - `1024px - 1399px`: 中間密度（詳細はドロワー）
  - `768px - 1023px`: タブレット1カラム
- 1400px対策:
  - テーブル列の優先表示制御
  - KPIカード 4列 -> 2列への切替
  - 比較ビューを横並びから縦積みに自動変更

## 7. コンポーネント設計（実装単位）

- レイアウト: `AppShell`, `SideNav`, `TopBar`, `PageHeader`
- 共通表示: `StatCard`, `StatusBadge`, `DataTable`, `EmptyState`, `ErrorState`, `SkeletonBlock`
- 操作: `SearchForm`, `FilterChips`, `ActionToolbar`, `ConfirmDialog`
- ドメイン:
  - `ProductTable`, `ProductDetailPanel`
  - `SimilarityQueryPanel`, `SimilarityResultList`, `SimilarityComparePanel`
  - `EmbeddingJobPanel`, `JobProgressBar`, `FailedItemsList`

## 8. API契約案

### Products

- `GET /api/products`
  - query: `q`, `category`, `embeddingStatus`, `page`, `limit`, `sort`
- `GET /api/products/:id`

### Embeddings

- `POST /api/embeddings/jobs`
  - body: `{ mode: "all" | "missing" | "failed", productIds?: string[] }`
- `GET /api/embeddings/jobs/:jobId`
- `GET /api/embeddings/failures?jobId=...`

### Similarity

- `POST /api/similarity/search`
  - 商品起点: `{ type: "product", productId, topK, scoreThreshold, category? }`
  - テキスト起点: `{ type: "text", text, topK, scoreThreshold, category? }`

### System

- `GET /api/system/health`

### 共通エラー

- `{ code, message, details?, requestId }`

## 9. 状態設計ルール（共通）

- ロード時はスケルトン表示でレイアウトシフトを防止
- 空状態は原因別文言を使い分ける（未登録/条件不一致/未実行）
- エラーは軽微（再試行）と重大（問い合わせ用requestId提示）を分離

## 10. MVPと将来拡張

### MVP

- ダッシュボード
- 商品管理
- 類似検索
- Embedding運用
- システム状態
- レスポンシブ（1400px, 1024px, 768px）

### 将来拡張

- 結果保存・共有
- 品質評価ワークフロー
- 権限管理・監査ログ
- CSV連携

## 11. 実装ステップ

1. API契約の固定（OpenAPI化）
2. 画面骨格（`AppShell` と共通状態コンポーネント）実装
3. 商品管理 -> 類似検索 -> Embedding運用の順で機能接続
4. 最後にレスポンシブ調整（1400/1024/768）と運用動作確認

