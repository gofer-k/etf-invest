from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskMetrics:
    annualization_factor: int = 252

    def volatility(self, returns: pd.Series) -> float:
        vol = float(returns.std() * (self.annualization_factor ** 0.5))
        logger.info("Annualized volatility: %.4f", vol)
        return vol

    def max_drawdown(self, prices: pd.Series) -> float:
        roll_max = prices.cummax()
        drawdown = (prices - roll_max) / roll_max
        mdd = float(drawdown.min())
        logger.info("Max drawdown: %.4f", mdd)
        return mdd

    def value_at_risk(self, returns: pd.Series, alpha: float = 0.05) -> float:
        var = float(np.quantile(returns.dropna(), alpha))
        logger.info("VaR at alpha=%.2f: %.4f", alpha, var)
        return var
