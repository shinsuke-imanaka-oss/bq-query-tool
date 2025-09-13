# charting.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

def render_plotly_chart(df: pd.DataFrame, cfg: dict):
    """
    Plotlyグラフを描画する。
    設定(cfg)に基づいて、単一グラフ、または左右のY軸を持つ組合せグラフを生成する。
    """
    try:
        chart_type = cfg.get("main_chart_type")
        x_axis = cfg.get("x_axis")
        y_axis_left = cfg.get("y_axis_left")
        y_axis_right = cfg.get("y_axis_right")
        legend_col_raw = cfg.get("legend_col")
        legend_col = legend_col_raw if legend_col_raw != "なし" else None

        if not all([chart_type, x_axis, y_axis_left]):
            st.warning("グラフを描画できません。グラフの種類、X軸、Y軸（左）を正しく設定してください。")
            return go.Figure()

        if chart_type == "組合せグラフ" and y_axis_right:
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # --- 凡例が指定されている場合 ---
            if legend_col:
                # 凡例の各項目でループ
                for value in df[legend_col].unique():
                    df_filtered = df[df[legend_col] == value]
                    # 左軸の棒グラフを追加
                    fig.add_trace(
                        go.Bar(
                            x=df_filtered[x_axis],
                            y=df_filtered[y_axis_left],
                            name=f"{value} ({y_axis_left})", # 凡例名を明確化
                            showlegend=True
                        ),
                        secondary_y=False,
                    )
                    # 右軸の折れ線グラフを追加
                    fig.add_trace(
                        go.Scatter(
                            x=df_filtered[x_axis],
                            y=df_filtered[y_axis_right],
                            name=f"{value} ({y_axis_right})", # 凡例名を明確化
                            mode='lines+markers',
                            showlegend=True
                        ),
                        secondary_y=True,
                    )
            # --- 凡例が指定されていない場合 ---
            else:
                fig.add_trace(
                    go.Bar(x=df[x_axis], y=df[y_axis_left], name=y_axis_left, showlegend=True),
                    secondary_y=False,
                )
                fig.add_trace(
                    go.Scatter(x=df[x_axis], y=df[y_axis_right], name=y_axis_right, mode='lines+markers', showlegend=True),
                    secondary_y=True,
                )

            fig.update_layout(barmode='group') # 棒グラフをグループ化
            fig.update_yaxes(title_text=y_axis_left, secondary_y=False)
            fig.update_yaxes(title_text=y_axis_right, secondary_y=True)

        # --- 単一グラフの場合 ---
        else:
            px_func_map = {
                "棒グラフ": px.bar, "折れ線グラフ": px.line,
                "面グラフ": px.area, "散布図": px.scatter, "円グラフ": px.pie
            }
            px_func = px_func_map.get(chart_type)

            if chart_type == "円グラフ":
                fig = px_func(df, names=x_axis, values=y_axis_left, hole=.3)
            elif px_func:
                kwargs = {'x': x_axis, 'y': y_axis_left, 'color': legend_col}
                if chart_type in ["折れ線グラフ", "散布図", "面グラフ"]:
                    kwargs['markers'] = True
                fig = px_func(df, **kwargs)
            else:
                return go.Figure()

        fig.update_layout(
            title=None,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig

    except Exception as e:
        st.error(f"グラフ描画中にエラーが発生しました: {e}")
        return go.Figure()