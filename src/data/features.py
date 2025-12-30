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
    
    # NEW: Moving Averages
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    # Golden Cross / Death Cross indicator
    # A classic signal:
    # 1 → MA50 crossed above MA200 (bullish)
    # 0 → otherwise
    df["golden_cross"] = (df["MA50"] > df["MA200"]).astype(int)
    df["death_cross"] = (df["MA50"] < df["MA200"]).astype(int)

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
    
    return df


def _max_drawdown(prices: pd.Series) -> pd.Series:
    roll_max = prices.cummax()
    drawdown = (prices - roll_max) / roll_max
    return drawdown.cummin()
