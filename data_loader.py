import asyncio
import aiohttp
import pandas as pd
import yfinance as yf
from typing import List, Optional

class DataLoader:
    def __init__(self, max_concurrent_requests: int = 5):
        self.max_concurrent_requests = max_concurrent_requests
        self.failed_tickers = []  # Add a list to track failed tickers

    @staticmethod
    def read_tickers(file_path: str) -> List[str]:
        """Read tickers from a Python list in a text file."""
        with open(file_path, "r") as f:
            content = f.read().strip()
        if content.startswith("[") and content.endswith("]"):
            tickers = eval(content)  # Assuming trusted file
        else:
            tickers = content.splitlines()
        return [t.strip().upper() for t in tickers if t.strip()]

    async def _fetch_stock_data_async(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch single stock data asynchronously"""
        try:
            # Fetch 410 days of data (enough for SMA150 calculation on 260 trading days)
            data = yf.download(symbol, period="410d", interval="1d", auto_adjust=False, progress=False)
            if data.empty:
                self.failed_tickers.append(symbol)  # Track symbols with empty data
                return None

            # Apply split adjustment
            if "Stock Splits" in data.columns:
                splits = data["Stock Splits"].replace(0, 1).cumprod()
                for col in ["Open", "High", "Low", "Close"]:
                    data[col] = data[col] / splits

            return data[["Open", "High", "Low", "Close", "Volume"]]
        except Exception:
            self.failed_tickers.append(symbol)  # Track symbols that raised exceptions
            return None

    async def fetch_all_stocks_data(self, tickers: List[str]) -> tuple[dict, List[str]]:
        """
        Fetch data for all stocks with concurrency control
        Returns: (results_dict, failed_tickers)
        """
        self.failed_tickers = []  # Reset failed tickers list
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def fetch_with_semaphore(symbol):
            async with semaphore:
                return await self._fetch_stock_data_async(symbol)
        
        tasks = [fetch_with_semaphore(symbol) for symbol in tickers]
        results_list = await asyncio.gather(*tasks)
        
        results = {}
        for symbol, data in zip(tickers, results_list):
            if data is not None:
                results[symbol] = data

        return results, self.failed_tickers
