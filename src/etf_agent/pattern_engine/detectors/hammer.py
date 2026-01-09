import pandas as pd

def detect_hammer(df: pd.DataFrame) -> pd.Series:
  open_price = df['open']
  close_price = df['close']
  high_price = df['high']
  low_price = df['low']

  body = (close_price - open_price).abs()
  # lower_shadow = (df[["Open", "Close"]].min(axis=1) - low_price).abs()
  lower_shadow = (pd.concat([open_price, close_price], axis=1).min(axis=1) - low_price).abs()
  upper_shadow = high_price - pd.concat([open_price, close_price], axis=1).max(axis=1)  

  return (
    lower_shadow >= 2 * body) & upper_shadow < body & (close_price > open_price)  # bullish hammer condition

