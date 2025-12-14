import asyncio
import aiohttp
import pandas as pd
import yfinance as yf
import json
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

# Configure logging for detailed failure tracking - set to DEBUG for maximum verbosity
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, max_concurrent_requests: int = 5, charts_dir: str = 'charts'):
        self.max_concurrent_requests = max_concurrent_requests
        self.charts_dir = charts_dir
        self.failed_tickers = []  # Add a list to track failed tickers
        self.failure_reasons = {}  # Track reason for each failure
        self.full_fetch_count = 0  # Track how many full 410d fetches
        self.incremental_fetch_count = 0  # Track how many incremental 3d fetches
        self.fallback_to_existing_count = 0  # Track how many used existing data as fallback
        logger.info(f"DataLoader initialized: max_concurrent={max_concurrent_requests}, charts_dir={charts_dir}")

    @staticmethod
    def read_tickers(file_path: str) -> List[str]:
        """Read tickers from a Python list in a text file."""
        logger.info(f"Reading tickers from {file_path}")
        with open(file_path, "r") as f:
            content = f.read().strip()
        if content.startswith("[") and content.endswith("]"):
            tickers = eval(content)  # Assuming trusted file
        else:
            tickers = content.splitlines()
        result = [t.strip().upper() for t in tickers if t.strip()]
        logger.info(f"Read {len(result)} tickers from {file_path}")
        return result

    def _load_existing_chart_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load existing chart data for a symbol from the charts directory."""
        filepath = os.path.join(self.charts_dir, f'{symbol}.json')
        if not os.path.exists(filepath):
            logger.debug(f"{symbol}: No existing chart file at {filepath}")
            return None
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Validate that we have the required fields
                if 'dates' in data and 'close' in data and len(data['dates']) > 0:
                    logger.debug(f"{symbol}: Loaded existing chart data with {len(data['dates'])} dates")
                    return data
                logger.warning(f"{symbol}: Existing chart file missing required fields (dates/close)")
                return None
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"{symbol}: Error loading existing chart file: {e}")
            return None

    def _merge_chart_data(self, existing_data: Dict[str, Any], new_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge new DataFrame data with existing chart data.
        - Override existing dates with new data
        - Add new dates to the dataset
        - Keep chronological order
        Returns a merged DataFrame.
        """
        logger.debug(f"_merge_chart_data called: new_df is None={new_df is None}, new_df.empty={new_df.empty if new_df is not None else 'N/A'}")
        
        if new_df is None or new_df.empty:
            # Convert existing data back to DataFrame
            logger.debug("new_df is empty/None, falling back to existing data")
            return self._existing_data_to_dataframe(existing_data)
        
        # Log new_df details
        logger.debug(f"new_df shape: {new_df.shape}, columns: {new_df.columns.tolist()}, index type: {type(new_df.index)}")
        logger.debug(f"new_df first few rows:\n{new_df.head(3)}")
        
        # Validate new_df has required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in new_df.columns for col in required_cols):
            logger.warning(f"Merge: new_df missing required columns. Has: {new_df.columns.tolist()}, Need: {required_cols}")
            # Fall back to existing data
            return self._existing_data_to_dataframe(existing_data)
        
        # Create DataFrame from existing data
        existing_df = self._existing_data_to_dataframe(existing_data)
        logger.debug(f"existing_df shape: {existing_df.shape}")
        
        if existing_df.empty:
            logger.debug("existing_df is empty, returning new_df only")
            return new_df
        
        # Get new dates as strings for comparison
        new_dates = set(idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx) 
                       for idx in new_df.index)
        logger.debug(f"new_dates to merge: {sorted(new_dates)}")
        
        # Filter out existing data for dates that are in new data (they will be overridden)
        existing_dates = [d for d in existing_data['dates'] if d not in new_dates]
        
        # Create a filtered existing DataFrame with only non-overlapping dates
        if existing_dates:
            existing_df_filtered = existing_df[~existing_df.index.strftime('%Y-%m-%d').isin(new_dates)]
        else:
            existing_df_filtered = pd.DataFrame()
        
        logger.debug(f"existing_df_filtered shape: {existing_df_filtered.shape}")
        
        # Concatenate and sort by date
        if not existing_df_filtered.empty:
            merged_df = pd.concat([existing_df_filtered, new_df])
        else:
            merged_df = new_df
        
        # Sort by index (date) to maintain chronological order
        merged_df = merged_df.sort_index()
        
        # Remove any duplicate indices, keeping the last (newest) value
        merged_df = merged_df[~merged_df.index.duplicated(keep='last')]
        
        logger.debug(f"merged_df final shape: {merged_df.shape}")
        return merged_df

    def _existing_data_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Convert existing chart data dict back to a DataFrame."""
        if not data or 'dates' not in data or len(data['dates']) == 0:
            logger.debug("_existing_data_to_dataframe: empty or invalid data")
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
            
            logger.debug(f"_existing_data_to_dataframe: converted {len(df)} rows")
            return df
        except Exception as e:
            logger.warning(f"_existing_data_to_dataframe: exception {e}")
            return pd.DataFrame()

    async def _fetch_stock_data_async(self, symbol: str, period: str = "410d") -> Optional[pd.DataFrame]:
        """Fetch single stock data asynchronously"""
        logger.info(f"{symbol}: Starting yfinance fetch (period={period})")
        try:
            # Use auto_adjust=True to get prices adjusted for splits AND dividends
            # This matches TradingView's SMA calculation methodology
            data = yf.download(symbol, period=period, interval="1d", auto_adjust=True, progress=False)
            
            logger.info(f"{symbol}: yfinance returned data.empty={data.empty}, shape={data.shape if not data.empty else 'N/A'}")
            
            if data.empty:
                logger.warning(f"{symbol}: yfinance returned EMPTY data for period={period}")
                return None

            # Log raw column info
            logger.info(f"{symbol}: Raw columns type={type(data.columns)}, columns={data.columns.tolist()}")
            
            # Handle multi-level column headers that yfinance sometimes returns
            # e.g., ('Open', 'AAPL') instead of 'Open'
            if isinstance(data.columns, pd.MultiIndex):
                logger.info(f"{symbol}: Detected MultiIndex columns, flattening...")
                # Flatten the multi-index by taking only the first level (price type)
                data.columns = data.columns.get_level_values(0)
                logger.info(f"{symbol}: After flattening, columns={data.columns.tolist()}")

            # With auto_adjust=True, prices are already adjusted for splits and dividends
            # No manual adjustment needed - this matches TradingView's methodology

            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                logger.error(f"{symbol}: MISSING columns after fetch: {missing_cols}. Available: {data.columns.tolist()}")
                return None

            result = data[required_cols]
            logger.info(f"{symbol}: Successfully fetched {len(result)} rows, date range: {result.index[0]} to {result.index[-1]}")
            return result
        except Exception as e:
            logger.error(f"{symbol}: EXCEPTION during fetch (period={period}): {type(e).__name__}: {str(e)}")
            return None

    async def _fetch_stock_data_with_merge(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch stock data with smart merging:
        - If no existing data: fetch full 410 days
        - If existing data exists: fetch only 3 days and merge
        """
        logger.info(f"{symbol}: _fetch_stock_data_with_merge started")
        existing_data = self._load_existing_chart_data(symbol)
        
        if existing_data is None:
            # No existing data - fetch full 410 days
            logger.info(f"{symbol}: No existing chart data, will do FULL 410d fetch")
            self.full_fetch_count += 1
            data = await self._fetch_stock_data_async(symbol, period="410d")
            if data is None or data.empty:
                self.failed_tickers.append(symbol)
                self.failure_reasons[symbol] = "No existing data and full 410d fetch failed"
                logger.error(f"{symbol}: FAILED - No existing chart file and 410d fetch returned empty/None")
                return None
            logger.info(f"{symbol}: SUCCESS - Full 410d fetch returned {len(data)} rows")
            return data
        else:
            # Existing data found - fetch only last 3 days and merge
            logger.info(f"{symbol}: Found existing data ({len(existing_data.get('dates', []))} dates), will do INCREMENTAL 3d fetch")
            self.incremental_fetch_count += 1
            new_data = await self._fetch_stock_data_async(symbol, period="3d")
            
            logger.info(f"{symbol}: 3d fetch result: new_data is None={new_data is None}, empty={new_data.empty if new_data is not None else 'N/A'}")
            
            if new_data is None or new_data.empty:
                # If 3-day fetch failed (e.g., weekend/holiday), use existing data as fallback
                logger.info(f"{symbol}: 3d fetch empty/None, attempting fallback to existing data")
                existing_df = self._existing_data_to_dataframe(existing_data)
                if existing_df.empty:
                    self.failed_tickers.append(symbol)
                    self.failure_reasons[symbol] = "3d fetch failed and existing data conversion failed"
                    logger.error(f"{symbol}: FAILED - 3d fetch empty AND existing data conversion failed")
                    return None
                # Successfully using existing data as fallback
                self.fallback_to_existing_count += 1
                logger.info(f"{symbol}: SUCCESS (FALLBACK) - Using existing data ({len(existing_df)} rows) since 3d fetch was empty")
                return existing_df
            
            # Merge new data with existing data
            logger.info(f"{symbol}: Merging {len(new_data)} new rows with existing data...")
            merged_df = self._merge_chart_data(existing_data, new_data)
            
            if merged_df is None or merged_df.empty:
                logger.error(f"{symbol}: FAILED - Merge returned empty/None DataFrame")
                self.failed_tickers.append(symbol)
                self.failure_reasons[symbol] = "Merge returned empty DataFrame"
                return None
                
            logger.info(f"{symbol}: SUCCESS - Merged result has {len(merged_df)} rows")
            return merged_df

    async def fetch_all_stocks_data(self, tickers: List[str]) -> tuple[dict, List[str]]:
        """
        Fetch data for all stocks with concurrency control and smart merging.
        Returns: (results_dict, failed_tickers)
        """
        logger.info(f"fetch_all_stocks_data: Starting fetch for {len(tickers)} tickers")
        self.failed_tickers = []  # Reset failed tickers list
        self.failure_reasons = {}  # Reset failure reasons
        self.full_fetch_count = 0
        self.incremental_fetch_count = 0
        self.fallback_to_existing_count = 0
        
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def fetch_with_semaphore(symbol):
            async with semaphore:
                return await self._fetch_stock_data_with_merge(symbol)
        
        tasks = [fetch_with_semaphore(symbol) for symbol in tickers]
        logger.info(f"fetch_all_stocks_data: Created {len(tasks)} fetch tasks, awaiting...")
        results_list = await asyncio.gather(*tasks)
        logger.info(f"fetch_all_stocks_data: All tasks completed")
        
        results = {}
        success_count = 0
        none_count = 0
        for symbol, data in zip(tickers, results_list):
            if data is not None:
                results[symbol] = data
                success_count += 1
            else:
                none_count += 1
        
        logger.info(f"fetch_all_stocks_data: Results - {success_count} success, {none_count} returned None")

        # Print fetch statistics
        print(f"📊 Fetch statistics: {self.full_fetch_count} full (410d), {self.incremental_fetch_count} incremental (3d)")
        logger.info(f"Fetch statistics: {self.full_fetch_count} full (410d), {self.incremental_fetch_count} incremental (3d)")
        if self.fallback_to_existing_count > 0:
            print(f"📊 Fallback to existing data: {self.fallback_to_existing_count} stocks (3d fetch empty, used cached data)")
            logger.info(f"Fallback to existing data: {self.fallback_to_existing_count} stocks")
        
        # Log failure reasons summary
        if self.failed_tickers:
            print(f"⚠️ Failed tickers ({len(self.failed_tickers)}):")
            logger.warning(f"Failed tickers ({len(self.failed_tickers)}): {self.failed_tickers[:20]}...")
            # Group by reason
            reason_counts = {}
            for ticker in self.failed_tickers:
                reason = self.failure_reasons.get(ticker, "Unknown reason")
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            for reason, count in reason_counts.items():
                print(f"   - {reason}: {count} tickers")
                logger.warning(f"   - {reason}: {count} tickers")
        
        return results, self.failed_tickers
    
    async def fetch_all_stocks_data_full(self, tickers: List[str]) -> tuple[dict, List[str]]:
        """
        Fetch full 410 days data for all stocks (no merging).
        Use this when you want to force a full refresh.
        Returns: (results_dict, failed_tickers)
        """
        self.failed_tickers = []  # Reset failed tickers list
        self.failure_reasons = {}  # Reset failure reasons
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def fetch_with_semaphore(symbol):
            async with semaphore:
                data = await self._fetch_stock_data_async(symbol, period="410d")
                if data is None or data.empty:
                    self.failed_tickers.append(symbol)
                    self.failure_reasons[symbol] = "Full 410d fetch returned empty"
                    logger.warning(f"{symbol}: FAILED - Full 410d fetch returned empty")
                    return None
                return data
        
        tasks = [fetch_with_semaphore(symbol) for symbol in tickers]
        results_list = await asyncio.gather(*tasks)
        
        results = {}
        for symbol, data in zip(tickers, results_list):
            if data is not None:
                results[symbol] = data

        return results, self.failed_tickers
