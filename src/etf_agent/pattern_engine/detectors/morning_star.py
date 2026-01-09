import pandas as pd

def detect_morning_star(df: pd.DataFrame) -> pd.Series:
  """
  Detects Morning Star candlestick patterns in the given DataFrame.

  A Morning Star pattern is a bullish reversal pattern that consists of three candles:
  1. A long bearish candle.
  2. A small-bodied candle (can be bullish or bearish) that gaps down from the first candle.
  3. A long bullish candle that closes well into the body of the first candle.

  Parameters:
  df (pd.DataFrame): DataFrame containing 'open', 'high', 'low', 'close' columns.

  Returns:
  pd.Series: A boolean Series indicating the presence of Morning Star patterns.
  """
  morning_star = pd.Series(False, index=df.index)

  for i in range(2, len(df)):
    first_candle = df.iloc[i - 2]
    second_candle = df.iloc[i - 1]
    third_candle = df.iloc[i]

    # First candle: long bearish
    first_bearish = first_candle['close'] < first_candle['open']
    first_long = (first_candle['open'] - first_candle['close']) > (first_candle['high'] - first_candle['low']) * 0.6

    # Second candle: small body, gaps down
    second_small_body = abs(second_candle['close'] - second_candle['open']) < (second_candle['high'] - second_candle['low']) * 0.3
    second_gaps_down = second_candle['high'] < first_candle['close']

    # Third candle: long bullish
    third_bullish = third_candle['close'] > third_candle['open']
    third_long = (third_candle['close'] - third_candle['open']) > (third_candle['high'] - third_candle['low']) * 0.6
    third_closes_into_first = third_candle['close'] > (first_candle['open'] + first_candle['close']) / 2

    if (first_bearish and first_long and
      second_small_body and second_gaps_down and
      third_bullish and third_long and third_closes_into_first):
      morning_star.iloc[i] = True

  return morning_star