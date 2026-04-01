# UI実装計画（6-UI設計.md対応）

## 目的

`order/description/6-UI設計.md` のMVPを、既存のPython資産（DB接続・ベクトル生成・類似検索ロジック）を再利用しながら、最短で動くWeb UIとして実装する。

## 実装方針

- バックエンドは `FastAPI` を採用し、REST APIと静的UI配信を同一プロセスで提供する。
- 既存の `app/utils/database.py` と `app/scripts/search-similar-products.py` の処理を流用して実装コストを抑える。
- UIはまずMVPに必要な1画面ダッシュボード形式で提供し、タブ切り替えで主要機能にアクセスできる構成にする。
- レスポンシブは `1400px / 1024px / 768px` の3段階で調整する。

## ステップ

1. **API基盤の実装**
   - `app/api/main.py` を作成
   - ヘルスチェック、商品一覧、類似検索、Embeddingジョブ起動のエンドポイントを追加
   - Pydanticモデルで入出力契約を固定

2. **Embeddingジョブ管理の実装**
   - バックグラウンドジョブ状態をインメモリ管理
   - `all/missing` モードで生成実行
   - 進捗・失敗件数・失敗理由を取得可能にする

3. **Web UIの実装**
   - `app/web/index.html`, `styles.css`, `app.js` を作成
   - 画面: ダッシュボード / 商品管理 / 類似検索 / Embedding運用 / システム状態
   - API連携と状態表示（loading / empty / error）を実装

4. **起動導線の整備**
   - `requirements.txt` にWeb関連依存を追加
   - `app/scripts/run-web-ui.py` を追加して起動を簡素化

5. **動作確認**
   - APIヘルス確認
   - 主要画面のデータ表示確認
   - 類似検索・Embeddingジョブの実行確認

