import pandas as pd

from detectors.doji import detect_doji
from detectors.hammer import detect_hammer
from detectors.inverted_hammer import detect_inverted_hammer
from detectors.engulfing import detect_engulfing
from detectors.shoting_star import detect_shooting_star
from detectors.morning_star import detect_morning_star

DETECTORS = {
  "doji": detect_doji,
  "hammer": detect_hammer,
  "inverted_hammer": detect_inverted_hammer,
  "engulfing": detect_engulfing,
  "shooting_star": detect_shooting_star,
  "morning_star": detect_morning_star,
}

def detect_patterns(df: pd.DataFrame) -> pd.DataFrame:
  """
  Detects various candlestick patterns in the given DataFrame.

  Parameters:
  df (pd.DataFrame): DataFrame containing 'Open', 'High', 'Low', 'Close' columns.

  Returns:
  pd.DataFrame: DataFrame with additional boolean columns for each detected pattern.
  """
  results = []
  for name, detector in DETECTORS.items():
    pattern_series = detector(df)
    for idx in df[pattern_series].index:
      row = df.loc[idx]      
      results.append({        
        "date": df.at[idx, 'Date'],
        "pattern": name,
        "price": float(row['Close']),
      })
      
  return results