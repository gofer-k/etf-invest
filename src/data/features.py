from curses import window
from typing import Dict
import pandas as pd
import numpy as np

from ..utils.analysis_request import AnalysisRequest
from ..utils.logger import get_logger

logger = get_logger(__name__)


def add_technical_features(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
  df = df.copy()
  features_cfg = config.get("features", {})
  window = int(features_cfg.get("rolling_windows", 20))

  logger.info("Adding technical features (rolling window = %d)", window)

  df["rolling_mean"] = df["Close"].rolling(window).mean()
  df["rolling_std"] = df["Close"].rolling(window).std()
  df["volatility"] = df["return"].rolling(window).std() * np.sqrt(252)
  df["max_drawdown"] = _max_drawdown(df["Close"])
  df["price_above_ma"] = (df["Close"] > df["rolling_mean"]).astype(int)
  df["VolumeZscore"] = (df["Volume"] - df["Volume"].rolling(20).mean()) / df["Volume"].rolling(20).std()
  
  window_lengths = [20, 50, 100, 150, 200, 250]
  for wl in window_lengths:
    # Simple Moving Averages
    df[f"SMA{wl}"] = df["Close"].rolling(wl).mean()
    # Bollinger Bands
    df[f"rolling_std{wl}"] = df["Close"].rolling(wl).std()
    df[f"BB_upper{wl}"] = df[f"SMA{wl}"] + (df[f"rolling_std{wl}"] * 2)
    df[f"BB_lower{wl}"] = df[f"SMA{wl}"] - (df[f"rolling_std{wl}"] * 2)
    df[f"BB_width{wl}"] = df[f"BB_upper{wl}"] - df[f"BB_lower{wl}"]
    df[f"BB_percent{wl}"] = (df["Close"] - df[f"BB_lower{wl}"]) / df[f"BB_width{wl}"]

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

def add_technical_features(df: pd.DataFrame, config: AnalysisRequest) -> pd.DataFrame:
  df = df.copy()

  df["VolumeZscore"] = (df["Volume"] - df["Volume"].rolling(20).mean()) / df["Volume"].rolling(20).std()
    
  for wl in config.rolling_windows:
    logger.info("Adding technical features (rolling window = %d)", wl)
    df["rolling_mean"] = df["Close"].rolling(wl).mean()
    df["rolling_std"] = df["Close"].rolling(wl).std()
    df["volatility"] = df["return"].rolling(wl).std() * np.sqrt(252)
    df["max_drawdown"] = _max_drawdown(df["Close"])
    df["price_above_ma"] = (df["Close"] > df["rolling_mean"]).astype(int)      
    
    # Simple Moving Averages
    df[f"SMA{wl}_window"] = wl
    df[f"SMA{wl}_rolling_mean"] = df["Close"].rolling(wl).mean()
    # Bollinger Bands
    df[f"SMA{wl}_rolling_std"] = df["Close"].rolling(wl).std()
    df[f"SMA{wl}_BB_upper"] = df[f"SMA{wl}_rolling_mean"] + (df[f"SMA{wl}_rolling_std"] * 2)
    df[f"SMA{wl}_BB_lower"] = df[f"SMA{wl}_rolling_mean"] - (df[f"SMA{wl}_rolling_std"] * 2)
    df[f"SMA{wl}_BB_width"] = df[f"SMA{wl}_BB_upper"] - df[f"SMA{wl}_BB_lower"]
    df[f"SMA{wl}_BB_percent"] = (df["Close"] - df[f"SMA{wl}_BB_lower"]) / df[f"SMA{wl}_BB_width"]

  # Golden Cross / Death Cross indicator
  # A classic signal:
  # 1 → SMA50 crossed above SMA200 (bullish)
  # 0 → otherwise
  df["golden_cross"] = (df["SMA50_rolling_mean"] > df["SMA200_rolling_mean"]).astype(int)
  df["death_cross"] = (df["SMA50_rolling_mean"] < df["SMA200_rolling_mean"]).astype(int)

  # === MACD CLASSIC (12, 26, 9) ===
  df["EMA12_window"] = 12
  df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
  df["EMA26_window"] = 26
  df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
  df["MACD_12_26"] = df["EMA12"] - df["EMA26"]
  df["MACD_signal_12_26"] = df["MACD_12_26"].ewm(span=9, adjust=False).mean()
  df["MACD_hist_12_26"] = df["MACD_12_26"] - df["MACD_signal_12_26"]
  # === MACD LONG-TERM (50, 200, 9) === 
  df["EMA50_window"] = 50
  df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
  df["EMA200_window"] = 200
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

  # df = df.dropna(subset=["VolumeZscore"])

  return df

def _max_drawdown(prices: pd.Series) -> pd.Series:
  roll_max = prices.cummax()
  drawdown = (prices - roll_max) / roll_max
  return drawdown.cummin()
