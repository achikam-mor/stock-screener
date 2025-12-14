from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from models import StockData, ScreenerResults
from stock_analyzer import StockAnalyzer

class StockScreener:
    def __init__(self, analyzer: StockAnalyzer, charts_dir: str = 'charts'):
        self.analyzer = analyzer
        self.charts_dir = charts_dir

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

        for symbol, data in stock_data.items():
            try:
                if not self.analyzer.validate_min_data(data, 150):
                    failed_tickers.append(symbol)
                    continue

                # Calculate SMA and prepare data
                data["SMA150"] = self.analyzer.calculate_sma(data, 150)
                updated_data = data.iloc[::-1].copy()

                # Check conditions
                condition_met, last_close, last_sma = self.analyzer.check_sma_conditions(updated_data)

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

        return ScreenerResults(hot_stocks, watch_list, failed_tickers, filtered_by_sma)
