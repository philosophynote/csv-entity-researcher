import os
import json
import time
from typing import Dict
import pandas as pd
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Firecrawl リモートMCPサーバーの設定
FIRECRAWL_MCP_SERVER_URL = "http://localhost:8080"  # デフォルト値、環境変数で上書き可能


class CompanyResearcher:
    def __init__(self, openai_api_key: str, firecrawl_server_url: str = None):
        self.client = OpenAI(api_key=openai_api_key)
        self.firecrawl_server_url = firecrawl_server_url or os.getenv(
            "FIRECRAWL_MCP_SERVER_URL", FIRECRAWL_MCP_SERVER_URL
        )

    def search_company_info(self, company_name: str, location: str = "") -> Dict:
        """
        FirecrawlリモートMCPサーバーを使用して企業情報を検索・収集する
        """
        search_query = company_name
        if location:
            search_query += f" {location}"

        # Response APIでリモートMCPサーバーとo3モデルを使用
        input_text = f"""
        以下の企業について詳細な情報をWEB検索で調査してください：{search_query}

        以下の項目について可能な限り詳しく情報を提供してください：
        1. 正式な企業名（corporation_name）
        2. 所在地・住所（address）
        3. 代表者名（daihyo_name）
        4. 企業公式サイトURL（corporation_url）
        5. サービス・製品サイトURL（service_url）
        6. 従業員数（employee_size）
        7. 資本金（capital）
        8. 設立年月日（established）
        9. 企業概要・事業内容（corporate_overview）
        10. 参考URL（source_urls）

        WEB検索を活用して最新の情報を取得し、回答は以下のJSON形式で提供してください。不明な項目は"不明"または空文字列にしてください：
        {{
            "corporation_name": "",
            "address": "",
            "daihyo_name": "",
            "corporation_url": "",
            "service_url": "",
            "employee_size": "",
            "capital": "",
            "established": "",
            "corporate_overview": "",
            "source_urls": ""
        }}
        """

        try:
            st.info(f"🔍 企業情報検索開始: {search_query}")

            # Response APIでリモートMCPサーバーとo3モデルを使用
            st.info("🤖 Response APIでo3モデル + リモートMCP実行中...")
            response = self.client.responses.create(
                model="gpt-4o-mini",
                input=input_text,
                tools=[
                    {
                        "type": "mcp",
                        "server_label": "firecrawl",
                        "server_url": self.firecrawl_server_url,
                        "require_approval": "never",
                    }
                ],
            )

            # レスポンスからJSON部分を抽出
            content = response.output_text
            st.success(f"✅ {search_query} の情報取得完了")

            # JSONの開始と終了を見つける
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                company_info = json.loads(json_str)

                # 検索クエリを追加
                company_info["search_query"] = search_query
                company_info["api_response_raw"] = content

                return company_info
            else:
                # JSONフォーマットが見つからない場合のフォールバック
                return {
                    "corporation_name": company_name,
                    "address": location,
                    "daihyo_name": "不明",
                    "corporation_url": "",
                    "service_url": "",
                    "employee_size": "不明",
                    "capital": "不明",
                    "established": "不明",
                    "corporate_overview": content,
                    "source_urls": "",
                    "search_query": search_query,
                    "api_response_raw": content,
                    "error": "JSON形式の解析に失敗",
                }

        except json.JSONDecodeError as e:
            st.error(f"📝 JSON解析エラー: {str(e)}")
            return {
                "corporation_name": company_name,
                "address": location,
                "daihyo_name": "不明",
                "corporation_url": "",
                "service_url": "",
                "employee_size": "不明",
                "capital": "不明",
                "established": "不明",
                "corporate_overview": "情報の取得に失敗しました",
                "source_urls": "",
                "search_query": search_query,
                "error": f"JSON解析エラー: {str(e)}",
            }
        except Exception as e:
            st.error(f"🚨 API呼び出しエラー: {str(e)}")
            return {
                "corporation_name": company_name,
                "address": location,
                "daihyo_name": "不明",
                "corporation_url": "",
                "service_url": "",
                "employee_size": "不明",
                "capital": "不明",
                "established": "不明",
                "corporate_overview": "情報の取得に失敗しました",
                "source_urls": "",
                "search_query": search_query,
                "error": f"API呼び出しエラー: {str(e)}",
            }

    def research_companies_from_csv(
        self, df: pd.DataFrame, progress_callback=None
    ) -> pd.DataFrame:
        """
        CSVから企業一覧を読み込み、各企業の情報を収集する
        """
        results = []
        total_companies = len(df)

        for index, row in df.iterrows():
            st.info(f"📊 進捗: {index + 1}/{total_companies} 企業を処理中...")

            if progress_callback:
                progress_callback(index + 1, total_companies)

            # CSVから企業名と所在地を取得
            company_name = ""
            location = ""

            # CSVの列名を柔軟に対応
            for col in df.columns:
                if any(
                    keyword in col.lower()
                    for keyword in ["name", "名", "企業", "company", "corporation"]
                ):
                    company_name = str(row[col]) if pd.notna(row[col]) else ""
                elif any(
                    keyword in col.lower()
                    for keyword in ["address", "住所", "所在", "location"]
                ):
                    location = str(row[col]) if pd.notna(row[col]) else ""

            if not company_name:
                # 最初の列を企業名として使用
                company_name = str(row.iloc[0]) if len(row) > 0 else ""

            if company_name:
                # 企業情報を収集
                company_info = self.search_company_info(company_name, location)
                results.append(company_info)

                # API制限を考慮して少し待機
                time.sleep(1)
            else:
                # 企業名が見つからない場合のデフォルト値
                results.append(
                    {
                        "corporation_name": "不明",
                        "address": "",
                        "daihyo_name": "不明",
                        "corporation_url": "",
                        "service_url": "",
                        "employee_size": "不明",
                        "capital": "不明",
                        "established": "不明",
                        "corporate_overview": "企業名が見つかりませんでした",
                        "source_urls": "",
                        "search_query": "",
                        "error": "企業名が見つからない",
                    }
                )

        return pd.DataFrame(results)


def get_openai_api_key():
    """
    OpenAI API KEYを取得する（環境変数またはStreamlitのsecrets）
    """
    # 環境変数から取得を試みる
    api_key = os.getenv("OPENAI_API_KEY")

    # Streamlitのsecretsから取得を試みる
    if not api_key and hasattr(st, "secrets"):
        try:
            api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass

    return api_key


def create_sample_csv():
    """
    サンプルCSVファイルを作成する
    """
    sample_data = {
        "corporation_name": ["株式会社サンプル", "テスト株式会社", "例示企業株式会社"],
        "address": ["東京都渋谷区", "大阪府大阪市", "神奈川県横浜市"],
    }

    return pd.DataFrame(sample_data)
