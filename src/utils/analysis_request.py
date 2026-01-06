from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    symbol_ticker: str
    dataset_source: str | None
    interval: str | None
    rolling_windows: list[int] | None
    strategy: dict | None
    factors: list[str] | None
    features: dict | None
