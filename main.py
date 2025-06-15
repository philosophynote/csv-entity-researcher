import streamlit as st
import pandas as pd
import io
from company_research import CompanyResearcher, get_openai_api_key, create_sample_csv


def main():
    st.title("CSV Entity Researcher")
    st.markdown(
        "CSV経由で企業一覧をimportし、記載された企業の情報をWEBから収集するツール"
    )

    # タブで機能を分割
    tab1, tab2 = st.tabs(["メイン機能", "デバッグ"])

    with tab1:
        # OpenAI API設定
        api_key = get_openai_api_key()

        if not api_key:
            st.warning("OpenAI API Keyが設定されていません")
            api_key_input = st.text_input(
                "OpenAI API Keyを入力してください", type="password"
            )
            if api_key_input:
                api_key = api_key_input
        else:
            st.success("OpenAI API Key が設定されています")

        # CSVファイルアップロード
        uploaded_file = st.file_uploader(
            "企業一覧CSVファイルをアップロード", type=["csv"]
        )

        # サンプルCSVダウンロード
        col1, col2 = st.columns(2)
        with col1:
            if st.button("サンプルCSVをダウンロード"):
                sample_df = create_sample_csv()
                csv_buffer = io.StringIO()
                sample_df.to_csv(csv_buffer, index=False, encoding="utf-8")
                st.download_button(
                    label="sample_companies.csv",
                    data=csv_buffer.getvalue(),
                    file_name="sample_companies.csv",
                    mime="text/csv",
                )

        if uploaded_file is not None:
            # CSVファイルを読み込み
            df = pd.read_csv(uploaded_file)
            st.subheader("アップロードされたデータ")
            st.dataframe(df)

            # 企業情報収集ボタン
            if st.button("企業情報を収集") and api_key:
                with st.spinner("企業情報を収集中..."):
                    try:
                        researcher = CompanyResearcher(api_key)

                        # プログレスバー
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        def progress_callback(current, total):
                            progress = current / total
                            progress_bar.progress(progress)
                            status_text.text(f"進行状況: {current}/{total} 企業")

                        # 企業情報収集実行
                        results_df = researcher.research_companies_from_csv(
                            df, progress_callback
                        )

                        st.success("企業情報の収集が完了しました")

                        # 結果表示
                        st.subheader("収集結果")
                        st.dataframe(results_df)

                        # CSVダウンロード機能
                        csv_buffer = io.StringIO()
                        results_df.to_csv(csv_buffer, index=False, encoding="utf-8")

                        st.download_button(
                            label="結果をCSVでダウンロード",
                            data=csv_buffer.getvalue(),
                            file_name="company_research_results.csv",
                            mime="text/csv",
                        )

                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")
            elif not api_key:
                st.warning("企業情報を収集するにはOpenAI API Keyが必要です")

    with tab2:
        st.subheader("デバッグモード")

        # OpenAI API設定（デバッグ用）
        debug_api_key = get_openai_api_key()
        if not debug_api_key:
            debug_api_key_input = st.text_input(
                "デバッグ用OpenAI API Key", type="password", key="debug_api"
            )
            if debug_api_key_input:
                debug_api_key = debug_api_key_input

        # 単一企業での検索テスト
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("企業名を入力", placeholder="例: 株式会社〇〇")
        with col2:
            company_location = st.text_input("所在地を入力", placeholder="例: 東京都")

        if st.button("単体テスト実行"):
            if company_name and debug_api_key:
                search_query = f"{company_name}"
                if company_location:
                    search_query += f" {company_location}"

                with st.spinner(f"'{search_query}'の情報を収集中..."):
                    try:
                        researcher = CompanyResearcher(debug_api_key)
                        company_info = researcher.search_company_info(
                            company_name, company_location
                        )

                        st.success(f"'{search_query}'の情報収集が完了しました")

                        # 結果表示
                        st.subheader("収集結果")
                        st.json(company_info)

                        # 詳細表示
                        if "error" not in company_info:
                            st.subheader("詳細情報")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(
                                    "**企業名:**",
                                    company_info.get("corporation_name", "不明"),
                                )
                                st.write(
                                    "**住所:**", company_info.get("address", "不明")
                                )
                                st.write(
                                    "**代表者:**",
                                    company_info.get("daihyo_name", "不明"),
                                )
                                st.write(
                                    "**従業員数:**",
                                    company_info.get("employee_size", "不明"),
                                )
                                st.write(
                                    "**設立:**", company_info.get("established", "不明")
                                )
                            with col2:
                                st.write(
                                    "**公式サイト:**",
                                    company_info.get("corporation_url", "不明"),
                                )
                                st.write(
                                    "**サービスサイト:**",
                                    company_info.get("service_url", "不明"),
                                )
                                st.write(
                                    "**資本金:**", company_info.get("capital", "不明")
                                )
                                if company_info.get("corporate_overview"):
                                    st.write("**企業概要:**")
                                    st.write(company_info.get("corporate_overview", ""))
                        else:
                            st.error(
                                f"エラー: {company_info.get('error', '不明なエラー')}"
                            )

                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")

            elif not company_name:
                st.warning("企業名を入力してください")
            elif not debug_api_key:
                st.warning("OpenAI API Keyが必要です")

        # デバッグ情報表示
        st.subheader("デバッグ情報")
        debug_info = {
            "Streamlit Version": st.__version__,
            "Pandas Version": pd.__version__,
            "OpenAI API Key Status": "設定済み" if debug_api_key else "未設定",
            "Company Research Module": "利用可能",
        }
        st.json(debug_info)


if __name__ == "__main__":
    main()
