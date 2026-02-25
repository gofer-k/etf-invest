from enum import Enum

class IndicatorType(Enum):
    MACD = "MACD"
    RSI = "RSI"
    BB = "Bollinger Bands"
    SMA = "Simple Moving Average"
    EMA = "Exponential Moving Average"
    ATR = "Average True Range"
    ACD = "ACD System"


class IndicatorConfig:
    def __init__(self, indicator_type: IndicatorType, params: dict):
        self.indicator_type = indicator_type
        self.params = params


class SmaConfig(IndicatorConfig):
    def __init__(self, window: int = 20):
        super().__init__(IndicatorType.SMA, {
            "window": window,
            "key": "SMA{}".format(window)
        })

class EmaConfig(IndicatorConfig):
    def __init__(self, window: int = 20):
        super().__init__(IndicatorType.EMA, {
            "window": window,
            "key": "EMA{}".format(window)
        })


class BollingerBandsConfig(IndicatorConfig):
    def __init__(self, window: int = 20, num_std: float = 2.0):
        super().__init__(IndicatorType.BB, {
            "window": window,
            "num_std": num_std,
            "key_upper": "BB_upper{}".format(window),
            "key_lower": "BB_lower{}".format(window),
            "key_width": "BB_width{}".format(window),
        })

class AtrConfig(IndicatorConfig):
    def __init__(self, window: int = 14, k: float = 1.0):
        super().__init__(IndicatorType.ATR, {
            "window": window,
            "k": k,
            "key": "ATR_{}".format(window)
        })

class MacdConfig(IndicatorConfig):
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__(IndicatorType.MACD, {
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period,
            "key": "MACD_{}_{}".format(fast_period, slow_period),
            "key_signal": "MACD_signal_{}_{}".format(fast_period, slow_period),
        })            


class RsiConfig(IndicatorConfig):
    def __init__(self, period: int = 14, exit: int = 45, long: int = 55):
        super().__init__(IndicatorType.RSI, {
            "period": period,
            "key": "RSI",
            "exit": exit,
            "long": long
        })        