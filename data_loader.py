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
            data = yf.download(symbol, period="500d", interval="1d", auto_adjust=False, progress=False)
            if data.empty:
                self.failed_tickers.append(symbol)  # Track symbols with empty data
                return None

            if "Stock Splits" in data.columns:
                splits = data["Stock Splits"].replace(0, 1).cumprod()
                for col in ["Open", "High", "Low", "Close"]:
                    data[col] = data[col] / splits

            return data[["Open", "High", "Low", "Close"]]
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
        async with semaphore:
            tasks = []
            for symbol in tickers:
                task = asyncio.create_task(self._fetch_stock_data_async(symbol))
                tasks.append((symbol, task))

            results = {}
            for symbol, task in tasks:
                data = await task
                if data is not None:
                    results[symbol] = data

            return results, self.failed_tickers
