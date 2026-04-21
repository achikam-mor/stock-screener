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


# ============================================================================
# CUP AND HANDLE PATTERN DETECTION (William O'Neil)
# ============================================================================

def detect_cup_formation(highs: List[float], lows: List[float], closes: List[float], 
                         start_idx: int, end_idx: int) -> Optional[Dict]:
    """
    Detect cup formation within a given range.
    
    Returns dict with:
    - left_rim_idx: Index of left rim peak
    - left_rim_price: Price at left rim
    - cup_bottom_idx: Index of cup bottom
    - cup_bottom_price: Price at cup bottom
    - right_rim_idx: Index of right rim
    - right_rim_price: Price at right rim
    - depth_percent: Depth as percentage
    - is_valid: Boolean indicating if cup meets criteria
    """
    if end_idx - start_idx < 30:  # Minimum 30 days for cup
        return None
    
    # Find left rim (highest high in first portion)
    search_end = start_idx + (end_idx - start_idx) // 3  # First third
    left_rim_idx = start_idx
    left_rim_price = highs[start_idx]
    
    for i in range(start_idx, min(search_end, len(highs))):
        if highs[i] > left_rim_price:
            left_rim_price = highs[i]
            left_rim_idx = i
    
    # Validate that price doesn't significantly exceed left rim during cup formation
    # This ensures the left rim is truly the peak and not violated during cup
    rim_violation_tolerance = 0.02  # Allow 2% tolerance for minor spikes
    
    for i in range(left_rim_idx + 1, min(end_idx, len(highs))):
        if highs[i] > left_rim_price * (1 + rim_violation_tolerance):
            # Price exceeded the left rim - this invalidates the cup
            return None
    
    # Find cup bottom (lowest point after left rim)
    cup_bottom_idx = left_rim_idx
    cup_bottom_price = lows[left_rim_idx]
    
    for i in range(left_rim_idx + 1, min(end_idx, len(lows))):
        if lows[i] < cup_bottom_price:
            cup_bottom_price = lows[i]
            cup_bottom_idx = i
    
    # Find right rim (where price recovers to near left rim level)
    # Look for the price that comes CLOSEST to the left rim (within 3% tolerance)
    # Search includes end_idx since that's where we expect the cup to complete
    right_rim_idx = None
    right_rim_price = None
    rim_tolerance = 0.03  # 3% tolerance
    best_diff = float('inf')
    
    for i in range(cup_bottom_idx + 1, min(end_idx + 1, len(highs))):
        diff = abs(highs[i] - left_rim_price) / left_rim_price
        if diff <= rim_tolerance and diff < best_diff:
            right_rim_idx = i
            right_rim_price = highs[i]
            best_diff = diff
    
    if right_rim_idx is None:
        return None
    
    # Calculate depth
    depth_percent = ((left_rim_price - cup_bottom_price) / left_rim_price) * 100
    
    # Validate depth (12-35% per O'Neil)
    if depth_percent < 12 or depth_percent > 35:
        return None
    
    # Validate time symmetry (more lenient tolerance for real-world patterns)
    left_duration = cup_bottom_idx - left_rim_idx
    right_duration = right_rim_idx - cup_bottom_idx
    
    if left_duration == 0:
        return None
    
    time_ratio = right_duration / left_duration
    if time_ratio < 0.5 or time_ratio > 2.0:  # 50% tolerance (more realistic than O'Neil's ideal)
        return None
    
    # Validate U-shape (not V-shape) - bottom should be relatively flat
    # Check if recovery isn't too steep
    if right_duration < 5:  # Too quick recovery = V-shape
        return None
    
    return {
        "left_rim_idx": left_rim_idx,
        "left_rim_price": left_rim_price,
        "cup_bottom_idx": cup_bottom_idx,
        "cup_bottom_price": cup_bottom_price,
        "right_rim_idx": right_rim_idx,
        "right_rim_price": right_rim_price,
        "depth_percent": depth_percent,
        "is_valid": True
    }


def detect_handle_downward_drift(highs: List[float], lows: List[float], closes: List[float],
                                  handle_start_idx: int, handle_end_idx: int,
                                  cup_bottom_price: float, cup_rim_price: float) -> Optional[str]:
    """
    Detect downward drift handle shape.
    Returns 'drift' if detected, None otherwise.
    """
    if handle_end_idx - handle_start_idx < 5:
        return None
    
    # Check for lower highs and lower lows pattern
    lower_highs_count = 0
    lower_lows_count = 0
    
    for i in range(handle_start_idx + 1, handle_end_idx):
        if highs[i] < highs[i-1]:
            lower_highs_count += 1
        if lows[i] < lows[i-1]:
            lower_lows_count += 1
    
    total_periods = handle_end_idx - handle_start_idx - 1
    
    # At least 60% should show downward drift
    if (lower_highs_count / total_periods >= 0.6 or 
        lower_lows_count / total_periods >= 0.6):
        return 'drift'
    
    return None


