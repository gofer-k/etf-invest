from src.utils.config_loader import load_config
from src.data.ingest import load_etf_history
from src.data.preprocess import clean_prices, add_returns
from src.etf_agent.strategy_engine.decision_engine import MacdStrategyEngine


def test_agent_decision_smoke():
    config = load_config()
    df = load_etf_history("VOO", config, period="3mo", interval="1d")
    df = add_returns(clean_prices(df))

    agent = MacdStrategyEngine(config)
    decision = agent.generate_signals(df)

    assert decision["action"] in {"BUY", "SELL", "HOLD"}
