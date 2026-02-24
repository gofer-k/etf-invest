from abc import abstractmethod

import pandas as pd
from pyparsing import Dict

class StrategyEngine:
    def __init__(self, config: dict = None) -> None:
        self.config = config
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> Dict:
        pass