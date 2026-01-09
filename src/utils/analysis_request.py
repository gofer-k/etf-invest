from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    symbol_ticker: str
    dataset_source: str | None
    interval: str | None
    period: str | None
    rolling_windows: list[int] | None
    strategy: dict | None
    tech_indicators: list[str] | None
