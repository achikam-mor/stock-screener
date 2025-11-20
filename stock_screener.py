from typing import Dict, List, Tuple
import pandas as pd
from models import StockData, ScreenerResults
from stock_analyzer import StockAnalyzer

class StockScreener:
    def __init__(self, analyzer: StockAnalyzer):
        self.analyzer = analyzer

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
                    
                    stock_data = StockData(
                        symbol=symbol,
                        last_close=last_close,
                        sma150=last_sma,
                        atr=atr,
                        atr_percent=atr_pct,
                        last_volume=last_volume,
                        avg_volume_14d=avg_volume_14d
                    )

                    if last_close > last_sma:
                        hot_stocks[symbol] = stock_data
                    else:
                        watch_list[symbol] = stock_data
                else:
                    # Stock has data but doesn't meet SMA conditions
                    filtered_by_sma.append(symbol)

            except Exception as e:
                failed_tickers.append(symbol)

        return ScreenerResults(hot_stocks, watch_list, failed_tickers, filtered_by_sma)
