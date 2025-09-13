# prompts.py
"""
BigQuery テーブルごとのプロンプト定義をまとめたファイル
- データ集計部分とグラフ選択部分を分離
- select_best_prompt() で自然言語から最適なテーブルを選択
"""

PROMPT_DEFINITIONS = {
    # === 既存の定義 ===
    "campaign": {
        "description": "キャンペーン単位での広告実績を分析",
        "template": """
# あなたは広告分析の専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, ServiceNameJA, PromotionName, AccountName, CampaignName, Date, DayOfWeekJA, AllConversions, Cost, VideoViews, ConversionValue, AllConversionValue
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    },
    "age_group": {
        "description": "年齢区分ごとの広告パフォーマンス分析",
        "template": """
# あなたは広告分析の専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_age_group`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, AgeRange, ServiceNameJA, PromotionName, AccountName, CampaignName, AdGroupName, Date, AllConversions, Cost, VideoViews
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。分析ではAgeRangeでの比較を優先。
# 出力: 実行可能な SQL だけ返す
"""
    },
    "keyword": {
        "description": "検索キーワードごとの広告パフォーマンス分析",
        "template": """
# あなたは検索連動型広告の分析専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_keyword`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, Keyword, QualityScore, ServiceNameJA, PromotionName, AccountName, CampaignName, AdGroupName, Date, AllConversions, Cost, VideoViews
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。Keyword単位の分析優先。
# 出力: 実行可能な SQL だけ返す
"""
    },
    "final_url": {
        "description": "ランディングページ単位の広告パフォーマンス分析",
        "template": """
# あなたはランディングページ最適化の専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_final_url`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, EffectiveFinalUrl, ServiceNameJA, PromotionName, AccountName, CampaignName, AdGroupName, Date, AllConversions, Cost, VideoViews
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。EffectiveFinalUrlごとのパフォーマンス分析優先
# 出力: 実行可能な SQL だけ返す
"""
    },
    "hourly": {
        "description": "時間帯ごとの広告パフォーマンス分析",
        "template": """
# あなたは広告配信最適化の専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_hourly`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, HourOfDay, ServiceNameJA, PromotionName, AccountName, CampaignName, Date, AllConversions, Cost, VideoViews
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。HourOfDayごとのパフォーマンス傾向を優先
# 出力: 実行可能な SQL だけ返す
"""
    },

    # === 新規追加分 ===
    "ad": {
        "description": "広告クリエイティブ別のパフォーマンスを分析",
        "template": """
# あなたは広告クリエイティブの分析専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_ad`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, Headline, AdName, AdTypeJA, HeadlineByAdType, Description1ByAdType, Description2ByAdType, ServiceNameJA, PromotionName, AccountName, CampaignName, AdGroupName, Date
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。HeadlineやAdNameなど広告クリエイティブ単位での分析を優先してください。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    },
    "ad_group": {
        "description": "広告グループ単位での広告実績を分析",
        "template": """
# あなたは広告運用専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_ad_group`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, AdGroupName_unified, ServiceNameJA, PromotionName, AccountName, CampaignName, Date
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。AdGroupName_unified単位での分析を優先してください。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    },
    "area": {
        "description": "地域（都道府県）ごとの広告パフォーマンス分析",
        "template": """
# あなたはエリアマーケティングの専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_area`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, RegionJA, ServiceNameJA, PromotionName, AccountName, CampaignName, Date
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。RegionJAごとのパフォーマンス分析を優先してください。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    },
    "budget": {
        "description": "予算の消費状況とコストを分析",
        "template": """
# あなたは広告予算管理の専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_budget`
# カラム: CostIncludingFees, AccountBudgetIncludingFees, PromotionBudgetIncludingFees, AccountName, PromotionName, ServiceNameJA, Date
# ルール: ユーザーの指示に合わせて予算やコストに関する情報を集計するSQLを生成してください。主にCostIncludingFees（実績コスト）、PromotionBudgetIncludingFees（プロモーション予算）、AccountBudgetIncludingFees（アカウント予算）の比較や集計を行います。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    },
    "campaign_device": {
        "description": "デバイス（PC、スマホなど）ごとの広告パフォーマンス分析",
        "template": """
# あなたは広告配信最適化の専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_campaign_device`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, DeviceCategory, ServiceNameJA, PromotionName, AccountName, CampaignName, Date
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。DeviceCategoryごとのパフォーマンス比較を優先してください。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    },
    "gender": {
        "description": "性別ごとの広告パフォーマンス分析",
        "template": """
# あなたはターゲット分析の専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_gender`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, UnifiedGenderJA, ServiceNameJA, PromotionName, AccountName, CampaignName, AdGroupName, Date
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。UnifiedGenderJAごとのパフォーマンス分析を優先してください。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    },
    "interest": {
        "description": "ユーザーの興味関心ごとの広告パフォーマンス分析",
        "template": """
# あなたはオーディエンスターゲティングの専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_gender`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, InterestName, ServiceNameJA, PromotionName, AccountName, CampaignName, AdGroupName, Date
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。InterestNameごとのパフォーマンス分析を優先してください。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    },
    "placement": {
        "description": "広告の掲載元（流入元）サイト別のパフォーマンス分析",
        "template": """
# あなたはディスプレイ広告の分析専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_placement`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, Placement, ServiceNameJA, PromotionName, AccountName, CampaignName, AdGroupName, Date
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。Placementごとのパフォーマンス分析を優先してください。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    },
    "search_query": {
        "description": "ユーザーが実際に検索した語句（検索クエリ）ごとのパフォーマンス分析",
        "template": """
# あなたは検索連動型広告の分析専門家です。
# ユーザー指示: {user_input}
# 分析対象: `vorn-digi-mktg-poc-635a.toki_air.LookerStudio_report_search_query`
# カラム: Impressions, Clicks, CostIncludingFees, Conversions, Query, UnifiedQueryMatchTypeWithVariantJA, ServiceNameJA, PromotionName, AccountName, CampaignName, AdGroupName, Date
# 指標: CTR=Clicks/Impressions, CPA=CostIncludingFees/Conversions, CPC=CostIncludingFees/Clicks, CVR=Conversions/Clicks
# ルール: ユーザーの指示に最も関連性の高い指標を選択してSQLを生成してください。CostはCostIncludingFeesを、ConversionsはConversionsを使用してください。Queryごとのパフォーマンス分析を優先してください。
# 出力: 実行可能な BigQuery SQL だけ返す（説明なし）
"""
    }
}

MODIFY_SQL_TEMPLATE = """
# あなたはSQLのエキスパートです。
# 以下の「元のSQL」を、「修正指示」に基づいて修正してください。

# 元のSQL:
{original_sql}

# 修正指示:
{modification_instruction}

# ルール:
# - BigQueryで実行可能なSQLクエリのみを生成してください。
# - SQL以外の説明やコメントは一切含めないでください。
# - 元のSQLの分析目的を維持しつつ、指示内容を正確に反映してください。

# 出力: 修正後のSQL
"""

def select_best_prompt(user_input: str):
    """
    自然言語指示から最適なテーブル（プロンプト）を選択するルール強化版ルーター
    - キーワードを拡充し、より多くの表現に対応
    - 評価の優先順位を調整し、誤分類を防止
    """
    # --- 評価の優先順位 1: 最も具体的・排他的なキーワード ---
    # 「検索クエリ」や「検索語句」は `search_query` テーブルを強く示すため、最優先で評価
    if any(keyword in user_input for keyword in ["検索クエリ", "検索語句", "検索した言葉"]):
        return PROMPT_DEFINITIONS["search_query"]

    # 「予算」や「費用」は `budget` テーブルにしかほぼ関連しないため、優先度を高く設定
    if any(keyword in user_input for keyword in ["予算", "コスト", "費用"]):
        return PROMPT_DEFINITIONS["budget"]

    # --- 評価の優先順位 2: 一般的だが、特定の分析軸を示すキーワード ---
    # 「キーワード」または「検索」のみの場合は、`keyword` (登録キーワード) を選択
    if any(keyword in user_input for keyword in ["キーワード", "検索"]):
        return PROMPT_DEFINITIONS["keyword"]

    if any(keyword in user_input for keyword in ["地域", "エリア", "場所", "都道府県", "市区町村"]):
        return PROMPT_DEFINITIONS["area"]

    # 「スマホ」や「PC」など、より口語的な表現を追加
    if any(keyword in user_input for keyword in ["デバイス", "端末", "スマートフォン", "スマホ", "PC", "モバイル", "タブレット"]):
        return PROMPT_DEFINITIONS["campaign_device"]

    if any(keyword in user_input for keyword in ["性別", "男女", "男性", "女性"]):
        return PROMPT_DEFINITIONS["gender"]

    if any(keyword in user_input for keyword in ["興味", "関心", "オーディエンス"]):
        return PROMPT_DEFINITIONS["interest"]

    # 「掲載面」や「配信先」といった関連キーワードを追加
    if any(keyword in user_input for keyword in ["流入元", "プレースメント", "掲載面", "配信先"]):
        return PROMPT_DEFINITIONS["placement"]

    if any(keyword in user_input for keyword in ["年齢", "Age", "ターゲット"]):
        return PROMPT_DEFINITIONS["age_group"]

    # 一般的な略語「LP」を追加
    if any(keyword in user_input for keyword in ["URL", "ランディングページ", "LP"]):
        return PROMPT_DEFINITIONS["final_url"]

    if any(keyword in user_input for keyword in ["時間帯", "時間別"]):
        return PROMPT_DEFINITIONS["hourly"]

    # --- 評価の優先順位 3: 階層的なキーワード（具体的なものを先に評価） ---
    # 「広告グループ」を先に評価
    if "広告グループ" in user_input:
        return PROMPT_DEFINITIONS["ad_group"]

    # 次に「広告」や「クリエイティブ」を評価
    if any(keyword in user_input for keyword in ["広告", "クリエイティブ", "見出し", "ディスクリプション"]):
        return PROMPT_DEFINITIONS["ad"]

    # --- 評価の優先順位 4: デフォルト ---
    # 上記のいずれにも一致しない場合は、最も基本的な「キャンペーン」単位の分析を返す
    else:
        return PROMPT_DEFINITIONS["campaign"]