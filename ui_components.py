# ui_components.py
import streamlit as st
import io
import pandas as pd
from charting import render_plotly_chart
from analysis_logic import run_analysis_flow, generate_ai_comment, rerun_sql_flow, modify_and_rerun_sql_flow

ANALYSIS_RECIPES = {
    "自由入力": "",
    "週次パフォーマンスサマリー": "過去7日間の主要KPI（コスト、インプレッション、クリック、コンバージョン、CVR、CPA）について、日別の推移と合計値を集計し、パフォーマンスを要約してください。",
    "成果の良いキャンペーンTop5": "先月のデータから、コンバージョン数が最も多いキャンペーンを5つ抽出し、その主要KPIをまとめてください。",
    "メディア別コスト比較": "今月のコストをメディア（ServiceNameJA_Media）別に集計し、円グラフで可視化してください。",
    "デバイス別パフォーマンス比較": "先月の実績をデバイスカテゴリ別（PC, スマートフォン, タブレット）に集計し、デバイスごとのコンバージョン数とCPAを比較してください。"
    }

def show_analysis_workbench(sheet_analysis_queries):
    """右側の分析ワークベンチUIを描画する"""
    st.header("🤖 AIアシスタント分析")

    st.markdown("---")
    st.markdown("##### AI分析へのフィルタ適用設定")
    cols = st.columns(3)
    with cols[0]:
        st.checkbox("期間", key="apply_date_filter")
    with cols[1]:
        st.checkbox("メディア", key="apply_media_filter")
    with cols[2]:
        st.checkbox("キャンペーン", key="apply_campaign_filter")
    st.markdown("---")

    if "updated_user_input" in st.session_state:
        st.session_state.user_input_main = st.session_state.updated_user_input
        del st.session_state.updated_user_input

    tab1, tab2, tab3 = st.tabs(["① 指示・対話", "② 結果・グラフ", "③ SQL・データ"])

    with tab1:
        st.subheader("分析の開始")
        recipe_selection = st.selectbox("分析レシピを選択:", options=ANALYSIS_RECIPES.keys())

        if st.session_state.get('recipe_selection_old') != recipe_selection:
            st.session_state.user_input_main = ANALYSIS_RECIPES[recipe_selection]
        st.session_state.recipe_selection_old = recipe_selection

        user_input = st.text_area("分析指示:", key="user_input_main", height=150)

        if st.button("分析を実行する", type="primary"):
            run_analysis_flow(
                user_input,
                st.session_state.filters,
                st.session_state.apply_date_filter,
                st.session_state.apply_media_filter,
                st.session_state.apply_campaign_filter,
                sheet_analysis_queries
            )
            st.session_state.editable_sql = st.session_state.get("sql", "")

        if not st.session_state.get("df", pd.DataFrame()).empty:
            with st.expander("実行結果プレビュー ＆ 対話で分析を修正", expanded=True):
                st.dataframe(st.session_state.df.head())

                with st.form(key="modification_form"):
                    modification_instruction = st.text_area(
                        "追加・修正の指示:",
                        placeholder="例：メディアで絞って、CVRの高い順に並び替えてください",
                        key="modification_instruction_tab1"
                    )
                    submitted = st.form_submit_button("↑ この指示で修正して実行")
                    if submitted:
                        modify_and_rerun_sql_flow(
                            original_sql=st.session_state.sql,
                            instruction=modification_instruction,
                            filters=st.session_state.filters,
                            apply_date=st.session_state.apply_date_filter,
                            apply_media=st.session_state.apply_media_filter,
                            apply_campaign=st.session_state.apply_campaign_filter
                        )

                        if modification_instruction:
                            st.session_state.updated_user_input = f"{user_input}\n\n# 修正指示:\n{modification_instruction}"

                        st.rerun()

    with tab2:
        if not st.session_state.get("df", pd.DataFrame()).empty:
            st.subheader("📈 分析結果")

            with st.expander("グラフ設定の表示/変更", expanded=True):
                cfg = st.session_state.get("graph_cfg", {})
                df = st.session_state.df
                df_columns = df.columns.tolist()
                numeric_cols = df.select_dtypes(include='number').columns.tolist()

                cfg_cols1 = st.columns(3)
                with cfg_cols1[0]:
                    chart_options = ["棒グラフ", "折れ線グラフ", "組合せグラフ", "面グラフ", "散布図", "円グラフ"]
                    cfg["main_chart_type"] = st.selectbox("グラフの種類", chart_options, index=chart_options.index(cfg.get("main_chart_type", "棒グラフ")))
                with cfg_cols1[1]:
                    cfg["x_axis"] = st.selectbox("X軸", df_columns, index=df_columns.index(cfg.get("x_axis", df_columns[0])))
                with cfg_cols1[2]:
                    cfg["y_axis_left"] = st.selectbox("Y軸 (左)", numeric_cols, index=numeric_cols.index(cfg.get("y_axis_left", numeric_cols[0])))

                cfg_cols2 = st.columns(2)
                with cfg_cols2[0]:
                    if cfg["main_chart_type"] == "組合せグラフ":
                        right_axis_options = ["なし"] + [col for col in numeric_cols if col != cfg["y_axis_left"]]
                        selected_right = cfg.get("y_axis_right")
                        right_index = right_axis_options.index(selected_right) if selected_right in right_axis_options else 0
                        cfg["y_axis_right"] = st.selectbox("Y軸 (右)", right_axis_options, index=right_index)
                    else:
                        cfg["y_axis_right"] = None
                with cfg_cols2[1]:
                    legend_options = ["なし"] + [col for col in df_columns if col not in [cfg["x_axis"], cfg["y_axis_left"], cfg.get("y_axis_right")]]
                    selected_legend = cfg.get("legend_col")
                    legend_index = legend_options.index(selected_legend) if selected_legend in legend_options else 0
                    cfg["legend_col"] = st.selectbox("凡例 (色分け)", legend_options, index=legend_index)

            st.session_state.graph_cfg = cfg
            st.session_state.fig = render_plotly_chart(st.session_state.df, st.session_state.graph_cfg)
            st.plotly_chart(st.session_state.fig, use_container_width=True)

            st.markdown("##### 🤖 AIによる分析コメント")
            st.info(st.session_state.comment)

            action_cols = st.columns(2)
            with action_cols[0]:
                if st.button("コメントを再生成"):
                    st.session_state.comment = generate_ai_comment(st.session_state.model, st.session_state.df, st.session_state.graph_cfg)
                    st.rerun()
            with action_cols[1]:
                if st.button("この分析を履歴に保存", icon="💾"):
                    user_input_for_history = st.session_state.get("user_input_main", "手動修正による分析")
                    history_entry = { "user_input": user_input_for_history, "sql": st.session_state.sql, "df": st.session_state.df, "graph_cfg": st.session_state.graph_cfg, "comment": st.session_state.comment }
                    st.session_state.analysis_history.append(history_entry)
                    if len(st.session_state.analysis_history) > 10: st.session_state.analysis_history.pop(0)
                    st.toast("現在の分析を履歴に保存しました！", icon="✅")
        else:
            st.info("「① 指示・対話」タブから分析を実行してください。")

    with tab3:
        if not st.session_state.get("df", pd.DataFrame()).empty:
            st.subheader("🔍 SQLと生データ")
            with st.expander("SQLの確認・修正 ▼", expanded=False):
                st.code(st.session_state.get("sql", ""), language="sql")
                edited_sql = st.text_area("SQLを直接編集して再実行できます:", value=st.session_state.get("editable_sql", ""), height=150, key="sql_edit_area")
                if st.button("SQLを直接修正して再実行"):
                    rerun_sql_flow(
                        edited_sql,
                        st.session_state.filters,
                        st.session_state.apply_date_filter,
                        st.session_state.apply_media_filter,
                        st.session_state.apply_campaign_filter,
                        sheet_analysis_queries
                    )
            with st.expander("テーブルデータとダウンロード"):
                st.dataframe(st.session_state.df)
                dl_cols = st.columns(2)
                with dl_cols[0]:
                    df_csv = st.session_state.df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button("CSV形式でDL", df_csv, "result.csv", "text/csv")
                with dl_cols[1]:
                    excel_buf = io.BytesIO()
                    st.session_state.df.to_excel(excel_buf, index=False, sheet_name="Result", engine="xlsxwriter")
                    st.download_button("Excel形式でDL", excel_buf, "result.xlsx")
        else:
            st.info("分析を実行すると、ここにSQLとデータが表示されます。")