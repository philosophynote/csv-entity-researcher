# プロジェクト知見集

## ライブラリ選定
- pandas
  - csvファイルの読み込みとデータフレーム操作
- openai
  - openai APIとの通信
- streamlit
  - ユーザーインターフェースの構築

## コード品質管理

- **ruff**: Pythonのリンター・フォーマッター
  - コードの品質チェックと自動フォーマット
  - 実行: `uv run ruff check` / `uv run ruff format`
  
- **pre-commit**: Git commitフック
  - commit前に自動的にruffでコードチェック・フォーマットを実行
  - 設定ファイル: `.pre-commit-config.yaml`