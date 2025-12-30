import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import os


def plot_price_and_indicators(df: pd.DataFrame, ticker: str):
    """
    Plots:
    - Close price
    - MA50
    - MA200
    - MACD (12/26/9)
    - MACD (50/200/9)
    """
    fig = plt.figure(figsize=(14, 10))

    # === PRICE + MA ===
    ax1 = plt.subplot(3, 1, 1)
    ax1.plot(df.index, df["Close"], label="Close", color="black")
    if "MA50" in df.columns:
        ax1.plot(df.index, df["MA50"], label="MA50", color="blue", linewidth=1.2)
    if "MA200" in df.columns:
        ax1.plot(df.index, df["MA200"], label="MA200", color="red", linewidth=1.2)

    ax1.set_title(f"{ticker} Price with MA50 & MA200")
    ax1.set_ylabel("Price")
    ax1.legend()
    ax1.grid(True)

    # === MACD (12/26/9) ===
    ax2 = plt.subplot(3, 1, 2)
    ax2.plot(df.index, df["MACD_12_26"], label="MACD 12/26", color="purple")
    ax2.plot(df.index, df["MACD_signal_12_26"], label="Signal 9", color="orange")
    ax2.bar(df.index, df["MACD_hist_12_26"], label="Histogram", color="gray", alpha=0.4)

    ax2.set_title("MACD (12, 26, 9)")
    ax2.set_ylabel("MACD")
    ax2.legend()
    ax2.grid(True)

    # === MACD (50/200/9) ===
    ax3 = plt.subplot(3, 1, 3)
    ax3.plot(df.index, df["MACD_50_200"], label="MACD 50/200", color="green")
    ax3.plot(df.index, df["MACD_signal_50_200"], label="Signal 9", color="brown")
    ax3.bar(df.index, df["MACD_hist_50_200"], label="Histogram", color="gray", alpha=0.4)

    ax3.set_title("MACD (50, 200, 9)")
    ax3.set_ylabel("MACD")
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout()
    _safe_show_or_save(fig, f"{ticker}_indicators")

def plot_price_indicators_and_signals(df: pd.DataFrame, ticker: str, signals: pd.Series):
    """
    Plots:
    - Price
    - MA50, MA200
    - BUY/SELL signals as arrows
    """
    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(df.index, df["Close"], label="Close", color="black")
    ax.plot(df.index, df["MA50"], label="MA50", color="blue", linewidth=1.2)
    ax.plot(df.index, df["MA200"], label="MA200", color="red", linewidth=1.2)

    # BUY / SELL markers
    buy_signals = df[signals == "BUY"]
    sell_signals = df[signals == "SELL"]

    ax.scatter(
        buy_signals.index,
        buy_signals["Close"],
        marker="^",
        color="green",
        s=120,
        label="BUY",
        zorder=5,
    )

    ax.scatter(
        sell_signals.index,
        sell_signals["Close"],
        marker="v",
        color="red",
        s=120,
        label="SELL",
        zorder=5,
    )

    ax.set_title(f"{ticker} Price with Trend Signals")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    _safe_show_or_save(fig, f"{ticker}_signals")

def _safe_show_or_save(fig, filename: str):
    """
    Show plot if interactive, otherwise save to output/<filename>.png
    """
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{filename}.png")

    # try:
    #     if os.environ.get("DISPLAY", "") == "":
    #         raise RuntimeError("No display found")
    #     plt.show()
    # except Exception:
    print(f"[INFO] No GUI display detected. Saving plot to {filepath}")
    fig.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close(fig)

def plot_interactive_signals(df: pd.DataFrame, ticker: str, signals: pd.Series):
    """
    Interactive Plotly chart:
    - Price + MA50 + MA200
    - BUY/SELL markers
    - MACD (12/26/9) and MACD (50/200/9)
    """

    fig = go.Figure()

    # === Price + MA ===
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(color="black")))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="MA50", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA200"], name="MA200", line=dict(color="red")))

    # === BUY / SELL markers ===
    buy = df[signals == "BUY"]
    sell = df[signals == "SELL"]

    fig.add_trace(go.Scatter(
        x=buy.index,
        y=buy["Close"],
        mode="markers",
        name="BUY",
        marker=dict(symbol="triangle-up", color="green", size=12)
    ))

    fig.add_trace(go.Scatter(
        x=sell.index,
        y=sell["Close"],
        mode="markers",
        name="SELL",
        marker=dict(symbol="triangle-down", color="red", size=12)
    ))

    fig.update_layout(
        title=f"{ticker} Price with Signals",
        yaxis_title="Price",
        xaxis_title="Date",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=600,
        template="plotly_white"
    )

    # === MACD subplot ===
    macd_fig = go.Figure()

    macd_fig.add_trace(go.Scatter(x=df.index, y=df["MACD_12_26"], name="MACD 12/26", line=dict(color="purple")))
    macd_fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal_12_26"], name="Signal 9", line=dict(color="orange")))
    macd_fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist_12_26"], name="Histogram", marker_color="gray", opacity=0.5))

    macd_fig.update_layout(
        title="MACD (12, 26, 9)",
        yaxis_title="MACD",
        xaxis_title="Date",
        height=400,
        template="plotly_white"
    )

    # === Save or show ===
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    price_path = os.path.join(output_dir, f"{ticker}_interactive_price.html")
    macd_path = os.path.join(output_dir, f"{ticker}_interactive_macd.html")

    try:
        fig.show()
        macd_fig.show()
    except Exception:
        print(f"[INFO] No browser display. Saving interactive charts to HTML.")
        fig.write_html(price_path)
        macd_fig.write_html(macd_path)
