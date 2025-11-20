from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class StockData:
    symbol: str
    last_close: float
    sma150: float
    atr: float
    atr_percent: float
    last_volume: float
    avg_volume_14d: float
    above_sma: bool

@dataclass
class ScreenerResults:
    hot_stocks: Dict[str, StockData]
    watch_list: Dict[str, StockData]
    failed_tickers: list[str]
