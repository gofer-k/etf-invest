import pandas as pd

def detect_harami(data: pd.DataFrame) -> pd.Series:
  """
  Detects Harami candlestick patterns in the given DataFrame.

  A Harami pattern is identified when a small real body (the difference between open and close prices)
  is contained within the previous large real body. This function checks for both bullish and bearish Harami patterns.

  Parameters:
  data (pd.DataFrame): DataFrame containing 'open', 'high', 'low', 'close' columns.

  Returns:
  pd.Series: A Series with 1 for bullish Harami, -1 for bearish Harami, and 0 for no pattern.
  """
  prev = data.shift(1)
  return (prev['Close'] < data['Open']) & (data['close'] < prev["Open"])
