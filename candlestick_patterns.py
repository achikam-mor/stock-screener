"""
Candlestick Pattern Detection Module

Detects 7 high-reliability candlestick patterns with confirmation:
- Hammer (Bullish Reversal)
- Shooting Star (Bearish Reversal)
- Bullish Engulfing (Bullish Reversal)
- Bearish Engulfing (Bearish Reversal)
- Morning Star (Bullish Reversal)
- Evening Star (Bearish Reversal)
- Three White Soldiers (Bullish Continuation)
- Three Black Crows (Bearish Continuation)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional


def calculate_body_size(open_price: float, close_price: float) -> float:
    """Calculate the body size of a candle."""
    return abs(close_price - open_price)


def calculate_upper_shadow(high: float, open_price: float, close_price: float) -> float:
    """Calculate the upper shadow length."""
    return high - max(open_price, close_price)


def calculate_lower_shadow(low: float, open_price: float, close_price: float) -> float:
    """Calculate the lower shadow length."""
    return min(open_price, close_price) - low


def is_bullish_candle(open_price: float, close_price: float) -> bool:
    """Check if candle is bullish (close > open)."""
    return close_price > open_price


def is_bearish_candle(open_price: float, close_price: float) -> bool:
    """Check if candle is bearish (close < open)."""
    return close_price < open_price


def detect_hammer(idx: int, opens: List[float], highs: List[float], 
                  lows: List[float], closes: List[float], atr: float) -> Optional[Dict]:
    """
    Detect Hammer pattern (Bullish Reversal).
    
    Criteria:
    - Lower shadow >= 2x body length
    - Upper shadow <= 10% of body (minimal)
    - Body in upper 30% of total range
    - Body size significant (> 30% of ATR)
    """
    if idx >= len(opens):
        return None
    
    open_p = opens[idx]
    high = highs[idx]
    low = lows[idx]
    close = closes[idx]
    
    body = calculate_body_size(open_p, close)
    lower_shadow = calculate_lower_shadow(low, open_p, close)
    upper_shadow = calculate_upper_shadow(high, open_p, close)
    total_range = high - low
    
    if total_range == 0 or atr is None or atr == 0:
        return None
    
    # Hammer criteria
    if (lower_shadow >= 2 * body and 
        upper_shadow <= 0.1 * body and
        body >= 0.3 * atr and
        (max(open_p, close) - low) / total_range >= 0.7):  # Body in upper 30%
        
        # Calculate confidence based on shadow ratio and volume
        confidence = min(95, 60 + (lower_shadow / body) * 10)
        
        return {
            "pattern": "hammer",
            "signal": "bullish",
            "confidence": round(confidence, 0)
        }
    
    return None


def detect_shooting_star(idx: int, opens: List[float], highs: List[float], 
                         lows: List[float], closes: List[float], atr: float) -> Optional[Dict]:
    """
    Detect Shooting Star pattern (Bearish Reversal).
    
    Criteria:
    - Upper shadow >= 2x body length
    - Lower shadow <= 10% of body (minimal)
    - Body in lower 30% of total range
    - Body size significant (> 30% of ATR)
    """
    if idx >= len(opens):
        return None
    
    open_p = opens[idx]
    high = highs[idx]
    low = lows[idx]
    close = closes[idx]
    
    body = calculate_body_size(open_p, close)
    lower_shadow = calculate_lower_shadow(low, open_p, close)
    upper_shadow = calculate_upper_shadow(high, open_p, close)
    total_range = high - low
    
    if total_range == 0 or atr is None or atr == 0:
        return None
    
    # Shooting Star criteria
    if (upper_shadow >= 2 * body and 
        lower_shadow <= 0.1 * body and
        body >= 0.3 * atr and
        (high - min(open_p, close)) / total_range >= 0.7):  # Body in lower 30%
        
        confidence = min(95, 60 + (upper_shadow / body) * 10)
        
        return {
            "pattern": "shooting_star",
            "signal": "bearish",
            "confidence": round(confidence, 0)
        }
    
    return None


def detect_bullish_engulfing(idx: int, opens: List[float], highs: List[float], 
                             lows: List[float], closes: List[float], 
                             volumes: List[int], atr: float) -> Optional[Dict]:
    """
    Detect Bullish Engulfing pattern (Bullish Reversal).
    
    Criteria:
    - Day 1: Bearish candle
    - Day 2: Bullish candle that completely engulfs Day 1
    - Day 2 opens below Day 1 close
    - Day 2 closes above Day 1 open
    """
    if idx < 1 or idx >= len(opens):
        return None
    
    # Day 1 (previous)
    open1 = opens[idx - 1]
    close1 = closes[idx - 1]
    
    # Day 2 (current)
    open2 = opens[idx]
    close2 = closes[idx]
    
    # Check pattern criteria
    if (is_bearish_candle(open1, close1) and  # Day 1 bearish
        is_bullish_candle(open2, close2) and  # Day 2 bullish
        open2 < close1 and  # Opens below previous close
        close2 > open1):  # Closes above previous open
        
        # Volume confirmation boost
        volume_boost = 0
        if idx < len(volumes) and idx - 1 < len(volumes):
            if volumes[idx] > volumes[idx - 1]:
                volume_boost = 10
        
        confidence = min(95, 70 + volume_boost)
        
        return {
            "pattern": "bullish_engulfing",
            "signal": "bullish",
            "confidence": round(confidence, 0)
        }
    
    return None


def detect_bearish_engulfing(idx: int, opens: List[float], highs: List[float], 
                             lows: List[float], closes: List[float], 
                             volumes: List[int], atr: float) -> Optional[Dict]:
    """
    Detect Bearish Engulfing pattern (Bearish Reversal).
    
    Criteria:
    - Day 1: Bullish candle
    - Day 2: Bearish candle that completely engulfs Day 1
    - Day 2 opens above Day 1 close
    - Day 2 closes below Day 1 open
    """
    if idx < 1 or idx >= len(opens):
        return None
    
    # Day 1 (previous)
    open1 = opens[idx - 1]
    close1 = closes[idx - 1]
    
    # Day 2 (current)
    open2 = opens[idx]
    close2 = closes[idx]
    
    # Check pattern criteria
    if (is_bullish_candle(open1, close1) and  # Day 1 bullish
        is_bearish_candle(open2, close2) and  # Day 2 bearish
        open2 > close1 and  # Opens above previous close
        close2 < open1):  # Closes below previous open
        
        # Volume confirmation boost
        volume_boost = 0
        if idx < len(volumes) and idx - 1 < len(volumes):
            if volumes[idx] > volumes[idx - 1]:
                volume_boost = 10
        
        confidence = min(95, 70 + volume_boost)
        
        return {
            "pattern": "bearish_engulfing",
            "signal": "bearish",
            "confidence": round(confidence, 0)
        }
    
    return None


def detect_morning_star(idx: int, opens: List[float], highs: List[float], 
                       lows: List[float], closes: List[float], atr: float) -> Optional[Dict]:
    """
    Detect Morning Star pattern (Bullish Reversal).
    
    Criteria:
    - Day 1: Long bearish candle
    - Day 2: Small body (indecision), gaps down
    - Day 3: Long bullish candle, closes above Day 1 midpoint
    """
    if idx < 2 or idx >= len(opens):
        return None
    
    # Day 1
    open1 = opens[idx - 2]
    close1 = closes[idx - 2]
    body1 = calculate_body_size(open1, close1)
    
    # Day 2
    open2 = opens[idx - 1]
    close2 = closes[idx - 1]
    body2 = calculate_body_size(open2, close2)
    
    # Day 3
    open3 = opens[idx]
    close3 = closes[idx]
    body3 = calculate_body_size(open3, close3)
    
    if atr is None or atr == 0:
        return None
    
    # Pattern criteria
    if (is_bearish_candle(open1, close1) and  # Day 1 bearish
        body1 > 0.7 * atr and  # Day 1 long
        body2 < 0.3 * body1 and  # Day 2 small
        max(open2, close2) < close1 and  # Day 2 gaps down
        is_bullish_candle(open3, close3) and  # Day 3 bullish
        body3 > 0.7 * atr and  # Day 3 long
        close3 > (open1 + close1) / 2):  # Closes above Day 1 midpoint
        
        confidence = 75
        
        return {
            "pattern": "morning_star",
            "signal": "bullish",
            "confidence": round(confidence, 0)
        }
    
    return None


def detect_evening_star(idx: int, opens: List[float], highs: List[float], 
                       lows: List[float], closes: List[float], atr: float) -> Optional[Dict]:
    """
    Detect Evening Star pattern (Bearish Reversal).
    
    Criteria:
    - Day 1: Long bullish candle
    - Day 2: Small body (indecision), gaps up
    - Day 3: Long bearish candle, closes below Day 1 midpoint
    """
    if idx < 2 or idx >= len(opens):
        return None
    
    # Day 1
    open1 = opens[idx - 2]
    close1 = closes[idx - 2]
    body1 = calculate_body_size(open1, close1)
    
    # Day 2
    open2 = opens[idx - 1]
    close2 = closes[idx - 1]
    body2 = calculate_body_size(open2, close2)
    
    # Day 3
    open3 = opens[idx]
    close3 = closes[idx]
    body3 = calculate_body_size(open3, close3)
    
    if atr is None or atr == 0:
        return None
    
    # Pattern criteria
    if (is_bullish_candle(open1, close1) and  # Day 1 bullish
        body1 > 0.7 * atr and  # Day 1 long
        body2 < 0.3 * body1 and  # Day 2 small
        min(open2, close2) > close1 and  # Day 2 gaps up
        is_bearish_candle(open3, close3) and  # Day 3 bearish
        body3 > 0.7 * atr and  # Day 3 long
        close3 < (open1 + close1) / 2):  # Closes below Day 1 midpoint
        
        confidence = 75
        
        return {
            "pattern": "evening_star",
            "signal": "bearish",
            "confidence": round(confidence, 0)
        }
    
    return None


def detect_three_white_soldiers(idx: int, opens: List[float], highs: List[float], 
                                lows: List[float], closes: List[float], atr: float) -> Optional[Dict]:
    """
    Detect Three White Soldiers pattern (Bullish Continuation).
    
    Criteria:
    - Three consecutive bullish candles
    - Each opens within previous body
    - Each closes near highs (< 20% shadow)
    - Progressive highs
    """
    if idx < 2 or idx >= len(opens):
        return None
    
    bodies = []
    for i in range(idx - 2, idx + 1):
        open_p = opens[i]
        close = closes[i]
        high = highs[i]
        
        # Must be bullish
        if not is_bullish_candle(open_p, close):
            return None
        
        # Must close near highs
        upper_shadow = calculate_upper_shadow(high, open_p, close)
        total_range = high - lows[i]
        if total_range > 0 and upper_shadow / total_range > 0.2:
            return None
        
        bodies.append(calculate_body_size(open_p, close))
    
    # Check opens within previous body
    for i in range(1, 3):
        prev_idx = idx - 3 + i
        curr_idx = idx - 3 + i + 1
        if opens[curr_idx] <= opens[prev_idx] or opens[curr_idx] >= closes[prev_idx]:
            return None
    
    # Check progressive highs
    if not (highs[idx - 2] < highs[idx - 1] < highs[idx]):
        return None
    
    confidence = 80
    
    return {
        "pattern": "three_white_soldiers",
        "signal": "bullish",
        "confidence": round(confidence, 0)
    }


def detect_three_black_crows(idx: int, opens: List[float], highs: List[float], 
                            lows: List[float], closes: List[float], atr: float) -> Optional[Dict]:
    """
    Detect Three Black Crows pattern (Bearish Continuation).
    
    Criteria:
    - Three consecutive bearish candles
    - Each opens within previous body
    - Each closes near lows (< 20% shadow)
    - Progressive lows
    """
    if idx < 2 or idx >= len(opens):
        return None
    
    bodies = []
    for i in range(idx - 2, idx + 1):
        open_p = opens[i]
        close = closes[i]
        low = lows[i]
        
        # Must be bearish
        if not is_bearish_candle(open_p, close):
            return None
        
        # Must close near lows
        lower_shadow = calculate_lower_shadow(low, open_p, close)
        total_range = highs[i] - low
        if total_range > 0 and lower_shadow / total_range > 0.2:
            return None
        
        bodies.append(calculate_body_size(open_p, close))
    
    # Check opens within previous body
    for i in range(1, 3):
        prev_idx = idx - 3 + i
        curr_idx = idx - 3 + i + 1
        if opens[curr_idx] >= opens[prev_idx] or opens[curr_idx] <= closes[prev_idx]:
            return None
    
    # Check progressive lows
    if not (lows[idx - 2] > lows[idx - 1] > lows[idx]):
        return None
    
    confidence = 80
    
    return {
        "pattern": "three_black_crows",
        "signal": "bearish",
        "confidence": round(confidence, 0)
    }


def check_confirmation(pattern_signal: str, pattern_idx: int, highs: List[float], 
                      lows: List[float], closes: List[float]) -> str:
    """
    Check if pattern has been confirmed by next day's price action.
    
    Bullish confirmation: Next day close > pattern high
    Bearish confirmation: Next day close < pattern low
    """
    # If this is the last candle, confirmation is pending
    if pattern_idx >= len(closes) - 1:
        return "pending"
    
    next_close = closes[pattern_idx + 1]
    
    if pattern_signal == "bullish":
        # Bullish confirmed if next close > pattern high
        if next_close > highs[pattern_idx]:
            return "confirmed"
        else:
            return "pending"
    else:  # bearish
        # Bearish confirmed if next close < pattern low
        if next_close < lows[pattern_idx]:
            return "confirmed"
        else:
            return "pending"


def calculate_days_ago(pattern_date: str, dates: List[str]) -> int:
    """Calculate how many days ago the pattern occurred."""
    if not dates:
        return 0
    
    try:
        last_date = dates[-1]
        pattern_dt = datetime.strptime(pattern_date, '%Y-%m-%d')
        last_dt = datetime.strptime(last_date, '%Y-%m-%d')
        days_diff = (last_dt - pattern_dt).days
        return max(0, days_diff)
    except:
        return 0


def scan_patterns_last_7days(opens: List[float], highs: List[float], 
                             lows: List[float], closes: List[float], 
                             volumes: List[int], atr: float, 
                             dates: List[str]) -> List[Dict]:
    """
    Scan last 7 trading days for candlestick patterns with confirmation.
    
    Returns list of detected patterns sorted by date (oldest first).
    Only returns confirmed or pending patterns (skips failed confirmations).
    
    Args:
        opens: List of opening prices
        highs: List of high prices
        lows: List of low prices
        closes: List of closing prices
        volumes: List of volumes
        atr: Average True Range value
        dates: List of date strings (YYYY-MM-DD format)
    
    Returns:
        List of pattern dictionaries with keys:
        - date: Pattern date (YYYY-MM-DD)
        - days_ago: Days since pattern
        - pattern: Pattern name
        - signal: "bullish" or "bearish"
        - confidence: Confidence score (0-100)
        - status: "confirmed" or "pending"
    """
    if len(opens) < 8:  # Need at least 8 days (7 to analyze + 1 for confirmation)
        return []
    
    patterns = []
    
    # Analyze last 7 trading days (need 8 days of data to check confirmation for day 7)
    start_idx = max(0, len(opens) - 7)
    
    for idx in range(start_idx, len(opens)):
        detected = None
        
        # Single candle patterns
        hammer = detect_hammer(idx, opens, highs, lows, closes, atr)
        if hammer:
            detected = hammer
        
        shooting_star = detect_shooting_star(idx, opens, highs, lows, closes, atr)
        if shooting_star:
            detected = shooting_star
        
        # Two candle patterns
        if idx >= 1:
            bullish_eng = detect_bullish_engulfing(idx, opens, highs, lows, closes, volumes, atr)
            if bullish_eng:
                detected = bullish_eng
            
            bearish_eng = detect_bearish_engulfing(idx, opens, highs, lows, closes, volumes, atr)
            if bearish_eng:
                detected = bearish_eng
        
        # Three candle patterns
        if idx >= 2:
            morning = detect_morning_star(idx, opens, highs, lows, closes, atr)
            if morning:
                detected = morning
            
            evening = detect_evening_star(idx, opens, highs, lows, closes, atr)
            if evening:
                detected = evening
            
            soldiers = detect_three_white_soldiers(idx, opens, highs, lows, closes, atr)
            if soldiers:
                detected = soldiers
            
            crows = detect_three_black_crows(idx, opens, highs, lows, closes, atr)
            if crows:
                detected = crows
        
        # If pattern detected, check confirmation and add to results
        if detected:
            status = check_confirmation(detected["signal"], idx, highs, lows, closes)
            
            # Only include confirmed or pending patterns (skip failed)
            if status in ["confirmed", "pending"]:
                pattern_date = dates[idx] if idx < len(dates) else ""
                days_ago = calculate_days_ago(pattern_date, dates)
                
                patterns.append({
                    "date": pattern_date,
                    "days_ago": days_ago,
                    "pattern": detected["pattern"],
                    "signal": detected["signal"],
                    "confidence": detected["confidence"],
                    "status": status
                })
    
    # Sort by date (oldest first) for chronological display
    patterns.sort(key=lambda x: x["date"])
    
    return patterns
