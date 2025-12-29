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

    return df


def _max_drawdown(prices: pd.Series) -> pd.Series:
    roll_max = prices.cummax()
    drawdown = (prices - roll_max) / roll_max
    return drawdown.cummin()
