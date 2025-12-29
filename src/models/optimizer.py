from dataclasses import dataclass
from typing import List

import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NaiveEqualWeightOptimizer:
    def optimize(self, tickers: List[str]) -> dict:
        n = len(tickers)
        if n == 0:
            raise ValueError("No tickers provided")
        weights = np.ones(n) / n
        allocation = dict(zip(tickers, weights))
        logger.info("Equal weight allocation: %s", allocation)
        return allocation
