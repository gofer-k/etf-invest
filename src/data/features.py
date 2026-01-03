from typing import Dict

import pandas as pd
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


def add_technical_features(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    df = df.copy()
    features_cfg = config.get("features", {})
    window = int(features_cfg.get("rolling_window_days", 20))

    logger.info("Adding technical features (rolling window = %d)", window)

    df["rolling_mean"] = df["Close"].rolling(window).mean()
    df["rolling_std"] = df["Close"].rolling(window).std()
    df["volatility"] = df["return"].rolling(window).std() * np.sqrt(252)
    df["max_drawdown"] = _max_drawdown(df["Close"])
    df["price_above_ma"] = (df["Close"] > df["rolling_mean"]).astype(int)
    
    
    # Simple Moving Averages
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA100"] = df["Close"].rolling(100).mean()
    df["SMA150"] = df["Close"].rolling(150).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["SMA250"] = df["Close"].rolling(250).mean()
    # Bollinger Bands
    df["rolling_std20"] = df["Close"].rolling(20).mean()
    df["BB_upper20"] = df["SMA20"] + (df["rolling_std20"] * 2)
    df["BB_lower20"] = df["SMA20"] - (df["rolling_std20"] * 2)
    df["BB_width20"] = df["BB_upper20"] - df["BB_lower20"]
    df["BB_percent20"] = (df["Close"] - df["BB_lower20"]) / df["BB_width20"]
    
    df["rolling_std50"] = df["Close"].rolling(50).mean()
    df["BB_upper50"] = df["SMA50"] + (df["rolling_std50"] * 2)
    df["BB_lower50"] = df["SMA50"] - (df["rolling_std50"] * 2)
    df["BB_width50"] = df["BB_upper50"] - df["BB_lower50"]
    df["BB_percent50"] = (df["Close"] - df["BB_lower50"]) / df["BB_width50"]
    
    df["rolling_std100"] = df["Close"].rolling(100).mean()
    df["BB_upper100"] = df["SMA100"] + (df["rolling_std100"] * 2)
    df["BB_lower100"] = df["SMA100"] - (df["rolling_std100"] * 2)
    df["BB_width100"] = df["BB_upper100"] - df["BB_lower100"]
    df["BB_percent100"] = (df["Close"] - df["BB_lower100"]) / df["BB_width100"]
    
    df["rolling_std150"] = df["Close"].rolling(150).mean()
    df["BB_upper150"] = df["SMA150"] + (df["rolling_std150"] * 2)
    df["BB_lower150"] = df["SMA150"] - (df["rolling_std150"] * 2)
    df["BB_width150"] = df["BB_upper150"] - df["BB_lower150"]
    df["BB_percent150"] = (df["Close"] - df["BB_lower150"]) / df["BB_width150"]
    
    df["rolling_std250"] = df["Close"].rolling(250).mean()
    df["BB_upper250"] = df["SMA250"] + (df["rolling_std250"] * 2)
    df["BB_lower250"] = df["SMA250"] - (df["rolling_std250"] * 2)
    df["BB_width250"] = df["BB_upper250"] - df["BB_lower250"]
    df["BB_percent250"] = (df["Close"] - df["BB_lower250"]) / df["BB_width250"]

    # Golden Cross / Death Cross indicator
    # A classic signal:
    # 1 → SMA50 crossed above SMA200 (bullish)
    # 0 → otherwise
    df["golden_cross"] = (df["SMA50"] > df["SMA200"]).astype(int)
    df["death_cross"] = (df["SMA50"] < df["SMA200"]).astype(int)

    # === MACD CLASSIC (12, 26, 9) ===
    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD_12_26"] = df["EMA12"] - df["EMA26"]
    df["MACD_signal_12_26"] = df["MACD_12_26"].ewm(span=9, adjust=False).mean()
    df["MACD_hist_12_26"] = df["MACD_12_26"] - df["MACD_signal_12_26"]
    # === MACD LONG-TERM (50, 200, 9) === 
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()
    df["MACD_50_200"] = df["EMA50"] - df["EMA200"]
    df["MACD_signal_50_200"] = df["MACD_50_200"].ewm(span=9, adjust=False).mean()
    df["MACD_hist_50_200"] = df["MACD_50_200"] - df["MACD_signal_50_200"]
    
    # RSI
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(20).mean()  # 20 days period - configure if needed
    avg_loss = loss.rolling(20).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df


def _max_drawdown(prices: pd.Series) -> pd.Series:
    roll_max = prices.cummax()
    drawdown = (prices - roll_max) / roll_max
    return drawdown.cummin()
