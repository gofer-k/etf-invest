import pandas as pd

def detect_inverted_hammer(df: pd.DataFrame) -> pd.Series:
  """
  Detects inverted hammer candlestick patterns in a DataFrame of OHLC data.

  An inverted hammer is characterized by:
  - A small real body at the lower end of the trading range.
  - A long upper shadow that is at least twice the length of the real body.
  - Little to no lower shadow.

  Parameters:
  df (pd.DataFrame): DataFrame containing 'open', 'high', 'low', 'close' columns.

  Returns:
  pd.Series: A boolean Series indicating the presence of inverted hammer patterns.
  """
  open_price = df['open']
  close_price = df['close']
  high_price = df['high']
  low_price = df['low']

  real_body = (close_price - open_price).abs()
  upper_shadow = high_price - pd.concat([open_price, close_price], axis=1).max(axis=1)
  lower_shadow = pd.concat([open_price, close_price], axis=1).min(axis=1) - low_price

  return (
      (close_price > open_price) &
      (upper_shadow > 2 * real_body) &
      (lower_shadow < real_body)
  )
