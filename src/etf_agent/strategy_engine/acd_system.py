from enum import Enum
from re import match

from matplotlib import pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dataclasses import dataclass
from src.etf_agent.strategy_engine.strategy_engine import StrategyEngine
from src.models.forecasting import SimpleForecaster
from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class AcdStrategyEngine(StrategyEngine):

    def __init__(self, config: dict = None) -> None:
        super().__init__(config=config)

    def pivotRange(self, df):
        """
        df must have columns: ['Close', 'High', 'Low']
        """
        
        df["PivotD"] = (df["Close"].shift(1) + df["High"].shift(1) + df["Low"].shift(1)) / 3
        df["TopPRD"] = (df["High"].shift(1) + df["Low"].shift(1)) / 2
        df["BottomPRD"] = 2 * df["PivotD"] - df["TopPRD"]

        sample = df.resample('W').agg({'Close': 'last', 'High': 'max', 'Low': 'min'})            
        df["PivotW"] = (sample["Close"] + sample["High"] + sample["Low"]) / 3
        df["TopPRW"] = (sample["High"] + sample["Low"]) / 2
        df["BottomPRW"] = 2 * df["PivotW"] - df["TopPRW"]

        return df         

    def opening_range_A(self, df, or_minutes = 30, A_value = 0.5):
      # assumes data with a DAteTimeIndex and a 'session' column grouped by session
      # df['Date'] = df.index.date
      or_high = []
      or_low = []
      for date, group in df.groupby('Date'):
        start_time = group.index[0]
        or_end = start_time + pd.Timedelta(minutes= or_minutes)
        on_window = group[group.index <= or_end]
        high = on_window['High'].max()
        low = on_window['Low'].min()
        or_high.append(pd.Series(high, index=on_window.index))
        or_low.append(pd.Series(low, index=on_window.index))

      df['OR_High'] = pd.concat(or_high).sort_index()
      df['OR_Low'] = pd.concat(or_low).sort_index()
      df['A_up'] = df['OR_High'] + A_value
      df['A_down'] = df['OR_Low'] - A_value
      return df

    def generate_signals(self, df):
      # Simple confirmation: close crosses above A_value
      df['long_signal'] = (df['Close'] > df['A_up']) & (df['Close'].shift(1) <= df['A_up'].shift(1))
      df['short_signal'] = (df['Close'] < df['A_down']) & (df['Close'].shift(1) >= df['A_down'].shift(1))

      # Filter by pivot range
      df['long_signal'] = df['long_signal'] & (df['Close'] > df['TopPRD']) & (df['Close'] > df['TopPRW'])
      df['short_signal'] = df['short_signal'] & (df['Close'] < df['BottomPRD']) & (df['Close'] < df['BottomPRW'])
      return df
    
    def plot_signals(self, df):
        fig, ax = plt.subplots(figsize=(12, 6))

        # price
        ax.plot(df.index, df['Close'], label='Close', color='black', linewidth = 1.0)

        # Daily pivot range
        ax.plot(df.index, df['TopPRD'], label='Top Pivot (Daily)', color='green', linestyle='--', alpha=0.7)
        ax.plot(df.index, df['PivotD'], label='Pivot (Daily)', color='gold', linestyle='-', alpha=0.7)
        ax.plot(df.index, df['BottomPRD'], label='Bottom Pivot (Daily)', color='red', linestyle='--', alpha=0.7)
        
        # Weekly pivot range
        ax.plot(df.index, df['TopPRW'], label='Top Pivot (Weekly)', color='green', linestyle=':', alpha=0.6)
        ax.plot(df.index, df['PivotW'], label='Pivot (Weekly)', color='orange', linestyle='-', alpha=0.6)
        ax.plot(df.index, df['BottomPRW'], label='Bottom Pivot (Weekly)', color='red', linestyle=':', alpha=0.6)


        # A-levels
        ax.plot(df.index, df['A_up'], label='A up', color='lime', linestyle='-.', alpha=0.8)
        ax.plot(df.index, df['A_down'], label='A down', color='magenta', linestyle='-.', alpha=0.8)

        # Long / short signals
        long_idx = df[df['long_signal']].index
        short_idx = df[df['short_signal']].index
        ax.scatter(long_idx, df.loc[long_idx, 'Close'], marker='^', color='green', label='Long entry', s=80, zorder = 5)
        ax.scatter(short_idx, df.loc[short_idx, 'Close'], marker='v', color='red', label='Short entry', s=80, zorder = 5)
        
        ax.set_title('ACD System Signals')
        ax.set_xlabel('DateTime')
        ax.set_ylabel('Price')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        fig.autofmt_xdate()               

        try:
          plt.tight_layout()
          plt.savefig('output/acd_signals_plot.png', dpi=800, bbox_inches='tight')
          plt.close()
          fig.write_html('output/acd_signals_plot.html' )
        except Exception:
          print(f"[INFO] No browser display. Saving interactive charts to HTML.")          

    def plot_signals_interactive(self, df):
      fig = make_subplots(rows=1, cols=1,
               shared_xaxes=True,
               vertical_spacing=0.05)

      # Price
      fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close', 
                  line=dict(color='black', width=1)))

      # Daily pivot range
      fig.add_trace(go.Scatter(x=df.index, y=df['TopPRD'], name='Top Pivot (Daily)', 
                  line=dict(color='green', dash='dash', width=1)))
      fig.add_trace(go.Scatter(x=df.index, y=df['PivotD'], name='Pivot (Daily)', 
                  line=dict(color='gold', width=1)))
      fig.add_trace(go.Scatter(x=df.index, y=df['BottomPRD'], name='Bottom Pivot (Daily)', 
                  line=dict(color='red', dash='dash', width=1)))
      
      # Weekly pivot range
      fig.add_trace(go.Scatter(x=df.index, y=df['TopPRW'], name='Top Pivot (Weekly)', 
                  line=dict(color='green', dash='dot', width=1)))
      fig.add_trace(go.Scatter(x=df.index, y=df['PivotW'], name='Pivot (Weekly)', 
                  line=dict(color='orange', width=1)))
      fig.add_trace(go.Scatter(x=df.index, y=df['BottomPRW'], name='Bottom Pivot (Weekly)', 
                  line=dict(color='red', dash='dot', width=1)))

      # A-levels
      fig.add_trace(go.Scatter(x=df.index, y=df['A_up'], name='A up', 
                  line=dict(color='lime', dash='dashdot', width=1)))
      fig.add_trace(go.Scatter(x=df.index, y=df['A_down'], name='A down', 
                  line=dict(color='magenta', dash='dashdot', width=1)))

      # Long / short signals
      long_idx = df[df['long_signal']].index
      short_idx = df[df['short_signal']].index
      
      fig.add_trace(go.Scatter(x=long_idx, y=df.loc[long_idx, 'Close'], 
                  mode='markers', name='Long entry',
                  marker=dict(symbol='triangle-up', color='green', size=8)))
      fig.add_trace(go.Scatter(x=short_idx, y=df.loc[short_idx, 'Close'], 
                  mode='markers', name='Short entry',
                  marker=dict(symbol='triangle-down', color='red', size=8)))

      fig.update_layout(title='ACD System Signals', xaxis_title='DateTime', 
               yaxis_title='Price', hovermode='x unified', height=600)
      fig.update_xaxes(rangeslider_visible=False)

      try:
        fig.write_html('output/acd_signals_plot.html')
        logger.info("Interactive chart saved to output/acd_signals_plot.html")
      except Exception as e:
        logger.error(f"Error saving interactive chart: {e}")   