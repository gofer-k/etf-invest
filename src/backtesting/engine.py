from dataclasses import dataclass
from typing import Callable, Dict

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame


@dataclass
class SimpleBacktester:
    initial_capital: float = 10000.0
    transaction_cost_pct: float = 0.0005

    def run(
        self,
        df: pd.DataFrame,
        signal_func: Callable[[pd.Series], int],
    ) -> BacktestResult:
        """
        signal_func: takes row (Series), returns -1 (SELL), 0 (HOLD), 1 (BUY)
        """
        df = df.copy()
        df["signal"] = df.apply(signal_func, axis=1)

        position = 0  # number of units
        cash = self.initial_capital
        equity_curve = []
        trades = []

        logger.info("Starting backtest (initial capital=%.2f)", self.initial_capital)

        for date, row in df.iterrows():
            price = row["Close"]
            signal = row["signal"]

            # Simple: if BUY and flat -> buy full capital
            # if SELL and long -> liquidate
            if signal == 1 and position == 0:
                units = cash / price
                cost = cash * self.transaction_cost_pct
                cash = cash - cost
                position = units
                trades.append(
                    {"date": date, "action": "BUY", "price": price, "units": units}
                )
            elif signal == -1 and position > 0:
                proceeds = position * price
                cost = proceeds * self.transaction_cost_pct
                cash = cash + proceeds - cost
                trades.append(
                    {"date": date, "action": "SELL", "price": price, "units": position}
                )
                position = 0

            equity = cash + position * price
            equity_curve.append((date, equity))

        equity_series = pd.Series(
            [e for _, e in equity_curve],
            index=[d for d, _ in equity_curve],
            name="equity",
        )
        trades_df = pd.DataFrame(trades)

        logger.info("Backtest completed. Final equity=%.2f", equity_series.iloc[-1])

        return BacktestResult(equity_curve=equity_series, trades=trades_df)
