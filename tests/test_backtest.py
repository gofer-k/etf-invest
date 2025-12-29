from src.utils.config_loader import load_config
from src.data.ingest import load_etf_history
from src.data.preprocess import clean_prices, add_returns
from src.backtesting.engine import SimpleBacktester


def test_backtester_smoke():
    config = load_config()
    df = load_etf_history("VOO", config, period="3mo", interval="1d")
    df = add_returns(clean_prices(df))

    backtester = SimpleBacktester(initial_capital=10000)

    def signal_func(row):
        return 1  # always long

    result = backtester.run(df, signal_func)
    assert not result.equity_curve.empty
