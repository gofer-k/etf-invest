# === Trend‑Following Logic ===
# The agent will behavior:
# Only BUY when:
#     Long‑term trend is bullish (MA50 > MA200)
#     MACD crosses above signal (momentum confirmation)
#     Drawdown is not extreme
# Only SELL when:
#     Trend turns bearish (MA50 < MA200)
#     MACD crosses below signal (momentum breakdown)
# HOLD otherwise

from dataclasses import dataclass
from typing import Dict

import pandas as pd

from src.models.risk import RiskMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DecisionEngine:
    config: Dict

    def __post_init__(self) -> None:
        agent_cfg = self.config.get("agent", {})
        self.vol_limit = float(agent_cfg.get("volatility_limit", 0.40))  # 40% annual vol
        self.mdd_limit = float(agent_cfg.get("max_drawdown_limit", -0.30))  # -30% MDD

        self.risk_metrics = RiskMetrics()

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """
        Trend-following strategy using:
        - MA50 / MA200 (Golden/Death Cross)
        - MACD (12/26/9)
        - MACD (50/200/9)
        - Risk filters (volatility, drawdown)
        """

        # === Extract latest values ===
        last = df.iloc[-1]

        ma50 = last["MA50"]
        ma200 = last["MA200"]

        macd = last["MACD_12_26"]
        macd_signal = last["MACD_signal_12_26"]

        macd_long = last["MACD_50_200"]
        macd_long_signal = last["MACD_signal_50_200"]

        # === Risk metrics ===
        vol = self.risk_metrics.volatility(df["return"])
        mdd = self.risk_metrics.max_drawdown(df["Close"])

        # === Trend filters ===
        bullish_trend = ma50 > ma200
        bearish_trend = ma50 < ma200

        # === MACD crossovers ===
        macd_bull = macd > macd_signal
        macd_bear = macd < macd_signal

        macd_long_bull = macd_long > macd_long_signal
        macd_long_bear = macd_long < macd_long_signal

        # === Risk filter ===
        risk_ok = (vol < self.vol_limit) and (mdd > self.mdd_limit)

        # === Decision Logic ===
        if bullish_trend and macd_bull and macd_long_bull and risk_ok:
            action = "BUY"
        elif bearish_trend and macd_bear and macd_long_bear:
            action = "SELL"
        else:
            action = "HOLD"

        logger.info(
            "Decision: %s | Trend: %s | MACD: %s | MACD LT: %s | Vol: %.4f | MDD: %.4f",
            action,
            "Bullish" if bullish_trend else "Bearish",
            "Bull" if macd_bull else "Bear",
            "Bull" if macd_long_bull else "Bear",
            vol,
            mdd,
        )

        return {
            "action": action,
            "trend_bullish": bullish_trend,
            "macd_bull": macd_bull,
            "macd_long_bull": macd_long_bull,
            "volatility": vol,
            "max_drawdown": mdd,
        }

# === Initial training te agent decision engine (to be replaced) ===
# from dataclasses import dataclass
# from typing import Dict

# import pandas as pd

# from src.models.forecasting import SimpleForecaster
# from src.models.risk import RiskMetrics
# from src.utils.logger import get_logger

# logger = get_logger(__name__)


# @dataclass
# class DecisionEngine:
#     config: Dict

#     def __post_init__(self) -> None:
#         agent_cfg = self.config.get("agent", {})
#         self.threshold = float(agent_cfg.get("signal_threshold", 0.01))
#         lookback = int(agent_cfg.get("lookback_days", 20))

#         self.forecaster = SimpleForecaster(lookback=lookback)
#         self.risk_metrics = RiskMetrics()

#     def generate_signal(self, df: pd.DataFrame) -> Dict:
#         self.forecaster.fit(df)
#         predicted_ret = self.forecaster.predict_next_return(df)

#         risk = self.risk_metrics.volatility(df["return"])
#         mdd = self.risk_metrics.max_drawdown(df["Close"])

#         if predicted_ret > self.threshold and mdd > -0.2:
#             action = "BUY"
#         elif predicted_ret < -self.threshold:
#             action = "SELL"
#         else:
#             action = "HOLD"

#         logger.info(
#             "Decision: %s (predicted_ret=%.4f, vol=%.4f, mdd=%.4f)",
#             action,
#             predicted_ret,
#             risk,
#             mdd,
#         )

#         return {
#             "action": action,
#             "predicted_return": predicted_ret,
#             "volatility": risk,
#             "max_drawdown": mdd,
#         }
