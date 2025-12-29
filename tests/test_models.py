from src.utils.config_loader import load_config
from src.data.ingest import load_etf_history
from src.data.preprocess import clean_prices, add_returns
from src.models.forecasting import SimpleForecaster


def test_simple_forecaster_smoke():
    config = load_config()
    df = load_etf_history("VOO", config, period="3mo", interval="1d")
    df = add_returns(clean_prices(df))

    model = SimpleForecaster(lookback=10)
    model.fit(df)
    pred = model.predict_next_return(df)

    assert isinstance(pred, float)