def detect_handle_flag(highs: List[float], lows: List[float], closes: List[float],
                       handle_start_idx: int, handle_end_idx: int,
                       cup_bottom_price: float, cup_rim_price: float) -> Optional[str]:
    """
    Detect flag pattern handle shape (parallel channel).
    Returns 'flag' if detected, None otherwise.
    """
    if handle_end_idx - handle_start_idx < 5:
        return None
    
    # Calculate upper and lower bounds
    handle_highs = highs[handle_start_idx:handle_end_idx]
    handle_lows = lows[handle_start_idx:handle_end_idx]
    
    avg_high = sum(handle_highs) / len(handle_highs)
    avg_low = sum(handle_lows) / len(handle_lows)
    
    # Check if highs and lows stay relatively parallel
    high_variance = sum(abs(h - avg_high) for h in handle_highs) / len(handle_highs)
    low_variance = sum(abs(l - avg_low) for l in handle_lows) / len(handle_lows)
    
    channel_width = avg_high - avg_low
    
    # Flag should have consistent channel width (variance < 30% of width)
    if (high_variance < 0.3 * channel_width and 
        low_variance < 0.3 * channel_width and
        channel_width > 0):
        return 'flag'
    
    return None


def detect_handle_pennant(highs: List[float], lows: List[float], closes: List[float],
                          handle_start_idx: int, handle_end_idx: int,
                          cup_bottom_price: float, cup_rim_price: float) -> Optional[str]:
    """
    Detect pennant handle shape (converging trendlines).
    Returns 'pennant' if detected, None otherwise.
    """
    if handle_end_idx - handle_start_idx < 5:
        return None
    
    # Calculate ranges for first and second half
    mid_idx = (handle_start_idx + handle_end_idx) // 2
    
    first_half_range = max(highs[handle_start_idx:mid_idx]) - min(lows[handle_start_idx:mid_idx])
    second_half_range = max(highs[mid_idx:handle_end_idx]) - min(lows[mid_idx:handle_end_idx])
    
    if first_half_range == 0:
        return None
    
    # Pennant should show tightening range (second half < first half)
    if second_half_range < first_half_range * 0.7:  # 30% reduction in range
        return 'pennant'
    
    return None


def detect_handle_shape(highs: List[float], lows: List[float], closes: List[float],
                        handle_start_idx: int, handle_end_idx: int,
                        cup_bottom_price: float, cup_rim_price: float) -> Optional[str]:
    """
    Detect handle shape - try all three types.
    Returns: 'drift', 'flag', 'pennant', or None
    """
    # Try downward drift first (most reliable per O'Neil)
    drift = detect_handle_downward_drift(highs, lows, closes, handle_start_idx, 
                                         handle_end_idx, cup_bottom_price, cup_rim_price)
    if drift:
        return drift
    
    # Try flag pattern
    flag = detect_handle_flag(highs, lows, closes, handle_start_idx, 
                              handle_end_idx, cup_bottom_price, cup_rim_price)
    if flag:
        return flag
    
    # Try pennant
    pennant = detect_handle_pennant(highs, lows, closes, handle_start_idx, 
                                    handle_end_idx, cup_bottom_price, cup_rim_price)
    if pennant:
        return pennant
    
    return None


def validate_handle_position(handle_start_idx: int, handle_end_idx: int,
                             highs: List[float], lows: List[float], closes: List[float],
                             cup_bottom_price: float, cup_rim_price: float) -> bool:
    """
    Validate handle meets O'Neil criteria:
    - Bottom stays above cup bottom
    - Forms in upper half of cup
    - Doesn't decline more than 15% from handle start
    """
    handle_low = min(lows[handle_start_idx:handle_end_idx])
    handle_start_price = closes[handle_start_idx]
    
    # Handle bottom must be above cup bottom
    if handle_low <= cup_bottom_price:
        return False
    
    # Handle should form in upper half of cup
    cup_range = cup_rim_price - cup_bottom_price
    if (handle_low - cup_bottom_price) < (cup_range * 0.5):
        return False
    
    # Handle decline shouldn't exceed 15%
    decline_percent = ((handle_start_price - handle_low) / handle_start_price) * 100
    if decline_percent > 15:
        return False
    
    return True


