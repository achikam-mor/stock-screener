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

    @staticmethod
    def find_key_levels(data: pd.DataFrame, window: int = 5, tolerance: float = 0.02, max_crossings: int = 20, min_touches: int = 2) -> list:
        """
        Find key price levels (support/resistance) using local extrema and clustering.
        Filters out levels that are crossed too frequently (noise) or not tested enough.
        Also filters out levels that are too far (>20%) from the current price.
        """
        # Handle MultiIndex columns if necessary
        highs = data["High"]
        lows = data["Low"]
        closes = data["Close"]
        
        if hasattr(highs, 'iloc') and len(highs.shape) > 1 and highs.shape[1] > 0:
            highs = highs.iloc[:, 0]
        if hasattr(lows, 'iloc') and len(lows.shape) > 1 and lows.shape[1] > 0:
            lows = lows.iloc[:, 0]
        if hasattr(closes, 'iloc') and len(closes.shape) > 1 and closes.shape[1] > 0:
            closes = closes.iloc[:, 0]
            
        # Get current price (last close)
        if len(closes) == 0:
            return []
        current_price = float(closes.iloc[-1])
            
        # Find local maxima (Resistance candidates)
        rolling_max = highs.rolling(window=window*2+1, center=True).max()
        resistances = highs[highs == rolling_max].dropna()
        
        # Find local minima (Support candidates)
        rolling_min = lows.rolling(window=window*2+1, center=True).min()
        supports = lows[lows == rolling_min].dropna()
        
        # Combine all candidates
        all_levels = pd.concat([resistances, supports])
        
        # Cluster levels
        if len(all_levels) == 0:
            return []
            
        levels_sorted = sorted(all_levels.values)
        clusters = []
        current_cluster = [levels_sorted[0]]
        
        for i in range(1, len(levels_sorted)):
            if levels_sorted[i] <= current_cluster[-1] * (1 + tolerance):
                current_cluster.append(levels_sorted[i])
            else:
                clusters.append(float(np.mean(current_cluster)))
                current_cluster = [levels_sorted[i]]
        clusters.append(float(np.mean(current_cluster)))
        
        # Filter levels
        valid_levels = []
        for level in clusters:
            # 0. Distance Filter: Ignore levels > 20% away from current price
            if abs(level - current_price) / current_price > 0.20:
                continue

            # 1. Noise Filter: Count crossings (Low < Level < High)
            crossings = ((lows < level) & (highs > level)).sum()
            
            # 2. Strength Filter: Count touches (High or Low within tolerance of Level)
            # A touch is when the price action came close to the level
            # We check if the High reached the level (from below) or Low reached it (from above)
            upper_zone = level * (1 + tolerance/2)
            lower_zone = level * (1 - tolerance/2)
            
            touches = ((highs >= lower_zone) & (lows <= upper_zone)).sum()
            
            # Relaxed condition: If it's a very strong level (many touches), allow slightly more noise
            # Or if it's very clean (few crossings), allow fewer touches
            if (crossings <= max_crossings and touches >= min_touches) or (touches >= 5 and crossings <= max_crossings * 1.5):
                valid_levels.append(round(level, 2))
                
        return valid_levels
