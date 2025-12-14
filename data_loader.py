import asyncio
import aiohttp
import pandas as pd
import yfinance as yf
import json
import os
from typing import List, Optional, Dict, Any

class DataLoader:
    def __init__(self, max_concurrent_requests: int = 5, charts_dir: str = 'charts'):
        self.max_concurrent_requests = max_concurrent_requests
        self.charts_dir = charts_dir
        self.failed_tickers = []  # Add a list to track failed tickers
        self.full_fetch_count = 0  # Track how many full 410d fetches
        self.incremental_fetch_count = 0  # Track how many incremental 3d fetches

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

    def _load_existing_chart_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load existing chart data for a symbol from the charts directory."""
        filepath = os.path.join(self.charts_dir, f'{symbol}.json')
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Validate that we have the required fields
                if 'dates' in data and 'close' in data and len(data['dates']) > 0:
                    return data
                return None
        except (json.JSONDecodeError, Exception):
            return None

    def _merge_chart_data(self, existing_data: Dict[str, Any], new_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge new DataFrame data with existing chart data.
        - Override existing dates with new data
        - Add new dates to the dataset
        - Keep chronological order
        Returns a merged DataFrame.
        """
        if new_df.empty:
            # Convert existing data back to DataFrame
            return self._existing_data_to_dataframe(existing_data)
        
        # Create DataFrame from existing data
        existing_df = self._existing_data_to_dataframe(existing_data)
        
        if existing_df.empty:
            return new_df
        
        # Get new dates as strings for comparison
        new_dates = set(idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx) 
                       for idx in new_df.index)
        
        # Filter out existing data for dates that are in new data (they will be overridden)
        existing_dates = [d for d in existing_data['dates'] if d not in new_dates]
        
        # Create a filtered existing DataFrame with only non-overlapping dates
        if existing_dates:
            existing_df_filtered = existing_df[~existing_df.index.strftime('%Y-%m-%d').isin(new_dates)]
        else:
            existing_df_filtered = pd.DataFrame()
        
        # Concatenate and sort by date
        if not existing_df_filtered.empty:
            merged_df = pd.concat([existing_df_filtered, new_df])
        else:
            merged_df = new_df
        
        # Sort by index (date) to maintain chronological order
        merged_df = merged_df.sort_index()
        
        # Remove any duplicate indices, keeping the last (newest) value
        merged_df = merged_df[~merged_df.index.duplicated(keep='last')]
        
        return merged_df

    def _existing_data_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Convert existing chart data dict back to a DataFrame."""
        if not data or 'dates' not in data or len(data['dates']) == 0:
            return pd.DataFrame()
        
        try:
            # Create DataFrame from existing data
            df = pd.DataFrame({
                'Open': data.get('open', []),
                'High': data.get('high', []),
                'Low': data.get('low', []),
                'Close': data.get('close', []),
                'Volume': data.get('volume', [])
            })
            
            # Set dates as index
            df.index = pd.to_datetime(data['dates'])
            df.index.name = 'Date'
            
            return df
        except Exception:
            return pd.DataFrame()

    async def _fetch_stock_data_async(self, symbol: str, period: str = "410d") -> Optional[pd.DataFrame]:
        """Fetch single stock data asynchronously"""
        try:
            # Use auto_adjust=True to get prices adjusted for splits AND dividends
            # This matches TradingView's SMA calculation methodology
            data = yf.download(symbol, period=period, interval="1d", auto_adjust=True, progress=False)
            if data.empty:
                return None

            # With auto_adjust=True, prices are already adjusted for splits and dividends
            # No manual adjustment needed - this matches TradingView's methodology

            return data[["Open", "High", "Low", "Close", "Volume"]]
        except Exception:
            return None

    async def _fetch_stock_data_with_merge(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch stock data with smart merging:
        - If no existing data: fetch full 410 days
        - If existing data exists: fetch only 3 days and merge
        """
        existing_data = self._load_existing_chart_data(symbol)
        
        if existing_data is None:
            # No existing data - fetch full 410 days
            self.full_fetch_count += 1
            data = await self._fetch_stock_data_async(symbol, period="410d")
            if data is None or data.empty:
                self.failed_tickers.append(symbol)
                return None
            return data
        else:
            # Existing data found - fetch only last 3 days and merge
            self.incremental_fetch_count += 1
            new_data = await self._fetch_stock_data_async(symbol, period="3d")
            
            if new_data is None or new_data.empty:
                # If fetch failed, return existing data as DataFrame
                existing_df = self._existing_data_to_dataframe(existing_data)
                if existing_df.empty:
                    self.failed_tickers.append(symbol)
                    return None
                return existing_df
            
            # Merge new data with existing data
            merged_df = self._merge_chart_data(existing_data, new_data)
            return merged_df

    async def fetch_all_stocks_data(self, tickers: List[str]) -> tuple[dict, List[str]]:
        """
        Fetch data for all stocks with concurrency control and smart merging.
        Returns: (results_dict, failed_tickers)
        """
        self.failed_tickers = []  # Reset failed tickers list
        self.full_fetch_count = 0
        self.incremental_fetch_count = 0
        
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def fetch_with_semaphore(symbol):
            async with semaphore:
                return await self._fetch_stock_data_with_merge(symbol)
        
        tasks = [fetch_with_semaphore(symbol) for symbol in tickers]
        results_list = await asyncio.gather(*tasks)
        
        results = {}
        for symbol, data in zip(tickers, results_list):
            if data is not None:
                results[symbol] = data

        # Print fetch statistics
        print(f"📊 Fetch statistics: {self.full_fetch_count} full (410d), {self.incremental_fetch_count} incremental (3d)")
        
        return results, self.failed_tickers
    
    async def fetch_all_stocks_data_full(self, tickers: List[str]) -> tuple[dict, List[str]]:
        """
        Fetch full 410 days data for all stocks (no merging).
        Use this when you want to force a full refresh.
        Returns: (results_dict, failed_tickers)
        """
        self.failed_tickers = []  # Reset failed tickers list
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def fetch_with_semaphore(symbol):
            async with semaphore:
                data = await self._fetch_stock_data_async(symbol, period="410d")
                if data is None or data.empty:
                    self.failed_tickers.append(symbol)
                    return None
                return data
        
        tasks = [fetch_with_semaphore(symbol) for symbol in tickers]
        results_list = await asyncio.gather(*tasks)
        
        results = {}
        for symbol, data in zip(tickers, results_list):
            if data is not None:
                results[symbol] = data

        return results, self.failed_tickers
