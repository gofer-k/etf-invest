import argparse
import asyncio
import requests
from enum import Enum

from vectorbt.data import Data

from src.utils.download_client.marketstack_client import MarketstackClient
from src.utils.paths import OUTPUT_DIR

class MarketStackEndPoint(Enum):
    """
    https://docs.apilayer.com/marketstack/docs/marketstack-api-v2-v-2-0-0?utm_source=MarketstackHomePage&utm_medium=Referral
    """
    EOD = "eod"        # end of day data
    EOD_DATE = "eod/"  # end of day data from specific dateExample, /eod/2020-01-01"
    EOD_LATEST = "eod/latest" #end of day data for latest date
    INTRADAY = "intraday" # intraday data, requires additional parameters like date or latest
    INTRADAY_LATEST = "intraday/latest"
    INTRADAY_DATE = "intraday/date"  # Example, /intraday/2020-01-01
    

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETF AI Agent CLI")
    parser.add_argument("--apikey", type=str, help="Api key for data provider")
    parser.add_argument("--tickers", type=str, help="list ETF tickers' symbols (e.g., VOO, ...)")
    parser.add_argument("--endpoint", type=str, help="endpoint: intraday|eod|latest")
    parser.add_argument("--date", type=str, help="Data date in YYYY-MM-DD format.  (e.g., 2023-01-01)")
    parser.add_argument("--date_from", type=str, help="Data start date in YYYY-MM-DD format.  (e.g., 2023-01-01)")
    parser.add_argument("--date_to", type=str, help="Data end date in YYYY-MM DD format.  (e.g., 2023-12-31)")
    parser.add_argument("--limit", type=int, help="Pagination limit (default: 100, max: 1000)")
    parser.add_argument("--offset", type=int, help="Pagination offset (default: 0)")
    parser.add_argument("--interval", type=str, help="Data interval (e.g., 15m, 30m, 1hour (Default), 3hour, 6hour, 12hour and 24hour)") 
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.apikey:
        raise ValueError("API key is required. Please provide it using --apikey argument.")
    if not args.tickers:
        raise ValueError("At least one ticker symbol is required. Please provide it using --tickers argument.")
        
def download_data() -> None:
    args = parse_args()
    validate_args(args)
    API_KEY = args.apikey     

    client = MarketstackClient(API_KEY)
    interval = args.interval if args.interval else "1hour"
    limit_requests = args.limit if args.limit else 100
    data = asyncio.run(client.fetch_etfs(args.tickers, interval, limit_requests))

    asyncio.run(client.save_json(OUTPUT_DIR / f"response_data.json", data))
    
if __name__ == "__main__":
    download_data()