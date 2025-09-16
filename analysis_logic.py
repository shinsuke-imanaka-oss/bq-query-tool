# analysis_logic.py
import streamlit as st
import pandas as pd
import json
import traceback
from prompts import select_best_prompt, MODIFY_SQL_TEMPLATE

MAX_ATTEMPTS = 3

def json_converter(o):
    import datetime, decimal
    if isinstance(o, (datetime.date, datetime.datetime)): return o.isoformat()
    if isinstance(o, decimal.Decimal): return float(o)
    return str(o)

def generate_ai_comment(model, df: pd.DataFrame, graph_cfg: dict) -> str:
    try:
        sample = df.head(10).to_dict(orient="records")
        chart_type = graph_cfg.get('main_chart_type', '未選択')
        analysis_focus = f"「{chart_type}」で可視化しています。"
        if legend_col := graph_cfg.get('legend_col'):
            if legend_col != "なし":
                analysis_focus += f" 「{legend_col}」でグループ化しています。"
        prompt = f"""
        以下のデータサンプルとグラフ設定に基づき、ビジネス上の示唆を含む簡潔な分析コメントを出してください。
        [データサンプル]
        {json.dumps(sample, ensure_ascii=False, default=json_converter)}
        [グラフ設定]
        {analysis_focus}
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ AIコメント生成でエラー: {e}"

def generate_sql(model, prompt_text):
    response = model.generate_content(
        prompt_text, generation_config={"temperature": 0, "max_output_tokens": 1024}
    )
    return response.text.strip().replace("```sql", "").replace("```", "").strip()

def execute_bigquery_with_retry(bq_client, model, sql_query):
    for attempt in range(MAX_ATTEMPTS):
        try:
            return sql_query, bq_client.query(sql_query).to_dataframe(), True
        except Exception as e:
            error_msg = str(e)
            if "403 Forbidden" in error_msg:
                 st.error("BigQueryへのアクセス権限がありません。")
                 return sql_query, pd.DataFrame(), False
            if attempt + 1 == MAX_ATTEMPTS:
                st.error(f"SQL修正を{MAX_ATTEMPTS}回試みましたが解決できませんでした。")
                return sql_query, pd.DataFrame(), False
            st.warning(f"SQLエラー発生。AIが修正を試みます... ({attempt + 1}/{MAX_ATTEMPTS})")
            correction_prompt = f"以下のSQLはエラーになりました。エラーメッセージを参考に修正してください。\n# SQL:\n{sql_query}\n# エラー:\n{error_msg}\n# 出力は修正後のSQLのみ"
            sql_query = generate_sql(model, correction_prompt)
    return sql_query, pd.DataFrame(), False

def build_where_clause(filters: dict, apply_date: bool, apply_media: bool, apply_campaign: bool, prefix: str = "WHERE") -> str:
    """フィルタ辞書と適用フラグからSQLのWHERE句またはAND句を構築する"""
    where_conditions = []
    if apply_date and "start_date" in filters and "end_date" in filters:
        start, end = filters["start_date"].strftime('%Y-%m-%d'), filters["end_date"].strftime('%Y-%m-%d')
        where_conditions.append(f"Date BETWEEN '{start}' AND '{end}'")

    if apply_media and filters.get("media"):
        media_list = ", ".join([f"'{m}'" for m in filters["media"]])
        where_conditions.append(f"ServiceNameJA_Media IN ({media_list})")

    if apply_campaign and filters.get("campaigns"):
        campaign_list = ", ".join([f"'{c}'" for c in filters["campaigns"]])
        where_conditions.append(f"CampaignName IN ({campaign_list})")

    # 条件が何もなければ空文字を返す
    if not where_conditions:
        return ""

    # prefix を付けて条件を連結する
    return f" {prefix} " + " AND ".join(where_conditions)

def run_analysis_flow(user_input: str, filters: dict, apply_date: bool, apply_media: bool, apply_campaign: bool):
    """分析指示から一連の処理を実行する"""
    bq_client, model = st.session_state.bq_client, st.session_state.model
    try:
        with st.spinner("GeminiがSQLを生成中です..."):
            info = select_best_prompt(user_input)
            if not info:
                st.error("分析対象のテーブルが見つかりませんでした。"); return

            # フィルタ条件を文字列として構築
            filter_context = build_where_clause(filters, apply_date, apply_media, apply_campaign)

            # フィルタが指定されている場合のみ、プロンプトに条件を組み込む
            if filter_context:
                prompt = info["template"].format(user_input=user_input)
                prompt_with_filter = f"{prompt}\n#追加のフィルタ条件:\n#以下のWHERE句を必ずSQLに含めてください。\n#`{filter_context}`"
                generated_sql = generate_sql(model, prompt_with_filter)
            else:
                # フィルタが指定されていない場合は、元のプロンプトでSQLを生成
                prompt = info["template"].format(user_input=user_input)
                generated_sql = generate_sql(model, prompt)

        with st.spinner("BigQueryでSQLを実行中です..."):
            final_sql, df, is_success = execute_bigquery_with_retry(bq_client, model, generated_sql)

            if is_success:
                st.session_state.sql, st.session_state.df = final_sql, df
                if df.empty:
                    st.warning("クエリは成功しましたが、結果データが0件でした。")
                else:
                    numeric_cols = df.select_dtypes(include='number').columns
                    y_axis_default = numeric_cols[0] if not numeric_cols.empty else (df.columns[1] if len(df.columns) > 1 else None)
                    if y_axis_default:
                        cfg = {"main_chart_type": "棒グラフ", "x_axis": df.columns[0], "y_axis_left": y_axis_default, "y_axis_right": "なし", "legend_col": "なし"}
                        st.session_state.graph_cfg = cfg
                        st.session_state.comment = generate_ai_comment(model, df, cfg)
                        st.success("分析完了！")
                        history_entry = {"user_input": user_input, "sql": final_sql, "df": df, "graph_cfg": cfg, "comment": st.session_state.comment}
                        st.session_state.analysis_history.append(history_entry)
                        if len(st.session_state.analysis_history) > 10: st.session_state.analysis_history.pop(0)
                    else:
                        st.warning("グラフ化に適した数値データが見つかりませんでした。")
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")

def rerun_sql_flow(sql_query: str, filters: dict, apply_date: bool, apply_media: bool, apply_campaign: bool):
    """ユーザーが修正したSQLを再実行する"""
    bq_client, model = st.session_state.bq_client, st.session_state.model
    try:
        with st.spinner("修正されたSQLをBigQueryで実行中です..."):
            # この関数ではフィルタを直接SQLに適用しないが、将来的な拡張性のために引数は維持
            df = bq_client.query(sql_query).to_dataframe()
            st.session_state.sql, st.session_state.df = sql_query, df
            if not df.empty:
                numeric_cols = df.select_dtypes(include='number').columns
                y_axis_default = numeric_cols[0] if not numeric_cols.empty else (df.columns[1] if len(df.columns) > 1 else None)
                if y_axis_default:
                    cfg = {"main_chart_type": "棒グラフ", "x_axis": df.columns[0], "y_axis_left": y_axis_default, "y_axis_right": "なし", "legend_col": "なし"}
                    st.session_state.graph_cfg = cfg
                    st.session_state.comment = generate_ai_comment(model, df, cfg)
                else:
                    st.warning("グラフ化に適した数値データが見つかりませんでした。")
            st.success("SQLの再実行完了！")
    except Exception as e:
        st.error(f"SQLの実行中にエラーが発生しました: {e}")

def modify_and_rerun_sql_flow(original_sql: str, instruction: str, filters: dict, apply_date: bool, apply_media: bool, apply_campaign: bool):
    """AIによるSQLの修正と再実行を行う"""
    bq_client, model = st.session_state.bq_client, st.session_state.model
    if not instruction:
        st.warning("修正指示が入力されていません。"); return
    try:
        with st.spinner("GeminiがSQLを修正中です..."):
            # この関数ではフィルタを直接SQLに適用しないが、将来的な拡張性のために引数は維持
            prompt = MODIFY_SQL_TEMPLATE.format(original_sql=original_sql, modification_instruction=instruction)
            modified_sql = generate_sql(model, prompt)
        
        with st.spinner("修正されたSQLをBigQueryで実行中です..."):
            final_sql, df, is_success = execute_bigquery_with_retry(bq_client, model, modified_sql)
            if is_success:
                st.session_state.sql, st.session_state.df, st.session_state.editable_sql = final_sql, df, final_sql
                if not df.empty:
                    numeric_cols = df.select_dtypes(include='number').columns
                    y_axis_default = numeric_cols[0] if not numeric_cols.empty else (df.columns[1] if len(df.columns) > 1 else None)
                    if y_axis_default:
                        cfg = {"main_chart_type": "棒グラフ", "x_axis": df.columns[0], "y_axis_left": y_axis_default, "y_axis_right": "なし", "legend_col": "なし"}
                        st.session_state.graph_cfg = cfg
                        st.session_state.comment = generate_ai_comment(model, df, cfg)
                    else:
                        st.warning("グラフ化に適した数値データが見つかりませんでした。")
                st.success("SQLの修正・再実行が完了しました！")
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")