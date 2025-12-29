import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def clean_prices(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Cleaning price data")
    df = df.dropna()
    df = df[df["Volume"] > 0]
    return df


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Adding returns column")
    df = df.copy()
    df["return"] = df["Close"].pct_change()
    return df
