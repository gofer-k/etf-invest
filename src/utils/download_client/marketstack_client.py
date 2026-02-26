import aiofiles
import aiohttp
import asyncio
import json

from typing import Dict, List, Optional, Any

class MarketstackError(Exception): pass

class MarketstackClient:
    BASE_URL = "https://api.marketstack.com/v2"

    def __init__(self, api_key: str,
                 timeout: int = 10,
                 max_retries: int = 3,
                 backoff_factor: float = 0.5,
                 concurrency_limit: int = 5,):
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.concurrency_limit = concurrency_limit  
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(concurrency_limit)

    async def __aenter__(self):
      if self._session is not None:
         raise RuntimeError("ClientSession already initialized")
      
      self._session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=self.timeout)
      )
      return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.close()
            self._session = None

    async def _request(self, endpoint: str, params: Dict[str, Any]):
      if self._session is None:
        raise RuntimeError("ClientSession not initialized. Use 'async with'.")
      params["access_key"] = self.api_key
      url = f"{self.BASE_URL}/{endpoint}"
      async with self._semaphore:
        for attempt in range(self.max_retries):
          try:            
            async with self._session.get(url, params=params) as response:
              if response.status == 429:
                delay = self.backoff_factor * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            
              if (response.status >= 500):
                delay = self.backoff_factor * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            
              if (response.status != 200):
                text = await response.text()
                raise MarketstackError(f"HTTP {response.status}: {text}")
                   
              return await response.json()
                
          except asyncio.TimeoutError:                
            if attempt == self.max_retries -1:
              raise MarketstackError("Timeout")
            await asyncio.sleep(self.backoff_factor * (2 ** attempt))

          except aiohttp.ClientError as e:  
            if attempt == self.max_retries - 1:
              raise MarketstackError(f"Connection error: {e}")   
            await asyncio.sleep(self.backoff_factor * (2 ** attempt))

      raise MarketstackError("Max retries exceeded")      

    async def fetch_all_pages(self, endpoint: str, params: Dict[str, Any], limit: int = 100):
        """Automatyczna paginacja."""
        offset = 0
        all_data: List[Dict[str, Any]] = []

        while True:
          page_params = params.copy()
          page_params.update({"limit": limit, "offset": offset})

          data = await self._request(endpoint, page_params)
          chunk = data.get("data", [])

          if not chunk:
            break

          all_data.extend(chunk)
          offset += limit

          # Obsługa next_url (jeśli API zwróci)
          next_url = data.get("pagination", {}).get("next_url")
          if not next_url:
            break

          await asyncio.sleep(0.2)  # delikatne odciążenie API

        return all_data
    
    # -------------------------
    # Endpointy Marketstack
    # -------------------------

    async def intraday(self, symbols: str, interval: str = "1hour", limit: int = 100):
        valid_intervals = {"15min", "30min", "1hour", "3hour", "6hour", "12hour", "24hour"}
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval: {interval}. Must be one of {valid_intervals}")
        
        params = {"symbols": symbols, "interval": interval}
        return await self.fetch_all_pages("intraday", params, limit)

    async def eod(self, symbols: str, limit: int = 100):
        """Dane End-of-Day."""
        params = {"symbols": symbols}
        return await self.fetch_all_pages("eod", params, limit)

    async def tickers(self):
        """Lista tickerów."""
        return await self.fetch_all_pages("tickers", {})

    async def fetch_etfs(self, symbols: str, interval: str = "1hour", limit: int = 100):
      API_KEY = self.api_key

      async with MarketstackClient(API_KEY) as client:
        tasks = [client.intraday(etf, interval) for etf in symbols.split(",")]
        # tasks = [client.eod(etf) for etf in symbols.split(",")]
        results = await asyncio.gather(*tasks)

        return dict(zip(symbols.split(","), results))

    async def save_json(self, filename, data):
      async with aiofiles.open(filename, "w+", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))
