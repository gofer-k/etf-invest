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
import vectorbt as vbt
from vectorbt.indicators.factory import IndicatorFactory

import config
from src.data.indicators import BollingerBandsConfig, IndicatorType, MacdConfig, RsiConfig
from src.etf_agent.strategy_engine.strategy_engine import StrategyEngine


def run_vectorbt_breakout(
	df: pd.DataFrame,
	lookback: int = 20,
	price_field: str = "Close",
	compute_indicators: list = None,
	init_cash: float = 10_000.0,
	fees: float = 0.0,
) -> tuple:
	"""Run a candlestick-based Donchian breakout backtest using vectorbt.

	Behavior changes from the original:
	- Uses `High` / `Low` for breakout detection (candlestick-aware).
	- Allows selecting trading price series via `price_field`:
	  - `Close` (default)
	  - `typical` -> (High + Low + Close) / 3
	  - `vwap` -> requires `Volume` column; computed per row
	- Optional indicator calculation when `compute_indicators=True`.

	Returns a tuple `(pf, indicators_df)` where `pf` is a
	`vectorbt.Portfolio` and `indicators_df` is the input DataFrame
	augmented with indicators (or `None` if `compute_indicators` is False).
	"""

	try:
		import vectorbt as vbt
	except Exception as e:  # pragma: no cover - optional dependency
		raise ImportError("vectorbt is required for this function. Install with `pip install vectorbt`") from e

	# Ensure required columns
	if not {"High", "Low", "Close"}.issubset(df.columns):
		raise ValueError("DataFrame must contain 'High', 'Low' and 'Close' columns")

	# Build the trading price series from the chosen price_field
	if price_field == "Close":
		price = df["Close"].astype(float)
	elif price_field == "typical":
		price = ((df["High"] + df["Low"] + df["Close"]) / 3.0).astype(float)
	elif price_field == "vwap":
		if "Volume" not in df.columns:
			raise ValueError("VWAP requested but 'Volume' column not present")
		# rolling VWAP over each bar (simple): cumulative typical*volume / cumulative volume
		tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
		cum_tp_vol = (tp * df["Volume"]).cumsum()
		cum_vol = df["Volume"].cumsum()
		price = (cum_tp_vol / cum_vol).astype(float)
	else:
		raise ValueError("price_field must be one of: 'Close', 'typical', 'vwap'")

	# Breakout signals use price extremes (High/Low) over lookback
	high_look = df["High"].rolling(window=lookback, min_periods=lookback).max()
	low_look = df["Low"].rolling(window=lookback, min_periods=lookback).min()

	# Entry when current High breaks previous lookback high
	entries = df["High"] > high_look.shift(1)
	# Exit when current Low breaks previous lookback low
	exits = df["Low"] < low_look.shift(1)
	indicators_df = None

	if compute_indicators is not None:
		indicators_df = df.copy()

	for ind in compute_indicators:
		if ind == IndicatorType.SMA:
			indicators_df[ind.params["key"]] = price.rolling(window=ind.params["window"]).mean()
		elif ind == IndicatorType.EMA:
			indicators_df[ind.params["key"]] = price.ewm(span=ind.params["window"], adjust=False).mean()
		elif ind == IndicatorType.ATR:
			high = indicators_df["High"]
			low = indicators_df["Low"]
			close = indicators_df["Close"]
			tr1 = high - low
			tr2 = (high - close.shift(1)).abs()
			tr3 = (low - close.shift(1)).abs()
			tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
			indicators_df[ind.params["key"]] = tr.rolling(window=ind.params["window"]).mean()
		elif ind == IndicatorType.RSI:
			delta = price.diff()
			up = delta.clip(lower=0.0)
			down = -delta.clip(upper=0.0)
			ma_up = up.ewm(alpha=1/ind.params["window"], adjust=False).mean()
			ma_down = down.ewm(alpha=1/ind.params["window"], adjust=False).mean()
			rs = ma_up / ma_down
			indicators_df["RSI"] = 100 - (100 / (1 + rs))
		elif ind == IndicatorType.MACD:
			ema_fast = price.ewm(span=ind.params["fast_period"], adjust=False).mean()
			ema_slow = price.ewm(span=ind.params["slow_period"], adjust=False).mean()
			macd = ema_fast - ema_slow
			signal = macd.ewm(span=ind.params["signal_period"], adjust=False).mean()
			indicators_df[ind.params["key"]] = macd
			indicators_df[ind.params["key_signal"]] = signal
		elif ind == IndicatorType.BollingerBands:
			sma = price.rolling(window=ind.params["window"]).mean()
			std = price.rolling(window=ind.params["window"]).std()
			twice_std = 2 * std
			indicators_df[ind.params["key_upper"]] = sma + twice_std
			indicators_df[ind.params["key_lower"]] = sma - twice_std
			indicators_df[ind.params["key_width"]] = twice_std

	# Build portfolio from boolean entry/exit signals - use chosen price series
	pf = vbt.Portfolio.from_signals(
    price,
    entries,
    exits,
    init_cash=init_cash,
    fees=fees)
	return pf, indicators_df

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
			print(stats[["Total Return [%]", "Sharpe Ratio", "Max Drawdown [%]", "Win Rate [%]", "Trades"]])
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
	
	def generate_sweep_signals(self, df: pd.DataFrame) -> Dict:
		window_highs = [10, 20, 50]
		window_lows = [5, 10, 20]

		price = df[self.config["price"]].astype(float)
		
		hl_grid = self.HLIndicator.run(
    	price,
    	window_high=window_highs,
    	window_low=window_lows
		)

		high_grid = hl_grid.high
		low_grid = hl_grid.low

		entries_grid = (price.vbt.tile(len(window_highs), len(window_lows)) > high_grid.shift(1)) & high_grid.notna()
		exits_grid   = (price.vbt.tile(len(window_highs), len(window_lows)) < low_grid.shift(1)) & low_grid.notna()

		pf_grid = vbt.Portfolio.from_signals(
				close=price.vbt.tile(len(window_highs), len(window_lows)),
				entries=entries_grid,
				exits=exits_grid,
				init_cash=self.config.get("initial_capital", 10_000),
				direction="longonly"
		)
		
		pf_grid.total_return().vbt.heatmap(
				x_levels=window_lows,
				y_levels=window_highs,
				xaxis_title="window_low",
				yaxis_title="window_high"
		).show()

	def run_strategy(self, name, entries, exits, price, init_cash=10_000, fees=0.0005, slippage=0.0005):
		pf = vbt.Portfolio.from_signals(
        close=price,
        entries=entries,
        exits=exits,
        init_cash=init_cash,
        fees=fees,
        slippage=slippage,
        direction="longonly"
    )
		stats = pf.stats()
		print(f"\n=== {name} ===")
		print(stats[["Total Return [%]", "Sharpe Ratio", "Max Drawdown [%]", "Win Rate [%]", "Trades"]])
		return pf

	# Usage:
	# entries_c, exits_c = candlestick_breakout(price)
	# pf_c = run_strategy("Candlestick breakout", entries_c, exits_c, price)
	def candlestick_breakout(self, price, window_high=20, window_low=10):
		hl = self.HLIndicator.run(price, window_high=window_high, window_low=window_low)
		ch_high, ch_low = hl.high, hl.low

		entries = (price > ch_high.shift(1)) & ch_high.notna()
		exits   = (price < ch_low.shift(1)) & ch_low.notna()
		return entries, exits		

	# Usage:
	# entries_a, exits_a = atr_breakout(price, high_, low_, atr_val, window=20, k=1.0)
	# pf_a = run_strategy("ATR breakout", entries_a, exits_a, price)
	def atr_breakout(self, price, high_, low_, atr_val, window=20, k=1.0):
		# ATR indicator
		atr = vbt.ATR.run(high_, low_, price, window=14)
		atr_val = atr.atr
		rolling_high = high_.rolling(window).max()
		rolling_low  = low_.rolling(window).min()

		upper_level = rolling_high + k * atr_val
		lower_level = rolling_low - k * atr_val

		entries = (price > upper_level.shift(1)) & upper_level.notna()
		exits   = (price < lower_level.shift(1)) & lower_level.notna()
		
		return entries, exits
		
	#Usage:
	# entries_mr, exits_mr = macd_rsi_breakout(price)
	# pf_mr = run_strategy("MACD + RSI breakout", entries_mr, exits_mr, price)
	def macd_rsi_breakout(self, price, macd: MacdConfig, rsi: RsiConfig, window_high=20, window_low=10,):
		returns = price.pct_change()
  	# MACD
		macd_ind = vbt.MACD.run(price, fast_window=macd.fast_window, slow_window=macd.slow_window, signal_window=macd.signal_window)
		macd = macd_ind.macd
		macd_signal = macd_ind.signal

		# # RSI
		rsi_ind = vbt.RSI.run(price, rsi.period)
		rsi = rsi_ind.rsi
		rsi_long = rsi.long
		rsi_exit = rsi.exit
		
		hl = self.HLIndicator.run(price, window_high=window_high, window_low=window_low)
		ch_high, ch_low = hl.high, hl.low
		base_entries = (price > ch_high.shift(1)) & ch_high.notna()
		base_exits   = (price < ch_low.shift(1)) & ch_low.notna()
		
		trend_filter = macd > macd_signal
		momentum_long = rsi > rsi_long
		momentum_exit = rsi < rsi_exit
		entries = base_entries & trend_filter & momentum_long
		exits   = base_exits | momentum_exit
		return entries, exits

	# Usage:
	# entries_bb, exits_bb = bollinger_breakout(price, bb_upper, bb_middle, use_lower_exit=False)
	# pf_bb = run_strategy("Bollinger band breakout", entries_bb, exits_bb, price)
	def bollinger_breakout(self, price, bb: BollingerBandsConfig,	use_lower_exit=False):
		bb = vbt.BBANDS.run(price, window= bb.window, alpha=bb.alpha)
		bb_upper = bb.upper
		bb_middle = bb.middle
		bb_lower = bb.lower
    # strict cross
		entries = (price > bb_upper) & (price.shift(1) <= bb_upper.shift(1)) & bb_upper.notna()
		
		if use_lower_exit:
			exits = (price < bb_lower) & (price.shift(1) >= bb_lower.shift(1)) & bb_lower.notna()
		else:
			exits = (price < bb_middle) & (price.shift(1) >= bb_middle.shift(1)) & bb_middle.notna()

		return entries, exits


# Example usage:
# Compare total returns
# summary = pd.DataFrame({
#     "Candlestick": pf_c.total_return(),
#     "ATR": pf_a.total_return(),
#     "MACD+RSI": pf_mr.total_return(),
#     "Bollinger": pf_bb.total_return(),
# }, index=["Total Return"])

# print("\n=== Summary ===")
# print(summary.T.sort_values("Total Return", ascending=False))

# # Example: plot best one
# pf_bb.plot().show()


