from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class StockData:
    symbol: str
    last_close: float
    sma150: float
    atr: float
    atr_percent: float
    last_volume: float
    avg_volume_14d: float
    golden_cross: bool = False  # 50 SMA crossed above 200 SMA recently
    death_cross: bool = False   # 50 SMA crossed below 200 SMA recently

@dataclass
class ScreenerResults:
    hot_stocks: Dict[str, StockData]
    watch_list: Dict[str, StockData]
    failed_tickers: list[str]
    filtered_by_sma: list[str]