def validate_volume_requirements(volumes: List[int], cup_start_idx: int, cup_end_idx: int,
                                 handle_start_idx: int, handle_end_idx: int,
                                 breakout_idx: Optional[int] = None) -> bool:
    """
    Validate O'Neil volume requirements:
    - Handle volume should be ≤70% of cup average volume
    - Breakout volume should be >150% of handle average volume
    """
    if not volumes or len(volumes) == 0:
        return False
    
    # Calculate cup average volume
    cup_volumes = volumes[cup_start_idx:cup_end_idx]
    if not cup_volumes:
        return False
    cup_avg_volume = sum(cup_volumes) / len(cup_volumes)
    
    # Calculate handle average volume
    handle_volumes = volumes[handle_start_idx:handle_end_idx]
    if not handle_volumes:
        return False
    handle_avg_volume = sum(handle_volumes) / len(handle_volumes)
    
    # Handle volume should be declining (≤70% of cup average)
    if handle_avg_volume > cup_avg_volume * 0.7:
        return False
    
    # If breakout occurred, check volume spike
    if breakout_idx is not None:
        breakout_volume = volumes[breakout_idx]
        if breakout_volume < handle_avg_volume * 1.5:
            return False
    
    return True


def detect_cup_and_handle(opens: List[float], highs: List[float], lows: List[float],
                          closes: List[float], volumes: List[int], dates: List[str]) -> Optional[Dict]:
    """
    Detect Cup and Handle pattern per William O'Neil methodology.
    
    Scans for potential left rims, then naturally finds cup bottoms and right rims.
    Returns only patterns where breakout confirmation occurred in last 7 days OR
    handle is forming within last 7 days.
    
    Returns dict with full pattern details or None if no valid pattern found.
    """
    if len(closes) < 35:  # Minimum: 30 days cup + 5 days handle
        return None
    
    # Only return patterns where breakout/handle is recent (last 7 days)
    recent_cutoff_idx = len(closes) - 7
    
    # New approach: Scan for potential left rims (local highs in recent 300 days)
    # Start from most recent data and work backward to find longer cups first
    max_lookback = min(300, len(closes) - 35)  # Need room for cup + handle
    
    for left_rim_idx in range(len(closes) - 35, max(0, len(closes) - max_lookback - 1), -1):
        # Check if this is a significant local high (potential left rim)
        # Must be higher than nearby prices (5-day window)
        window_start = max(0, left_rim_idx - 5)
        window_end = min(len(highs), left_rim_idx + 6)
        if highs[left_rim_idx] != max(highs[window_start:window_end]):
            continue  # Not a local high
        
        left_rim_price = highs[left_rim_idx]
        
        # Search forward for cup bottom (30-300 days from left rim)
        for bottom_search_end in range(left_rim_idx + 30, min(left_rim_idx + 301, len(lows) - 5)):
            # Find the lowest low between left rim and search point
            bottom_segment = lows[left_rim_idx:bottom_search_end]
            if not bottom_segment:
                continue
            cup_bottom_price = min(bottom_segment)
            cup_bottom_idx = left_rim_idx + bottom_segment.index(cup_bottom_price)
            
            # Validate depth (12-35%)
            depth_percent = ((left_rim_price - cup_bottom_price) / left_rim_price) * 100
            if depth_percent < 12 or depth_percent > 35:
                continue
            
            # Must have at least 5 days after bottom for recovery + handle
            if cup_bottom_idx >= len(highs) - 10:
                continue
            
            # Search for right rim (price recovering to near left rim, within 3%)
            right_rim_idx = None
            right_rim_price = None
            best_diff = float('inf')
            rim_tolerance = 0.03
            
            # Search from bottom to reasonable distance (max 300 days total cup)
            search_end = min(cup_bottom_idx + (cup_bottom_idx - left_rim_idx) * 3, 
                           left_rim_idx + 300, 
                           len(highs) - 5)
            
            for i in range(cup_bottom_idx + 5, search_end):  # Need at least 5 days recovery
                diff = abs(highs[i] - left_rim_price) / left_rim_price
                if diff <= rim_tolerance and diff < best_diff:
                    right_rim_idx = i
                    right_rim_price = highs[i]
                    best_diff = diff
            
            if right_rim_idx is None:
                continue
            
            # Validate no rim violations between left and right rim
            rim_violation = False
            for i in range(left_rim_idx + 1, right_rim_idx + 1):
                if highs[i] > left_rim_price * 1.02:  # 2% tolerance
                    rim_violation = True
                    break
            if rim_violation:
                continue
            
            # Validate time symmetry (50% tolerance)
            left_duration = cup_bottom_idx - left_rim_idx
            right_duration = right_rim_idx - cup_bottom_idx
            if left_duration == 0:
                continue
            time_ratio = right_duration / left_duration
            if time_ratio < 0.5 or time_ratio > 2.0:
                continue
            
            # Validate U-shape (not V-shape)
            if right_duration < 5:
                continue
            
            # Valid cup found! Now look for handle
            cup = {
                "left_rim_idx": left_rim_idx,
                "left_rim_price": left_rim_price,
                "cup_bottom_idx": cup_bottom_idx,
                "cup_bottom_price": cup_bottom_price,
                "right_rim_idx": right_rim_idx,
                "right_rim_price": right_rim_price,
                "depth_percent": depth_percent,
                "is_valid": True
            }
            
            # Now look for handle after cup
            handle_search_start = cup["right_rim_idx"]
            handle_search_end = min(handle_search_start + 25, len(closes))  # Max 25 days handle
            
            # Try different handle lengths (5-25 days)
            for handle_end in range(handle_search_start + 5, handle_search_end + 1):
                handle_start_idx = cup["right_rim_idx"]
                handle_end_idx = handle_end
                
                # Validate handle position
                if not validate_handle_position(handle_start_idx, handle_end_idx, highs, lows, closes,
                                               cup["cup_bottom_price"], cup["left_rim_price"]):
                    continue
                
                # Detect handle shape
                handle_shape = detect_handle_shape(highs, lows, closes, handle_start_idx, handle_end_idx,
                                                   cup["cup_bottom_price"], cup["left_rim_price"])
                
                if not handle_shape:
                    continue
                
                # Validate volume requirements
                if not validate_volume_requirements(volumes, left_rim_idx, cup["right_rim_idx"],
                                                   handle_start_idx, handle_end_idx):
                    continue
                
                # Find handle resistance (highest point in handle)
                handle_resistance = max(highs[handle_start_idx:handle_end_idx])
                handle_low = min(lows[handle_start_idx:handle_end_idx])
                
                # Check for breakout (1% above handle resistance)
                breakout_idx = None
                breakout_date = None
                
                for i in range(handle_end_idx, len(closes)):
                    if closes[i] >= handle_resistance * 1.01:  # 1% above resistance
                        # Validate breakout volume
                        if validate_volume_requirements(volumes, left_rim_idx, cup["right_rim_idx"],
                                                       handle_start_idx, handle_end_idx, i):
                            breakout_idx = i
                            breakout_date = dates[i] if i < len(dates) else None
                            break
                
                # Determine if pattern is recent enough to return
                status = None
                days_ago = None
                
                if breakout_idx and breakout_idx >= recent_cutoff_idx:
                    # Breakout occurred in last 7 days - CONFIRMED
                    status = "confirmed"
                    days_ago = len(closes) - 1 - breakout_idx
                elif handle_end_idx >= recent_cutoff_idx and not breakout_idx:
                    # Handle is forming in last 7 days, no breakout yet - FORMING
                    status = "forming"
                    days_ago = len(closes) - 1 - handle_end_idx
                else:
                    # Pattern is too old, continue searching
                    continue
                
                # Calculate confidence based on handle shape
                confidence = {
                    'drift': 87,
                    'flag': 82,
                    'pennant': 77
                }.get(handle_shape, 75)
                
                # Calculate profit target (cup depth projected upward from rim)
                rim_price = cup["left_rim_price"]
                profit_target = rim_price + (rim_price * (cup["depth_percent"] / 100))
                
                # Calculate risk/reward ratio
                risk = rim_price - handle_low
                reward = profit_target - rim_price
                risk_reward_ratio = reward / risk if risk > 0 else 0
                
                # Return the pattern
                return {
                    "pattern": "cup_and_handle",
                    "signal": "bullish",
                    "handle_shape": handle_shape,
                    "cup_start_date": dates[left_rim_idx] if left_rim_idx < len(dates) else None,
                    "cup_end_date": dates[cup["right_rim_idx"]] if cup["right_rim_idx"] < len(dates) else None,
                    "handle_start_date": dates[handle_start_idx] if handle_start_idx < len(dates) else None,
                    "breakout_date": breakout_date,
                    "rim_price": round(rim_price, 2),
                    "cup_bottom_price": round(cup["cup_bottom_price"], 2),
                    "handle_low": round(handle_low, 2),
                    "depth_percent": round(cup["depth_percent"], 2),
                    "profit_target": round(profit_target, 2),
                    "risk_reward_ratio": round(risk_reward_ratio, 2),
                    "status": status,
                    "confidence": confidence,
                    "days_ago": days_ago
                }
    
    return None
