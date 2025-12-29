from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SimpleForecaster:
    lookback: int = 20

    def __post_init__(self) -> None:
        self.model = LinearRegression()

    def fit(self, df: pd.DataFrame) -> None:
        if "return" not in df.columns:
            raise ValueError("DataFrame must contain 'return' column")

        logger.info("Fitting SimpleForecaster with lookback=%d", self.lookback)

        returns = df["return"].dropna()
        if len(returns) <= self.lookback:
            raise ValueError("Not enough data to fit model")

        X = []
        y = []
        for i in range(self.lookback, len(returns)):
            X.append(returns.iloc[i - self.lookback : i].values)
            y.append(returns.iloc[i])

        X_arr = np.vstack(X)
        y_arr = np.array(y)

        self.model.fit(X_arr, y_arr)
        logger.info("Model fitted on %d samples", len(y_arr))

    def predict_next_return(self, df: pd.DataFrame) -> float:
        returns = df["return"].dropna()
        if len(returns) < self.lookback:
            raise ValueError("Not enough data to predict")

        last_window = returns.iloc[-self.lookback :].values.reshape(1, -1)
        pred = float(self.model.predict(last_window)[0])
        logger.info("Predicted next return: %.5f", pred)
        return pred
