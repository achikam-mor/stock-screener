from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import logging
from models import StockData, ScreenerResults
from stock_analyzer import StockAnalyzer

logger = logging.getLogger(__name__)

class StockScreener:
    def __init__(self, analyzer: StockAnalyzer, charts_dir: str = 'charts'):
        self.analyzer = analyzer
        self.charts_dir = charts_dir
        self.failure_reasons = {}  # Track why each stock failed screening

    def _get_cross_data_from_chart(self, symbol: str) -> Tuple[bool, bool]:
        """Load golden/death cross data from chart file."""
        import os
        import json
        
        filepath = os.path.join(self.charts_dir, f'{symbol}.json')
        if not os.path.exists(filepath):
            return False, False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('golden_cross', False), data.get('death_cross', False)
        except (json.JSONDecodeError, Exception):
            return False, False

    def screen_stocks(self, stock_data: Dict[str, pd.DataFrame]) -> ScreenerResults:
        hot_stocks: Dict[str, StockData] = {}
        watch_list: Dict[str, StockData] = {}
        failed_tickers: List[str] = []
        filtered_by_sma: List[str] = []
        self.failure_reasons = {}  # Reset failure reasons

        logger.info(f"screen_stocks: Starting screening of {len(stock_data)} stocks")
        
        # Log sample stock data for debugging
        sample_symbols = list(stock_data.keys())[:3]
        for sym in sample_symbols:
            df = stock_data[sym]
            logger.info(f"SAMPLE {sym}: shape={df.shape}, columns={df.columns.tolist()}, index_type={type(df.index)}")
            logger.debug(f"SAMPLE {sym}: first 3 rows:\n{df.head(3)}")

        for symbol, data in stock_data.items():
            try:
                if not self.analyzer.validate_min_data(data, 150):
                    failed_tickers.append(symbol)
                    reason = f"Insufficient data: only {len(data)} rows, need 150"
                    self.failure_reasons[symbol] = reason
                    logger.debug(f"{symbol}: {reason}")
                    continue

                # Calculate SMA and prepare data
                data["SMA150"] = self.analyzer.calculate_sma(data, 150)
                updated_data = data.iloc[::-1].copy()
                
                logger.debug(f"{symbol}: Data prepared, shape={updated_data.shape}, has SMA150={('SMA150' in updated_data.columns)}")

                # Check conditions
                condition_met, last_close, last_sma = self.analyzer.check_sma_conditions(updated_data)
                logger.debug(f"{symbol}: condition_met={condition_met}, last_close={last_close}, last_sma={last_sma}")

                if condition_met:
                    # Calculate ATR
                    atr, atr_pct = self.analyzer.calculate_atr(updated_data, 14)
                    
                    # Calculate volume metrics
                    last_volume, avg_volume_14d = self.analyzer.calculate_volume_metrics(updated_data)
                    
                    # Get golden/death cross from chart data
                    golden_cross, death_cross = self._get_cross_data_from_chart(symbol)
                    
                    stock_entry = StockData(
                        symbol=symbol,
                        last_close=last_close,
                        sma150=last_sma,
                        atr=atr,
                        atr_percent=atr_pct,
                        last_volume=last_volume,
                        avg_volume_14d=avg_volume_14d,
                        golden_cross=golden_cross,
                        death_cross=death_cross
                    )

                    if last_close > last_sma:
                        hot_stocks[symbol] = stock_entry
                    else:
                        watch_list[symbol] = stock_entry
                else:
                    # Stock has data but doesn't meet SMA conditions
                    filtered_by_sma.append(symbol)

            except Exception as e:
                failed_tickers.append(symbol)
                reason = f"Exception during screening: {str(e)}"
                self.failure_reasons[symbol] = reason
                logger.warning(f"{symbol}: {reason}")

        # Log summary of screening failures
        if failed_tickers:
            logger.info(f"Screening completed: {len(failed_tickers)} tickers failed screening")
            # Group by reason type
            reason_counts = {}
            for ticker in failed_tickers:
                reason = self.failure_reasons.get(ticker, "Unknown")
                # Simplify reason for grouping
                if "Insufficient data" in reason:
                    key = "Insufficient data (< 150 rows)"
                elif "Exception" in reason:
                    key = "Exception during screening"
                else:
                    key = reason
                reason_counts[key] = reason_counts.get(key, 0) + 1
            for reason, count in reason_counts.items():
                logger.info(f"   - {reason}: {count} tickers")

        return ScreenerResults(hot_stocks, watch_list, failed_tickers, filtered_by_sma)
