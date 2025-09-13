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
        """
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
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR
            FROM `{table}` {where_clause}
            GROUP BY Date
            ORDER BY Date ASC
        """
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
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR
            FROM `{table}` {where_clause}
            GROUP BY Date
            ORDER BY Date ASC
        """
    },

    # 基本的なレポート
    "メディア": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT
                ServiceNameJA_Media,
                SUM(CostIncludingFees) AS Cost,
                SUM(Conversions) AS Conversions,
                SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA,
                SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR
            FROM `{table}` {where_clause}
            GROUP BY ServiceNameJA_Media ORDER BY Cost DESC
        """
    },
    "デバイス": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign_device",
        "query": """
            SELECT DeviceCategory, SUM(CostIncludingFees) AS Cost, SUM(Conversions) AS Conversions, SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA
            FROM `{table}` {where_clause}
            GROUP BY DeviceCategory ORDER BY Cost DESC
        """
    },
    "月別": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT FORMAT_DATE('%Y-%m', Date) as YearMonth, SUM(CostIncludingFees) AS Cost, SUM(Conversions) AS Conversions
            FROM `{table}` {where_clause}
            GROUP BY YearMonth ORDER BY YearMonth ASC
        """
    },
    "日別": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT FORMAT_DATE('%Y-%m-%d', Date) as Date, SUM(CostIncludingFees) as Cost, SUM(Conversions) as Conversions
            FROM `{table}` {where_clause}
            GROUP BY Date ORDER BY Date ASC
        """
    },
    "曜日": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT DayOfWeekJA, SUM(CostIncludingFees) AS Cost, SUM(Conversions) AS Conversions, SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA
            FROM `{table}` {where_clause}
            GROUP BY DayOfWeekJA
        """
    },

    # 配信設定別のレポート
    "キャンペーン": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT CampaignName, SUM(CostIncludingFees) as Cost, SUM(Conversions) as Conversions, SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA
            FROM `{table}` {where_clause}
            GROUP BY CampaignName ORDER BY Cost DESC LIMIT 15
        """
    },
    "広告グループ": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_ad_group",
        "query": """
            SELECT AdGroupName_unified, SUM(CostIncludingFees) as Cost, SUM(Conversions) as Conversions, SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA
            FROM `{table}` {where_clause}
            GROUP BY AdGroupName_unified ORDER BY Cost DESC LIMIT 15
        """
    },
    "テキストCR": { # 広告クリエイティブレポートで代表
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_ad",
        "query": """
            SELECT AdName, Headline, SUM(Impressions) as Impressions, SUM(Clicks) as Clicks, SUM(Conversions) as Conversions, SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) as CTR
            FROM `{table}`
            WHERE AdTypeJA = 'テキスト' {where_clause}
            GROUP BY AdName, Headline ORDER BY Clicks DESC LIMIT 15
        """
    },
    "ディスプレイCR": { # 広告クリエイティブレポートで代表
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_ad",
        "query": """
            SELECT AdName, SUM(Impressions) as Impressions, SUM(Clicks) as Clicks, SUM(Conversions) as Conversions, SAFE_DIVIDE(SUM(Clicks), SUM(Impressions)) as CTR
            FROM `{table}`
            WHERE AdTypeJA != 'テキスト' {where_clause}
            GROUP BY AdName ORDER BY Clicks DESC LIMIT 15
        """
    },
    "キーワード": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_keyword",
        "query": """
            SELECT Keyword, SUM(CostIncludingFees) as Cost, SUM(Conversions) as Conversions, AVG(QualityScore) as AvgQualityScore
            FROM `{table}` {where_clause}
            GROUP BY Keyword ORDER BY Cost DESC LIMIT 20
        """
    },
    "最終ページURL": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_final_url",
        "query": """
            SELECT EffectiveFinalUrl, SUM(CostIncludingFees) as Cost, SUM(Conversions) as Conversions, SAFE_DIVIDE(SUM(Conversions), SUM(Clicks)) AS CVR
            FROM `{table}` {where_clause}
            GROUP BY EffectiveFinalUrl ORDER BY Cost DESC LIMIT 15
        """
    },

    # ターゲティング別のレポート
    "地域": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_area",
        "query": """
            SELECT RegionJA, SUM(CostIncludingFees) as Cost, SUM(Conversions) as Conversions, SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA
            FROM `{table}` {where_clause}
            GROUP BY RegionJA ORDER BY Cost DESC
        """
    },
    "時間": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_hourly",
        "query": """
            SELECT HourOfDay, SUM(CostIncludingFees) as Cost, SUM(Conversions) as Conversions
            FROM `{table}` {where_clause}
            GROUP BY HourOfDay ORDER BY HourOfDay ASC
        """
    },
    "性別": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_gender",
        "query": """
            SELECT UnifiedGenderJA, SUM(CostIncludingFees) as Cost, SUM(Conversions) as Conversions, SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) as CPA
            FROM `{table}` {where_clause}
            GROUP BY UnifiedGenderJA ORDER BY Cost DESC
        """
    },
    "年齢": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_age_group",
        "query": """
            SELECT AgeRange, SUM(CostIncludingFees) AS Cost, SUM(Conversions) AS Conversions, SAFE_DIVIDE(SUM(CostIncludingFees), SUM(Conversions)) AS CPA
            FROM `{table}` {where_clause}
            GROUP BY AgeRange ORDER BY Cost DESC
        """
    },

    # デフォルトクエリ
    "default": {
        "table": "vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign",
        "query": """
            SELECT Date, SUM(CostIncludingFees) as TotalCost, SUM(Conversions) as TotalConversions
            FROM `{table}` {where_clause}
            GROUP BY Date ORDER BY Date DESC LIMIT 7
        """
    }
}


@st.cache_data(ttl=600)
def get_ai_dashboard_comment(_bq_client, _model, sheet_name, filters):
    """
    選択されたシートとフィルタに基づいてAIコメントを生成する。
    """
    try:
        query_info = SHEET_ANALYSIS_QUERIES.get(sheet_name, SHEET_ANALYSIS_QUERIES["default"])
        table_id = query_info["table"]
        base_query = query_info["query"] # base_query を定義

        # クエリテンプレートに既にWHERE句があるか（{where_clause}以外に）を判定
        has_fixed_where = 'WHERE' in base_query.upper().replace('{WHERE_CLAUSE}', '')

        if has_fixed_where:
            # 既にWHERE句がある場合は、prefix="AND" を指定して条件句を生成
            where_clause = build_where_clause(
                filters, apply_date=True, apply_media=True, apply_campaign=True, prefix="AND"
            )
        else:
            # そうでなければデフォルトの "WHERE" を使う
            where_clause = build_where_clause(
                filters, apply_date=True, apply_media=True, apply_campaign=True
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