from typing import Dict

try:
    import yfinance as yf
except Exception as _exc:  # pragma: no cover - import-time guard
    yf = None
    _YF_IMPORT_ERROR = _exc

import pandas as pd
from pathlib import Path
from typing import Dict

from src.utils.paths import RAW_DATA_DIR
from src.utils.logger import get_logger


logger = get_logger(__name__)


def load_etf_history(
    ticker: str,
    config: Dict,
    period: str | None = None,
    interval: str | None = None,
) -> pd.DataFrame:
    if yf is None:
        raise ImportError(
            "The `yfinance` package is required to download ETF history. "
            "Install it with `pip install yfinance` or `pip install -r requirements.txt`."
        ) from _YF_IMPORT_ERROR

    data_cfg = config.get("data", {})
    period = period or data_cfg.get("period", "1y")
    interval = interval or data_cfg.get("interval", "1d")

    logger.info(
        "Downloading data for %s (period=%s, interval=%s)", ticker, period, interval
    )

    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True)

    if df.empty:
        raise ValueError(f"No data returned for ticker {ticker}")

    df.index = df.index.tz_localize(None)
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    logger.info("Downloaded %d rows for %s", len(df), ticker)
    return df

def load_etf_local_history(
    ticker: str,
    config: Dict,
    period: str | None = None,
    interval: str | None = None,
) -> pd.DataFrame:
    """
    Load ETF historical data from a local CSV file instead of yfinance.
    CSV must be located in data/raw/<TICKER>.csv
    """

    file_path = RAW_DATA_DIR / f"{ticker}.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"Local CSV not found: {file_path}")

    logger.info("Loading local CSV for %s from %s", ticker, file_path)

    df = pd.read_csv(file_path, parse_dates=["Date"], date_format="%m/%d/%Y", thousands=",", quotechar='"')
    df = df.set_index("Date")

    required_cols = {"Open", "High", "Low", "Close", "Volume"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"CSV for {ticker} is missing required columns: {required_cols}"
        )

    logger.info("Loaded %d rows for %s", len(df), ticker)
    return df

logger = get_logger(__name__)



