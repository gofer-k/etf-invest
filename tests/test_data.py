from src.utils.config_loader import load_config
from src.data.ingest import load_etf_history
from src.data.preprocess import clean_prices, add_returns


def test_data_pipeline_smoke():
    config = load_config()
    df = load_etf_history("VOO", config, period="1mo", interval="1d")
    df = clean_prices(df)
    df = add_returns(df)

    assert not df.empty
    assert "return" in df.columns
