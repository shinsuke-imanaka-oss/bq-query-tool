# main.py

import os
import pandas as pd
import streamlit as st
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import bigquery
from datetime import date, timedelta
import base64

from looker_handler import show_looker_studio_integration, show_filter_ui
from ui_components import show_analysis_workbench
from dashboard_analyzer import SHEET_ANALYSIS_QUERIES, get_ai_dashboard_comment

# 環境変数からGCPプロジェクトIDとロケーションを取得
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "vorn-digi-mktg-poc-635a")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")

# 背景画像のファイル名を定数として定義
BACKGROUND_IMAGE_FILE = "C:/Users/shinsuke-imanaka/bq-query-tool/本番用_v2/Image_tokiair.png"

def get_base64_of_bin_file(bin_file):
    """画像ファイルをBase64エンコードする"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

@st.cache_resource
def init_clients():
    """GCPのクライアント（Vertex AI, BigQuery）を初期化する"""
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model = GenerativeModel("gemini-2.0-flash-001")
        bq_client = bigquery.Client(project=PROJECT_ID)
        return bq_client, model
    except Exception as e:
        st.error(f"GCPクライアントの初期化中にエラーが発生しました: {e}")
        return None, None

def init_session_state():
    """アプリケーションで利用するセッション変数を初期化する"""
    defaults = {
        "sql": "", "df": pd.DataFrame(), "comment": "", "fig": None,
        "graph_cfg": {}, "is_looker_hidden": False, "editable_sql": "",
        "analysis_history": [],
        "apply_date_filter": True,
        "apply_media_filter": True,
        "apply_campaign_filter": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # looker_handler.py内のinit_filtersに処理を委譲
    from looker_handler import init_filters
    init_filters()

def main():
    """アプリケーションのメイン関数"""
    st.set_page_config(layout="wide")
    st.title("広告分析アプリ_トキエア")
    
    # 背景画像を削除したため、CSSのセクションを削除

    bq_client, model = init_clients()
    if not bq_client or not model:
        st.stop()

    init_session_state()

    st.session_state.bq_client = bq_client
    st.session_state.model = model

    with st.sidebar:
        st.header("表示モード切替")
        st.session_state.view_mode = st.radio(
            "表示モードを選択してください",
            ["📊 ダッシュボード表示", "🤖 AIアシスタント分析", "🤖 AIアシスタント分析（全画面）"],
            key="view_mode_selection"
        )
        st.markdown("---")

        st.header("レポートフィルタ")
        show_filter_ui(bq_client)

        st.markdown("---")
        st.header("📜 分析履歴")
        if not st.session_state.analysis_history:
            st.info("分析を実行すると履歴がここに表示されます。")
        else:
            for i, history in enumerate(reversed(st.session_state.analysis_history)):
                if isinstance(history, dict) and 'user_input' in history:
                    with st.expander(f"履歴{len(st.session_state.analysis_history) - i}: {history['user_input'][:20]}"):
                        st.caption(f"指示内容: {history['user_input']}")
                        if st.button(f"この分析を再現する", key=f"history_btn_{i}"):
                            st.session_state.user_input_main = history["user_input"]
                            st.session_state.sql = history["sql"]
                            st.session_state.editable_sql = history["sql"]
                            st.session_state.df = history["df"]
                            st.session_state.graph_cfg = history["graph_cfg"]
                            st.session_state.comment = history["comment"]
                            st.rerun()

    # メインコンテンツの表示
    if st.session_state.view_mode == "📊 ダッシュボード表示":
        st.info("AIによる深掘り分析は、左のサイドバーで「AIアシスタント分析」を選択してください。")
        show_looker_studio_integration(
            bq_client=st.session_state.bq_client,
            model=st.session_state.model,
            sheet_analysis_queries=SHEET_ANALYSIS_QUERIES
        )

    elif st.session_state.view_mode == "🤖 AIアシスタント分析":
        col_looker, col_analysis = st.columns([0.6, 0.4])
        with col_looker:
            with st.container(height=800):
                show_looker_studio_integration(
                    bq_client=st.session_state.bq_client,
                    model=st.session_state.model,
                    key_prefix="analysis_view",
                    sheet_analysis_queries=SHEET_ANALYSIS_QUERIES
                )
        with col_analysis:
            with st.container(height=800):
                show_analysis_workbench(sheet_analysis_queries=SHEET_ANALYSIS_QUERIES)
    
    elif st.session_state.view_mode == "🤖 AIアシスタント分析（全画面）":
        show_analysis_workbench(sheet_analysis_queries=SHEET_ANALYSIS_QUERIES)

if __name__ == "__main__":
    main()