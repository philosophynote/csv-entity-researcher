# プロジェクトコンテキスト

## 概要

- プロジェクト名: CSV Entity Researcher
- 技術スタック: Python, OpenAI Response API, Pandas, Streamlit
- 目標: CSV経由で企業情報を収集し、分析結果をCSVに出力するツールの開発

## 制約条件
- CSVファイルの読み込みと書き出し
  - CSVのテンプレートは`template/entities.csv`に存在
- CSVから企業名と企業所在地を抽出
- デバックのため、画面から企業名と企業所在地を入力可能
- WEBで収集する項目は次の通り:
  - 企業名
  - 企業所在地
  - コーポレートサイトURL
  - サービスURL
  - 設立年
  - 従業員数
  - 代表者名
  - 資本金
  - 企業概要
  - 情報元URL
- 収集が終わったら、CSVに出力

## 技術選定理由
- Python: データ処理と分析に最適
- OpenAI Response API: 簡単にWEB検索などを統合可能なLLMAPI
- Pandas: データ操作と分析に強力なライブラリ
- Streamlit: データアプリケーションの迅速な構築に最適