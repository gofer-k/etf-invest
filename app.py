import argparse

import pandas as pd

from src.data.indicators import AtrConfig, BollingerBandsConfig, EmaConfig, MacdConfig, RsiConfig, SmaConfig
from src.etf_agent.strategy_engine.break_out_engine import BreakOutEngine
from src.utils.config_loader import load_config
from src.utils.logger import get_logger
from src.data.ingest import load_cfg_etf_local_history
from src.data.preprocess import clean_prices, add_returns
from src.data.features import add_technical_features_offline
from src.etf_agent.strategy_engine.decision_engine import MacdStrategyEngine
from src.etf_agent.reports import generate_text_report
from src.backtesting.engine import SimpleBacktester
from src.backtesting.metrics import compute_cagr, compute_sharpe
from src.utils.export import export_compressed_json, export_report_to_json
from src.utils.paths import OUTPUT_DIR
from src.visualization.plotter import plot_interactive_signals

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETF AI Agent CLI")
    parser.add_argument("--ticker", type=str, help="ETF ticker symbol (e.g., VOO)")
    parser.add_argument("--period", type=str, help="Data period (e.g., 1y, 6mo)")
    parser.add_argument("--interval", type=str, help="Data interval (e.g., 1d, 1h)")
    parser.add_argument("--acd_signals", type=str, help="ACD system signals")
    parser.add_argument("--backtest", type=str, help="backtest signals")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()

    ticker = args.ticker or config["data"]["default_ticker"]
    config["features"]["acd_signals"] = args.acd_signals if args.acd_signals else config["features"].get("acd_signals", True)
    config["backtest"]["enabled"] = args.backtest if args.backtest else config["backtest"].get("enabled", False)

    # df = load_etf_history(ticker, config, period=args.period, interval=args.interval)
    df = load_cfg_etf_local_history(ticker)
    df = clean_prices(df)
    # df = add_returns(df)
    # df = add_technical_features_offline(df, config)
    # print("=== ETF REPORT: indicators")
    # print(df[["Close", "SMA50", "SMA200", "golden_cross", "death_cross"]].tail())
    
    if config["backtest"]["enabled"]:
      # backtest_indicators(config, df, ticker)
      config["looback"] = 20
      config["price"] = "Close"
      SmaConfig(window=14)
      SmaConfig(window=30)
      SmaConfig(window=50)
      EmaConfig(window=50)
      EmaConfig(window=200)
      bb = BollingerBandsConfig(window=20, num_std=2.0)
      atr=AtrConfig(window=14, k=1.0)
      macd=MacdConfig(fast_period=12, slow_period=26, signal_period=9)
      rsi=RsiConfig(period=14, exit=45, long=55)
      breakout_test = BreakOutEngine(config)
      pf_a = breakout_test.atr_breakout(df['Close'], df["High"], df["Low"], atr)
      pf_mr = breakout_test.macd_rsi_breakout(df['Close'], macd, rsi)
      pf_bb = breakout_test.bollinger_breakout(df['Close'], bb, use_lower_exit=False)
      breakout_test.summary([pf_a, pf_mr, pf_bb], ["Total Return [%]", "Sharpe Ratio", "Max Drawdown [%]", "Win Rate [%]"])
      breakout_test.plot_equity_curves([pf_a[1], pf_mr[1], pf_bb[1]], ["ATR Breakout", "MACD+RSI Breakout", "Bollinger Bands Breakout"])

    export_report_to_json(df, OUTPUT_DIR / "bollinger_rsi_macd_report.json")
    export_compressed_json(df, OUTPUT_DIR / "bollinger_rsi_macd_report.json.gz")

    if config["features"].get("acd_signals", True):
        backtest_acd_system(config, df)

def backtest_indicators(config: dict, df: pd.DataFrame, ticker: str):
  agent = MacdStrategyEngine(config)
  decision = agent.generate_signals(df)

  report = generate_text_report(ticker, df, decision)
  print(report)
  
  backtest = SimpleBacktester(
      initial_capital=config["backtest"]["initial_capital"],
      transaction_cost_pct=config["backtest"]["transaction_cost_pct"],
  )

  threshold = config["agent"]["signal_threshold"]

  def signal_func(row):
    if row["return"] > threshold:
      return 1
    elif row["return"] < -threshold:
      return -1
    return 0

  result = backtest.run(df, signal_func)
  cagr = compute_cagr(result.equity_curve)
  sharpe = compute_sharpe(result.equity_curve)

  print()
  print("=== BACKTEST SUMMARY ===")
  print(f"Final equity: {result.equity_curve.iloc[-1]:.2f}")
  print(f"CAGR: {cagr:.2%}")
  print(f"Sharpe ratio: {sharpe:.2f}")

    # signals = df.apply(lambda row: "BUY" if row["return"] > threshold 
    #                else "SELL" if row["return"] < -threshold 
    #                else "HOLD", axis=1)    

    # plot_price_indicators_and_signals(df, ticker, signals)

    # agent_signals = df.apply(lambda row: agent.generate_signals(df.loc[:row.name])["action"], axis=1)

    # plot_price_indicators_and_signals(df, ticker, agent_signals)
  signals = df.apply(lambda row: agent.generate_signals(df.loc[:row.name])["action"], axis=1)

  periods = [20, 50, 100, 150, 200, 250]

  for period in periods:
    plot_interactive_signals(df, period, ticker, signals)

def backtest_acd_system(config: dict, df: pd.DataFrame):
  from src.etf_agent.strategy_engine.acd_system import AcdStrategyEngine
  acd = AcdStrategyEngine(config)
  df = acd.pivotRange(df)
  df = acd.opening_range_A(df)
  df = acd.generate_signals(df)
  # acd.plot_signals(df)
  acd.plot_signals_interactive(df)

def backtest_breakout_system(config: dict, df: pd.DataFrame):  
  from src.etf_agent.strategy_engine.break_out_engine import run_vectorbt_breakout

  period = config["backtest"].get("breakout_lookback", 20)
  pf, indicators_df = run_vectorbt_breakout(df, lookback=period, price_field="Close", compute_indicators=[])
  print(pf.stats())
  plot_interactive_signals(indicators_df, period, "Breakout Strategy", pf.signals)

if __name__ == "__main__":
    main()
