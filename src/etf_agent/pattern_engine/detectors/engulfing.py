import pandas as pd
def detect_engulfing(data: pd.DataFrame) -> pd.DataFrame:
  prev = data.shift(1)
  bullish_engulfing = (
    (data['close'] > data['open']) &
    (prev['Close'] < prev['Open']) &
    (data['Close'] > prev['Open']) &
    (data['Open'] < prev['Close'])
  )
  bearish_engulfing = (
    (data['close'] < data['open']) &
    (prev['Close'] > prev['Open']) &
    (data['Open'] > prev['Close']) &
    (data['Close'] < prev['Open'])
  )
  return bullish_engulfing | bearish_engulfing