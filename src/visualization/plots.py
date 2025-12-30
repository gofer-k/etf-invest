import matplotlib.pyplot as plt
import pandas as pd


def plot_price_and_indicators(df: pd.DataFrame, ticker: str):
    """
    Plots:
    - Close price
    - MA50
    - MA200
    - Volume
    - MACD (12/26/9)
    - MACD (50/200/9)
    - golden_cross
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
    plt.show()
