from dataclasses import dataclass
from typing import Dict

import pandas as pd

from src.models.forecasting import SimpleForecaster
from src.models.risk import RiskMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DecisionEngine:
    config: Dict

    def __post_init__(self) -> None:
        agent_cfg = self.config.get("agent", {})
        self.threshold = float(agent_cfg.get("signal_threshold", 0.01))
        lookback = int(agent_cfg.get("lookback_days", 20))

        self.forecaster = SimpleForecaster(lookback=lookback)
        self.risk_metrics = RiskMetrics()

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        self.forecaster.fit(df)
        predicted_ret = self.forecaster.predict_next_return(df)

        risk = self.risk_metrics.volatility(df["return"])
        mdd = self.risk_metrics.max_drawdown(df["Close"])

        if predicted_ret > self.threshold and mdd > -0.2:
            action = "BUY"
        elif predicted_ret < -self.threshold:
            action = "SELL"
        else:
            action = "HOLD"

        logger.info(
            "Decision: %s (predicted_ret=%.4f, vol=%.4f, mdd=%.4f)",
            action,
            predicted_ret,
            risk,
            mdd,
        )

        return {
            "action": action,
            "predicted_return": predicted_ret,
            "volatility": risk,
            "max_drawdown": mdd,
        }
