from src.data.features import add_technical_features
from src.data.ingest import load_etf_local_history
from src.data.preprocess import add_returns, clean_prices
from fastapi import FastAPI
from src.utils.analysis_request import AnalysisRequest
from src.utils.export import export_compressed_json, export_report_to_json
from src.utils.paths import OUTPUT_DIR

app = FastAPI()

@app.post("/analytics/run")
def run_analysis(request: AnalysisRequest):
  df = {}  
  df = load_etf_local_history(request.dataset_source, request.symbol_ticker)
  df = clean_prices(df)
  df = add_returns(df)
  df = add_technical_features(df, request)

  export_report_to_json(df, OUTPUT_DIR / f"technical_report_{request.symbol_ticker}.json")
  output = export_compressed_json(df, OUTPUT_DIR / f"technical_report_{request.symbol_ticker}.gz")
  # return df.to_dict(orient="records")
  return {
    "format": "gz",
    "response_file": output
    }
