import pandas as pd
import numpy as np


def compute_cagr(equity_curve: pd.Series) -> float:
    if len(equity_curve) < 2:
        return 0.0

    start = float(equity_curve.iloc[0])
    end = float(equity_curve.iloc[-1])
    days = (equity_curve.index[-1] - equity_curve.index[0]).days
    years = days / 365.25
    if years <= 0:
        return 0.0
    return (end / start) ** (1 / years) - 1


def compute_sharpe(equity_curve: pd.Series, risk_free_rate: float = 0.0) -> float:
    returns = equity_curve.pct_change().dropna()
    if len(returns) == 0:
        return 0.0
    excess = returns - risk_free_rate / 252
    return float(np.sqrt(252) * excess.mean() / excess.std())
