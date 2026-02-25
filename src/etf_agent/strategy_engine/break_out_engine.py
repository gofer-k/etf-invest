"""VectorBT breakout strategy example utilities.

This module provides a simple Donchian-style breakout backtest using
vectorbt. It implements entry on breakout above the N-bar high and
exit on break below the N-bar low (both using previous-bar values),
and operates on candlestick data (Open/High/Low/Close) rather than
only using the `Close` price.

The implementation supports selecting different price series to trade
on (Close, Typical Price, VWAP when `Volume` exists) and can compute
common indicators useful for filtering or analysis:

- SMA / EMA (moving averages)
- ATR (average true range) for volatility-based position sizing
- RSI for momentum filtering
- MACD for trend confirmation
- Bollinger Bands for volatility

Install with: pip install vectorbt
"""

from __future__ import annotations
from typing import Dict
import pandas as pd
import numpy as np
import vectorbt as vbt
import plotly.express as px
from vectorbt.indicators.factory import IndicatorFactory

import config
from src.data.indicators import AtrConfig, BollingerBandsConfig, IndicatorType, MacdConfig, RsiConfig
from src.etf_agent.strategy_engine.strategy_engine import StrategyEngine

class BreakOutEngine(StrategyEngine):
	def __init__(self, config: dict = None) -> None:
		super().__init__(config=config)

	def generate_signals(self, df: pd.DataFrame) -> Dict:
		#			def run_strategy(name, entries, exits, price, init_cash=10_000, fees=0.0005, slippage=0.0005):
		loopback = self.config["looback"]
		price = df[config["price"]].astype(float)
		# Breakout signals use price extremes (High/Low) over lookback
		high = df["High"].rolling(window=loopback, min_periods=loopback).max()
		low = df["Low"].rolling(window=loopback, min_periods=loopback).min()

		# Long entry: close crosses above rolling high
		entries = price > high.shift(1)

		# Long exit: close crosses below rolling low
		exits = price < low.shift(1)

		entries = entries & high.notna()
		exits = exits & low.notna()

		# Strict entry/exit: only trigger on actual crossovers (not just being above/below)
		# entries = (price > high) & (price.shift(1) <= high.shift(1))
		# exits   = (price < low)  & (price.shift(1) >= low.shift(1))

		pf = vbt.Portfolio.from_signals(
			freq='D',	# use daily frequency for stats and plotting (can be adjusted based on your data)
			close=price,
			entries=entries,
			exits=exits,
			init_cash=self.config.get("initial_capital", 10_000),
			fees=self.config.get("transaction_cost_pct", 0.0005),	# commission per trade + spread
			slippage=self.config.get("slippage_pct", 0.0005),
			direction="longonly",	# learn about this options here: https://vectorbt.dev/api/vbt.Portfolio.from_signals.html and in general the different ways to build a portfolio: https://vectorbt.dev/guide/portfolio.html
			stop_loss=self.config.get("stop_loss_pct", 0.05), # 5% below entry
			take_profit=self.config.get("take_profit_pct", 0.1) # 10% above entry
		)

		stats = pf.stats()
		if self.config.get("print_stats", True):
			print(f"\n=== {self.config['name']} ===")
			cols_to_print = ["Total Return [%]", "Sharpe Ratio", "Max Drawdown [%]", "Win Rate [%]", "Trades"]
			available_cols = [c for c in cols_to_print if c in stats.index]
			if available_cols:
				print(stats[available_cols])
			else:
				print(stats)
		if (self.config.get("plot_equity_curve", True)):
			pf.plot().show()
			pf.plot_equity().show()
			pf.plot_drawdowns().show()
			pf.plot_trades().show()
			pf.plot_indicators().show()  # only works if indicators were computed and added to the portfolio
		return pf

	def rolling_hl_nb(close, window_high, window_low):
		high = close.rolling(window_high).max()
		low = close.rolling(window_low).min()
		return high, low

	HLIndicator = IndicatorFactory(
		class_name="HLIndicator",
		input_names=["close"],
		param_names=["window_high", "window_low"],
		output_names=["high", "low"]
	).from_apply_func(
		rolling_hl_nb,
		keep_pd=True
	)
	
	def _run_strategy(self, name, entries, exits, price, init_cash=10_000, fees=0.0005, slippage=0.0005) -> tuple[str, vbt.Portfolio]:
		pf = vbt.Portfolio.from_signals(
		    freq='D',
	        close=price,
	        entries=entries,
	        exits=exits,
	        init_cash=init_cash,
	        fees=fees,
	        slippage=slippage,
	        direction="longonly",
	    )
		return (name, pf)

	# Usage:
	# BreakOutEngine().candlestick_breakout(price)
	def candlestick_breakout(self, price, window_high=20, window_low=10):
		hl = self.HLIndicator.run(price, window_high=window_high, window_low=window_low)
		ch_high, ch_low = hl.high, hl.low

		entries = (price > ch_high.shift(1)) & ch_high.notna()
		exits   = (price < ch_low.shift(1)) & ch_low.notna()

		pf = self._run_strategy("Candlestick breakout", entries, exits, price)
		pf.plot().show()	
		return pf	

	# Usage:
	# BreakOutEngine().breakout(price, high_, low_, atr_val, window=20, k=1.0)
	def atr_breakout(self, price, high_, low_, atr: AtrConfig):
		atr_ind = vbt.ATR.run(high_, low_, price, window=atr.params["window"])
		atr_val = atr_ind.atr
		rolling_high = high_.rolling(window=atr.params["window"]).max()
		rolling_low  = low_.rolling(window=atr.params["window"]).min()

		upper_level = rolling_high + atr.params["k"] * atr_val
		lower_level = rolling_low - atr.params["k"] * atr_val

		entries = (price > upper_level.shift(1)) & upper_level.notna()
		exits   = (price < lower_level.shift(1)) & lower_level.notna()
		pf = self._run_strategy("ATR breakout", entries, exits, price)
		# pf.plot(title="ATR Breakout Strategy").show()
		return pf
		
	#Usage:
	# BreakOutEngine().macd_rsi_breakout(price)# 
	def macd_rsi_breakout(self, price, macd: MacdConfig, rsi: RsiConfig, window_high=20, window_low=10,):
		"""
		Combines Donchian breakout with MACD and RSI filters:
		- Entry: price breaks above N-bar high AND MACD > signal AND RSI > long threshold
		- Exit: price breaks below N-bar low OR RSI < exit threshold
		This allows for more selective entries that align with trend and momentum, while still using the breakout levels for timing.
		Using different windows for entry and exit is a classic trend‑following technique:
		| window_high	| Entry breakout | Larger window → fewer but stronger breakouts |
		| window_low	| Exit breakout  | Smaller window → tighter stops, quicker exits |
		This gives you a Donchian‑style breakout with asymmetric entry/exit timing.
		"""
		returns = price.pct_change()
  	# MACD
		macd_ind = vbt.MACD.run(price, fast_window=macd.params["fast_period"], slow_window=macd.params["slow_period"], signal_window=macd.params["signal_period"])
		macd_vals = macd_ind.macd
		macd_signal = macd_ind.signal

		# # RSI
		rsi_ind = vbt.RSI.run(price, rsi.params["period"])
		rsi_vals = rsi_ind.rsi
		rsi_long = rsi.params["long"]
		rsi_exit = rsi.params["exit"]
		
		hl = self.HLIndicator.run(price, window_high=window_high, window_low=window_low)
		ch_high, ch_low = hl.high, hl.low
		base_entries = (price > ch_high.shift(1)) & ch_high.notna()
		base_exits   = (price < ch_low.shift(1)) & ch_low.notna()
		
		trend_filter = macd_vals > macd_signal
		momentum_long = rsi_vals > rsi_long
		momentum_exit = rsi_vals < rsi_exit
		entries = base_entries & trend_filter & momentum_long
		exits   = base_exits | momentum_exit
		pf = self._run_strategy("MACD + RSI breakout", entries, exits, price)
		# pf.plot(title="MACD + RSI Breakout Strategy").show()	
		return pf	

	# Usage:
	# BreakOutEngine().bollinger_breakout(price, bb_upper, bb_middle, use_lower_exit=False)
	def bollinger_breakout(self, price, bb: BollingerBandsConfig,	use_lower_exit=False):
		bb_ind = vbt.BBANDS.run(price, window=bb.params["window"], alpha=bb.params["num_std"])
		bb_upper = bb_ind.upper
		bb_middle = bb_ind.middle
		bb_lower = bb_ind.lower
    # strict cross
		entries = (price > bb_upper) & (price.shift(1) <= bb_upper.shift(1)) & bb_upper.notna()
		
		if use_lower_exit:
			exits = (price < bb_lower) & (price.shift(1) >= bb_lower.shift(1)) & bb_lower.notna()
		else:
			exits = (price < bb_middle) & (price.shift(1) >= bb_middle.shift(1)) & bb_middle.notna()

		pf = self._run_strategy("Bollinger band breakout", entries, exits, price)
		# pf.plot(title="Bollinger Band Breakout Strategy").show()		
		return pf


	def summary(self, portfolios: [], desired_metrics: []):
		rows = {}
		for item in portfolios:
			stats	= item[1].stats()
			name = item[0] if hasattr(item, "__len__") and len(item) > 1 else "Strategy"
			row = {m: (stats[m] if m in stats.index else pd.NA) for m in desired_metrics}
			rows[name] = row
		summary = pd.DataFrame.from_dict(rows, orient='index')

		print("\n=== Summary ===")
		if "Total Return [%]" in summary.columns:
			print(summary.sort_values("Total Return [%]", ascending=False))
		else:
			print(summary)

	def plot_equity_curves(self, portfolios: [], titles: []):
		for pf, title in zip(portfolios, titles):
			pf.plot(title=title).show()



