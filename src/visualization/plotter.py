import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

from src.utils.paths import OUTPUT_DIR


def plot_interactive_signals(df: pd.DataFrame, period: int, ticker: str, signals: pd.Series):
    """
    Interactive Plotly chart:
    - Price + SMA50 + SMA200
    - BUY/SELL markers
    - MACD (12/26/9) and MACD (50/200/9)
    """
    # Define Bollinger Band periods and colors
    periods_colors = { 20: 'blue', 50: "red", 100: 'green', 150: 'orange', 200: "brown", 250: 'purple' }
    
    # Create subplots
    fig = make_subplots(rows=3, cols=1,
                         shared_xaxes=True, row_heights=[0.5, 0.15, 0.35],
                         vertical_spacing=0.05,
                         subplot_titles=("Price + Bollinger Bands", "Volume", "RSI & MACD")) 

    # Main pane: Bollinger Bands for each period
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(color="black")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA{period}'], mode='lines',
                name=f'SMA{period}', line=dict(color=periods_colors[period], dash='solid')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'BB_upper{period}'], mode='lines',
                 name=f'Upper Band {period}', line=dict(color=periods_colors[period], dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'BB_lower{period}'], mode='lines',
                name=f'Lower Band {period}', line=dict(color=periods_colors[period], dash='dot')), row=1, col=1)
   
    # === BUY / SELL markers ===
    buy = df[signals == "BUY"]
    sell = df[signals == "SELL"]

    fig.add_trace(go.Scatter(
        x=buy.index,
        y=buy["Close"],
        mode="markers",
        name="BUY",
        marker=dict(symbol="triangle-up", color="green", size=12)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=sell.index,
        y=sell["Close"],
        mode="markers",
        name="SELL",
        marker=dict(symbol="triangle-down", color="red", size=12)
    ), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color="blue"), row=2, col=1)

    # RSI & MACD
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="orange")), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_12_26"], name="MACD", line=dict(color="purple")), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal_12_26"], name="Signal", line=dict(color="green")), row=3, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist_12_26"], name="MACD Hist", marker_color="blue"), row=3, col=1)

    # Update layout
    fig.update_layout(
        title={"text": f"Bollinger Bands ({period} days), RSI, MACD, Volume"},
        xaxis_title='Date',
        yaxis_title='Price',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    # === Save or show ===    
    price_path = os.path.join(OUTPUT_DIR, f"{ticker}_interactive_price_{period}d.html")
    
    try:
        fig.show()
    except Exception:
        print(f"[INFO] No browser display. Saving interactive charts to HTML.")
        fig.write_html(price_path)
