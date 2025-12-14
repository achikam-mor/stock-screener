import pandas as pd
import numpy as np
from typing import Tuple

class StockAnalyzer:
    @staticmethod
    def calculate_sma(data: pd.DataFrame, window: int = 150) -> pd.Series:
        """Calculate SMA based on closing prices."""
        close_col = data["Close"]
        # Handle both flat and MultiIndex columns
        if hasattr(close_col, 'iloc') and len(close_col.shape) > 1 and close_col.shape[1] > 0:
            close_col = close_col.iloc[:, 0]
        return close_col.rolling(window=window).mean()

    @staticmethod
    def calculate_atr(data: pd.DataFrame, window: int = 14) -> Tuple[float, float]:
        """Calculate ATR using High-Low range for the given window."""
        first_values = data.head(window)
        
        # Handle both flat and MultiIndex columns
        highs = first_values["High"]
        lows = first_values["Low"]
        closes = first_values["Close"]
        
        if hasattr(highs, 'iloc') and len(highs.shape) > 1 and highs.shape[1] > 0:
            highs = highs.iloc[:, 0]
        if hasattr(lows, 'iloc') and len(lows.shape) > 1 and lows.shape[1] > 0:
            lows = lows.iloc[:, 0]
        if hasattr(closes, 'iloc') and len(closes.shape) > 1 and closes.shape[1] > 0:
            closes = closes.iloc[:, 0]
            
        highs = highs.values
        lows = lows.values
        average_close = closes.values.mean()
        
        differences = np.abs(highs - lows)
        average_atr = float(differences.mean())
        return average_atr, average_atr/average_close * 100

    @staticmethod
    def validate_min_data(data: pd.DataFrame, window: int = 150) -> bool:
        """Check if there are at least `window` non-NaN closing prices."""
        close_col = data["Close"]
        # Handle both flat and MultiIndex columns
        if hasattr(close_col, 'iloc') and len(close_col.shape) > 1 and close_col.shape[1] > 0:
            close_col = close_col.iloc[:, 0]
        return close_col.dropna().shape[0] >= window

    @staticmethod
    def check_sma_conditions(data: pd.DataFrame, tolerance: float = 0.04) -> Tuple[bool, float, float]:
        """Check if stock meets SMA conditions."""
        sma = data["SMA150"]
        close_col = data["Close"]
        
        # Handle both flat and MultiIndex columns
        if hasattr(close_col, 'iloc') and len(close_col.shape) > 1 and close_col.shape[1] > 0:
            close_col = close_col.iloc[:, 0]
        
        last_close = float(close_col.iloc[0])
        last_sma = float(sma.iloc[0])

        # Condition 1: last close within ±tolerance% of SMA
        lower_bound = last_sma * (1 - tolerance)
        upper_bound = last_sma * (1 + tolerance)
        condition1 = lower_bound <= last_close <= upper_bound

        # Condition 2: SMA trending or flat (average slope over last 14 days)
        recent_sma = sma.iloc[:14]
        slope = -recent_sma.diff().mean()
        condition2 = slope >= 0

        return condition1 and condition2, last_close, last_sma

    @staticmethod
    def calculate_volume_metrics(data: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate volume metrics: last day volume and average of previous 14 days.
        Uses 15 days total (1 last + 14 previous).
        """
        volume_col = data["Volume"].iloc[:15]  # Get last 15 days
        
        # Handle both flat and MultiIndex columns
        if hasattr(volume_col, 'iloc') and len(volume_col.shape) > 1 and volume_col.shape[1] > 0:
            volume_col = volume_col.iloc[:, 0]
        
        last_volume = float(volume_col.iloc[0])  # Most recent day
        avg_volume_14d = float(volume_col.iloc[1:15].mean())  # Previous 14 days average
        return last_volume, avg_volume_14d
