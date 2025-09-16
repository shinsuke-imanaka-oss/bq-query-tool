# looker_handler.py

import streamlit as st
import json
from urllib.parse import quote
import datetime
import pandas as pd
from dashboard_analyzer import get_ai_dashboard_comment
import os

# --- レポート基本情報 ---
REPORT_ID = os.environ.get("LOOKER_REPORT_ID")
if not REPORT_ID:
    st.error("環境変数LOOKER_REPORT_IDが設定されていません。")
    st.stop()
    
REPORT_SHEETS = {
    "予算管理": "Gcf9",
    "サマリー01": "6HI9",
    "サマリー02": "IH29",
    "メディア": "GTrk",
    "デバイス": "kovk",
    "月別": "Bsvk",
    "日別": "40vk",
    "曜日": "hsv3",
    "キャンペーン": "cYwk",
    "広告グループ": "1ZWq",
    "テキストCR": "NfWq",
    "ディスプレイCR": "p_grkcjbbytd",
    "キーワード": "imWq",
    "地域": "ZNdq",
    "時間": "bXdq",
    "最終ページURL": "7xXq",
    "性別": "ctdq",
    "年齢": "fX53",
}

@st.cache_data(ttl=43200)
def get_filter_options(_bq_client, table_id, column_name):
    """BigQueryからフィルタの選択肢を取得する"""
    try:
        query = f"SELECT DISTINCT {column_name} FROM `{table_id}` WHERE {column_name} IS NOT NULL ORDER BY {column_name}"
        return _bq_client.query(query).to_dataframe()[column_name].tolist()
    except Exception as e:
        st.error(f"フィルタオプションの取得中にエラーが発生しました ({column_name}): {e}")
        return []

def init_filters():
    """filtersセッションの初期化"""
    if "filters" not in st.session_state:
        st.session_state.filters = {}

    defaults = {
        "sheet": "メディア",
        "start_date": datetime.date.today() - datetime.timedelta(days=30),
        "end_date": datetime.date.today(),
        "media": [],
        "campaigns": []
    }

    for key, value in defaults.items():
        if key not in st.session_state.filters:
            st.session_state.filters[key] = value

def show_filter_ui(bq_client):
    """サイドバーに表示するフィルタUIを構築し、結果をsession_stateに保存する"""
    init_filters()

    # シート選択
    sheet_names = list(REPORT_SHEETS.keys())
    selected_sheet_name = st.selectbox(
        "表示するレポートシートを選択:",
        sheet_names,
        index=sheet_names.index(st.session_state.filters.get("sheet", "メディア")),
    )
    st.session_state.filters["sheet"] = selected_sheet_name
    
    st.markdown("---")

    # 日付入力
    start_date = st.date_input("開始日", value=st.session_state.filters["start_date"])
    end_date = st.date_input("終了日", value=st.session_state.filters["end_date"])

    table_id_for_filters = "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign"
    media_options = get_filter_options(bq_client, table_id_for_filters, "ServiceNameJA_Media")
    campaign_options = get_filter_options(bq_client, table_id_for_filters, "CampaignName")

    selected_media = st.multiselect(
        "メディア",
        options=media_options,
        default=st.session_state.filters["media"]
    )
    selected_campaigns = st.multiselect(
        "キャンペーン",
        options=campaign_options,
        default=st.session_state.filters["campaigns"]
    )

    # 選択状態を保存
    st.session_state.filters.update({
        "start_date": start_date,
        "end_date": end_date,
        "media": selected_media,
        "campaigns": selected_campaigns
    })

def show_looker_studio_integration(bq_client, model, key_prefix=""):
    init_filters()  # filters初期化

    selected_page_id = REPORT_SHEETS[st.session_state.filters["sheet"]]

    params = {}
    filters = st.session_state.filters
    if "start_date" in filters and "end_date" in filters:
        params["p_start_date"] = filters["start_date"].strftime("%Y%m%d")
        params["p_end_date"] = filters["end_date"].strftime("%Y%m%d")
    if filters.get("media"):
        params["p_media"] = ",".join(filters["media"])
    if filters.get("campaigns"):
        params["p_campaign"] = ",".join(filters["campaigns"])

    # URL生成
    params_json = json.dumps(params)
    encoded_params = quote(params_json)
    base_url = f"https://lookerstudio.google.com/embed/reporting/{REPORT_ID}"
    final_url = f"{base_url}/page/{selected_page_id}?params={encoded_params}"

    # ★★★ ここにデバッグ用のコードを追加 ★★★
    st.subheader("💡 デバッグ情報")
    st.write(f"**生成されたURL:** `{final_url}`")
    st.write(f"**パラメータ辞書:** `{params}`")
    st.markdown("---")
    # ★★★ ここまで ★★★

    # iframeで表示
    st.components.v1.iframe(final_url, height=600, scrolling=True)
    st.markdown("---")

    st.subheader("🤖 AIによる分析サマリー")
    with st.spinner("AIが現在の表示内容を分析中です..."):
        # @st.cache_dataデコレータがついているので、引数が同じならキャッシュが返る
        comment = get_ai_dashboard_comment(
            _bq_client=bq_client,
            _model=model,
            sheet_name=st.session_state.filters["sheet"],
            filters=st.session_state.filters
        )
        st.info(comment)

    # 再生成ボタンも用意
    if st.button("最新の情報で再生成", key=f"{key_prefix}_regenerate_summary"):
        # キャッシュをクリアして再実行
        get_ai_dashboard_comment.clear()
        st.rerun()