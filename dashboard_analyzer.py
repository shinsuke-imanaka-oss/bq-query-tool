# dashboard_analyzer.py

import streamlit as st
import pandas as pd
from analysis_logic import build_where_clause

# --- シート別分析クエリの定義 ---
SHEET_ANALYSIS_QUERIES = {
    # 予算・サマリー
    "予算管理": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_budget",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m-%d', Date) AS Date,
                PromotionName,
                SUM(CostIncludingFees) AS ActualCost,
                AVG(PromotionBudgetIncludingFees) AS PromotionBudget
            FROM `{table}` {where_clause}
            GROUP BY Date, PromotionName
            ORDER BY Date DESC
        """,
        "supported_filters": ["date"]
    },
    "サマリー01": { # サマリーは日別の主要KPI推移を分析
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m-%d', Date) AS Date,
                SUM(CostIncludingFees) AS Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) AS Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY Date
            ORDER BY Date ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "サマリー02": { # サマリー01と同様のクエリを使用
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m-%d', Date) AS Date,
                SUM(CostIncludingFees) AS Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) AS Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY Date
            ORDER BY Date ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    # サマリー02として複数のクエリに分割
    "サマリー02_年月メディア分布": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m', Date) as YearMonth,
                ServiceNameJA_Media,
                SUM(Clicks) AS Clicks
            FROM `{table}` {where_clause}
            GROUP BY YearMonth, ServiceNameJA_Media
            ORDER BY YearMonth ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "サマリー02_年月デバイス分布": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign_device",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m', Date) as YearMonth,
                DeviceCategory,
                SUM(Clicks) AS Clicks
            FROM `{table}` {where_clause}
            GROUP BY YearMonth, DeviceCategory
            ORDER BY YearMonth ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "サマリー02_年月性別分布": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_gender",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m', Date) as YearMonth,
                UnifiedGenderJA,
                SUM(Clicks) AS Clicks
            FROM `{table}` {where_clause}
            GROUP BY YearMonth, UnifiedGenderJA
            ORDER BY YearMonth ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "サマリー02_年月年齢分布": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_age_group",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m', Date) as YearMonth,
                AgeRange,
                SUM(Clicks) AS Clicks
            FROM `{table}` {where_clause}
            GROUP BY YearMonth, AgeRange
            ORDER BY YearMonth ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "サマリー02_時間×曜日": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_hourly",
        "query": """
            SELECT
                HourOfDay,
                CASE EXTRACT(DAYOFWEEK FROM Date)
                    WHEN 1 THEN '日'
                    WHEN 2 THEN '月'
                    WHEN 3 THEN '火'
                    WHEN 4 THEN '水'
                    WHEN 5 THEN '木'
                    WHEN 6 THEN '金'
                    WHEN 7 THEN '土'
                END AS DayOfWeekJA,
                SUM(Clicks) AS Clicks
            FROM `{table}` {where_clause}
            GROUP BY HourOfDay, DayOfWeekJA
            ORDER BY HourOfDay ASC, DayOfWeekJA ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "サマリー02_地域別": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_area",
        "query": """
            SELECT
                RegionJA,
                SUM(Clicks) AS Clicks
            FROM `{table}` {where_clause}
            GROUP BY RegionJA
            ORDER BY Clicks DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    # 基本的なレポート
    "メディア": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                ServiceNameJA_Media,
                SUM(CostIncludingFees) AS Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) AS Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY ServiceNameJA_Media
            ORDER BY Cost DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "デバイス": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign_device",
        "query": """
            SELECT
                DeviceCategory,
                SUM(CostIncludingFees) AS Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) AS Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY DeviceCategory
            ORDER BY Cost DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "月別": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m', Date) as YearMonth,
                SUM(CostIncludingFees) AS Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) AS Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY YearMonth
            ORDER BY YearMonth ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "日別": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m-%d', Date) as Date,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY Date
            ORDER BY Date ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "曜日": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                DayOfWeekJA,
                SUM(CostIncludingFees) AS Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) AS Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY DayOfWeekJA
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    # 配信設定別のレポート
    "キャンペーン": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                CampaignName,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY CampaignName
            ORDER BY Cost DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "広告グループ": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_ad_group",
        "query": """
            SELECT
                AdGroupName_unified,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY AdGroupName_unified
            ORDER BY Cost DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "テキストCR": { # 広告クリエイティブレポートで代表
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_ad",
        "query": """
            SELECT
                AdName, Headline,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) as Impressions,
                SUM(Clicks) as Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}`
            WHERE AdTypeJA = 'テキスト' {where_clause}
            GROUP BY AdName, Headline
            ORDER BY Clicks DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "ディスプレイCR": { # 広告クリエイティブレポートで代表
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_ad",
        "query": """
            SELECT
                AdName,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) as Impressions,
                SUM(Clicks) as Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}`
            WHERE AdTypeJA != 'テキスト' {where_clause}
            GROUP BY AdName
            ORDER BY Clicks DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "キーワード": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_keyword",
        "query": """
            SELECT
                Keyword,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY Keyword
            ORDER BY Cost DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "最終ページURL": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_final_url",
        "query": """
            SELECT
                EffectiveFinalUrl,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY EffectiveFinalUrl
            ORDER BY Cost DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    # ターゲティング別のレポート
    "地域": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_area",
        "query": """
            SELECT
                RegionJA,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY RegionJA
            ORDER BY Cost DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "時間": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_hourly",
        "query": """
            SELECT
                HourOfDay,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY HourOfDay
            ORDER BY HourOfDay ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    # 時間×曜日用の新しいエントリ
    "時間×曜日": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_hourly",
        "query": """
            SELECT
                HourOfDay,
                CASE EXTRACT(DAYOFWEEK FROM Date)
                    WHEN 1 THEN '日'
                    WHEN 2 THEN '月'
                    WHEN 3 THEN '火'
                    WHEN 4 THEN '水'
                    WHEN 5 THEN '木'
                    WHEN 6 THEN '金'
                    WHEN 7 THEN '土'
                END AS DayOfWeekJA,
                SUM(Clicks) AS Clicks
            FROM `{table}` {where_clause}
            GROUP BY
                HourOfDay,
                DayOfWeekJA
            ORDER BY HourOfDay ASC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "性別": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_gender",
        "query": """
            SELECT
                UnifiedGenderJA,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY UnifiedGenderJA
            ORDER BY Cost DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    "年齢": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_age_group",
        "query": """
            SELECT
                AgeRange,
                SUM(CostIncludingFees) AS Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) AS Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY AgeRange
            ORDER BY Cost DESC
        """,
        "supported_filters": ["date", "media", "campaign"]
    },
    # デフォルトクエリ
    "default": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                FORMAT_DATE('%Y-%m-%d', Date) as Date,
                SUM(CostIncludingFees) as Cost,
                SUM(Impressions) AS Impressions,
                SUM(Clicks) AS Clicks,
                SUM(Conversions) as Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR,
                SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) AS CTR,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Clicks)) AS CPC
            FROM `{table}` {where_clause}
            GROUP BY Date
            ORDER BY Date DESC LIMIT 7
        """,
        "supported_filters": ["date", "media", "campaign"]
    }
}


@st.cache_data(ttl=600)
def get_ai_dashboard_comment(_bq_client, _model, sheet_name, filters, sheet_analysis_queries):
    """
    選択されたシートとフィルタに基づいてAIコメントを生成する。
    """
    try:
        query_info = sheet_analysis_queries.get(sheet_name, sheet_analysis_queries["default"])
        table_id = query_info["table"]
        base_query = query_info["query"]
        
        # supported_filters キーが存在しない場合、デフォルトで全て適用
        supported_filters = query_info.get("supported_filters", ["date", "media", "campaign"])

        # クエリテンプレートに既にWHERE句があるか判定
        has_fixed_where = 'WHERE' in base_query.upper().replace('{WHERE_CLAUSE}', '')

        # supported_filters に基づいて build_where_clause を呼び出し
        if has_fixed_where:
            where_clause = build_where_clause(
                filters,
                apply_date="date" in supported_filters,
                apply_media="media" in supported_filters,
                apply_campaign="campaign" in supported_filters,
                prefix="AND"
            )
        else:
            where_clause = build_where_clause(
                filters,
                apply_date="date" in supported_filters,
                apply_media="media" in supported_filters,
                apply_campaign="campaign" in supported_filters
            )

        final_query = base_query.format(table=table_id, where_clause=where_clause)

        df = _bq_client.query(final_query).to_dataframe()

        if df.empty:
            return "分析対象のデータが見つかりませんでした。フィルタ条件を変更してみてください。"

        prompt = f"""
        あなたは優秀なデータアナリストです。
        以下のデータは、広告レポートの「{sheet_name}」シートのサマリーです。
        このデータから読み取れる重要な傾向や、特筆すべき点を箇条書きで3つ以内にまとめて、マーケティング担当者向けに分かりやすく解説してください。

        [データサマリー]
        {df.to_string()}
        """
        response = _model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"Error in get_ai_dashboard_comment: {e}")
        st.error(f"コメント生成中にエラーが発生しました: {e}")
        return "コメントの生成中にエラーが発生しました。管理者にご確認ください。"