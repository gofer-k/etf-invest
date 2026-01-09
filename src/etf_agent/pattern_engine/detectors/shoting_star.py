import pandas as pd

def detect_shooting_star(candle: pd.DataFrame) -> pd.Series:
  """
  Detects Shooting Star candlestick patterns in the given DataFrame.

  A Shooting Star is characterized by:
  - A small real body near the lower end of the trading range.
  - A long upper shadow that is at least twice the length of the real body.
  - Little to no lower shadow.

  Parameters:
  candle (pd.DataFrame): DataFrame containing 'open', 'high', 'low', 'close' columns.

  Returns:
  pd.Series: A boolean Series indicating the presence of a Shooting Star pattern.
  """
  open_price = candle['open']
  close_price = candle['close']
  high_price = candle['high']
  low_price = candle['low']

  real_body = (close_price - open_price).abs()
  upper_shadow = high_price - pd.concat([open_price, close_price], axis=1).max(axis=1)
  lower_shadow = pd.concat([open_price, close_price], axis=1).min(axis=1) - low_price

  shooting_star = (
      (upper_shadow >= 2 * real_body) &
      (lower_shadow < real_body) &
      (close_price < open_price)
  )

  return shooting_star