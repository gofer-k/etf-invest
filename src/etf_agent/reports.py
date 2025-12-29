from typing import Dict

import pandas as pd


def generate_text_report(ticker: str, df: pd.DataFrame, decision: Dict) -> str:
    last_close = float(df["Close"].iloc[-1])
    action = decision["action"]
    pred_ret = decision["predicted_return"]
    vol = decision["volatility"]
    mdd = decision["max_drawdown"]

    lines = [
        f"=== ETF REPORT: {ticker} ===",
        f"Last close price: {last_close:.2f}",
        f"Predicted next-day return: {pred_ret:.4%}",
        f"Annualized volatility: {vol:.2%}",
        f"Max drawdown (sample): {mdd:.2%}",
        "",
        f"Action suggestion: {action}",
        "",
        "Note: This is an experimental model-based suggestion, ",
        "not financial advice. Review before acting.",
    ]
    return "\n".join(lines)
