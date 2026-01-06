import argparse

from src.utils.config_loader import load_config
from src.utils.logger import get_logger
from src.data.ingest import load_etf_history
from src.data.ingest import load_etf_local_history
from src.data.preprocess import clean_prices, add_returns
from src.data.features import add_technical_features
from src.etf_agent.decision_engine import DecisionEngine
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()

    ticker = args.ticker or config["data"]["default_ticker"]

    # df = load_etf_history(ticker, config, period=args.period, interval=args.interval)
    df = load_etf_local_history(ticker, period=args.period, interval=args.interval)
    df = clean_prices(df)
    df = add_returns(df)
    df = add_technical_features(df, config)
    print("=== ETF REPORT: indicators")
    print(df[["Close", "SMA50", "SMA200", "golden_cross", "death_cross"]].tail())

    agent = DecisionEngine(config)
    decision = agent.generate_signal(df)

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

    # agent_signals = df.apply(lambda row: agent.generate_signal(df.loc[:row.name])["action"], axis=1)

    # plot_price_indicators_and_signals(df, ticker, agent_signals)
    
    signals = df.apply(lambda row: agent.generate_signal(df.loc[:row.name])["action"], axis=1)

    periods = [20, 50, 100, 150, 200, 250]

    for period in periods:
        plot_interactive_signals(df, period, ticker, signals)
    
    export_report_to_json(df, OUTPUT_DIR / "bollinger_rsi_macd_report.json")
    export_compressed_json(df, OUTPUT_DIR / "bollinger_rsi_macd_report.json.gz")

if __name__ == "__main__":
    main()
