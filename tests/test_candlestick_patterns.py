"""Unit tests for the hardened candlestick pattern detectors."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from candlestick_patterns import (
    compute_volume_confirmation, prior_trend, _vol_confidence_boost,
    detect_hammer, detect_shooting_star,
    detect_bullish_engulfing, detect_bearish_engulfing,
    detect_piercing_line, detect_dark_cloud_cover,
    detect_morning_star, detect_evening_star,
    detect_three_white_soldiers, detect_three_black_crows,
    scan_patterns_last_7days,
    VOL_CONFIRM, VOL_MID, CONF_FLOOR,
)


# ── Volume helpers ─────────────────────────────────────────────────────────────

def test_volume_confirmation_high():
    vols = [100_000] * 20 + [200_000]
    ratio, confirmed = compute_volume_confirmation(vols, 20)
    assert confirmed is True
    assert ratio >= VOL_CONFIRM


def test_volume_confirmation_mid():
    vols = [100_000] * 20 + [125_000]
    ratio, confirmed = compute_volume_confirmation(vols, 20)
    assert not confirmed
    assert ratio >= VOL_MID


def test_volume_confirmation_low():
    vols = [100_000] * 20 + [80_000]
    ratio, confirmed = compute_volume_confirmation(vols, 20)
    assert not confirmed
    assert ratio < VOL_MID


def test_volume_confirmation_insufficient_data():
    ratio, confirmed = compute_volume_confirmation([50_000], 0)
    assert ratio == 0.0
    assert confirmed is False


def test_vol_confidence_boost():
    assert _vol_confidence_boost(1.6) == 10
    assert _vol_confidence_boost(1.3) == 5
    assert _vol_confidence_boost(1.0) == 0


# ── Prior trend ────────────────────────────────────────────────────────────────

def _downtrend(n=15):
    return [100.0 - i * 1.0 for i in range(n)]


def _uptrend(n=15):
    return [100.0 + i * 1.0 for i in range(n)]


def _sideways(n=15):
    return [100.0 + (i % 2) * 0.1 for i in range(n)]


def test_prior_trend_down():
    closes = _downtrend(20)
    assert prior_trend(closes, 15) == "downtrend"


def test_prior_trend_up():
    closes = _uptrend(20)
    assert prior_trend(closes, 15) == "uptrend"


def test_prior_trend_sideways():
    closes = _sideways(20)
    assert prior_trend(closes, 15) == "sideways"


def test_prior_trend_too_few_bars():
    assert prior_trend([100.0, 99.0, 98.0], 2) == "sideways"


# ── Hammer ─────────────────────────────────────────────────────────────────────

def _make_hammer(atr=2.0):
    """Classic hammer: real body near top, lower shadow ~2.86× body (clearly > 2.5×)."""
    # body=0.35, lower_shadow=1.0 (2.86x), upper_shadow=0.05, total_range=1.4
    opens  = [9.65]
    highs  = [10.05]
    lows   = [8.65]
    closes = [10.0]
    return opens, highs, lows, closes, atr


def test_hammer_detected():
    op, hi, lo, cl, atr = _make_hammer()
    result = detect_hammer(0, op, hi, lo, cl, atr)
    assert result is not None
    assert result["signal"] == "bullish"
    assert result["pattern"] == "hammer"
    assert result["confidence"] >= CONF_FLOOR


def test_hammer_rejects_no_lower_shadow():
    op  = [10.0]
    hi  = [10.3]
    lo  = [9.9]
    cl  = [10.2]
    assert detect_hammer(0, op, hi, lo, cl, 1.0) is None


def test_hammer_rejects_doji():
    """Body < 8% of range → doji, not hammer."""
    op  = [10.005]
    hi  = [10.2]
    lo  = [8.0]
    cl  = [10.01]
    assert detect_hammer(0, op, hi, lo, cl, 2.0) is None


# ── Shooting Star ──────────────────────────────────────────────────────────────

def test_shooting_star_detected():
    # body=0.35 (bearish), upper_shadow=1.0 (2.86×), lower_shadow=0.05, total_range=1.4
    op = [10.0]
    hi = [11.0]
    lo = [9.60]
    cl = [9.65]
    result = detect_shooting_star(0, op, hi, lo, cl, 2.0)
    assert result is not None
    assert result["signal"] == "bearish"


def test_shooting_star_rejects_large_lower_shadow():
    op = [10.1]
    hi = [12.0]
    lo = [9.0]   # big lower shadow
    cl = [10.0]
    assert detect_shooting_star(0, op, hi, lo, cl, 2.0) is None


# ── Engulfing ──────────────────────────────────────────────────────────────────

def test_bullish_engulfing_detected():
    op = [11.0, 9.5]
    hi = [11.5, 11.5]
    lo = [9.8, 9.2]
    cl = [10.0, 11.2]
    atr = 1.5
    result = detect_bullish_engulfing(1, op, hi, lo, cl, atr)
    assert result is not None
    assert result["signal"] == "bullish"


def test_bullish_engulfing_requires_significant_prior_body():
    """Prior body < 0.3 * ATR → rejected."""
    op = [10.05, 9.9]
    hi = [10.1, 10.2]
    lo = [9.9, 9.8]
    cl = [10.0, 10.05]  # prior body = 0.05, ATR = 2.0 → too small
    assert detect_bullish_engulfing(1, op, hi, lo, cl, 2.0) is None


def test_bearish_engulfing_detected():
    op = [10.0, 11.5]
    hi = [11.0, 11.8]
    lo = [9.8, 9.5]
    cl = [11.0, 9.8]
    atr = 1.5
    result = detect_bearish_engulfing(1, op, hi, lo, cl, atr)
    assert result is not None
    assert result["signal"] == "bearish"


# ── Piercing Line ──────────────────────────────────────────────────────────────

def test_piercing_line_detected():
    """Day 1 long bearish; Day 2 opens below Day 1 low, closes above midpoint but below Day 1 open."""
    op = [12.0, 9.0]
    hi = [12.5, 11.3]
    lo = [10.0, 8.8]
    cl = [10.0, 11.2]   # midpoint of Day1 = (12+10)/2=11, close=11.2 > 11
    atr = 2.0
    result = detect_piercing_line(1, op, hi, lo, cl, atr)
    assert result is not None
    assert result["signal"] == "bullish"
    assert result["pattern"] == "piercing_line"


def test_piercing_line_rejects_full_engulf():
    """If close >= Day 1 open it becomes engulfing, not piercing."""
    op = [12.0, 9.0]
    hi = [12.5, 12.5]
    lo = [10.0, 8.8]
    cl = [10.0, 12.1]   # exceeds Day 1 open → not piercing
    assert detect_piercing_line(1, op, hi, lo, cl, 2.0) is None


# ── Dark Cloud Cover ───────────────────────────────────────────────────────────

def test_dark_cloud_cover_detected():
    # Day1 bullish body=2, Day2 opens above Day1 high, closes below midpoint (11), above Day1 open (10)
    op = [10.0, 13.0]
    hi = [12.0, 13.2]
    lo = [9.8,  10.5]
    cl = [12.0, 10.8]
    atr = 2.0
    result = detect_dark_cloud_cover(1, op, hi, lo, cl, atr)
    assert result is not None
    assert result["signal"] == "bearish"
    assert result["pattern"] == "dark_cloud_cover"


def test_dark_cloud_cover_rejects_full_engulf():
    op = [10.0, 13.0]
    hi = [12.0, 13.2]
    lo = [9.8, 9.5]
    cl = [12.0, 9.6]    # close < Day 1 close → full engulf, not dark cloud
    assert detect_dark_cloud_cover(1, op, hi, lo, cl, 2.0) is None


# ── Morning / Evening Star ─────────────────────────────────────────────────────

def test_morning_star_detected():
    op = [12.0, 9.5, 9.0]
    hi = [12.5, 10.0, 12.5]
    lo = [9.5,  9.0, 8.5]
    cl = [10.0, 9.6, 12.0]
    atr = 2.0
    result = detect_morning_star(2, op, hi, lo, cl, atr)
    assert result is not None
    assert result["signal"] == "bullish"


def test_evening_star_detected():
    op = [10.0, 12.5, 13.0]
    hi = [12.5, 13.0, 13.5]
    lo = [9.8,  12.3, 9.5]
    cl = [12.0, 12.6, 9.8]
    atr = 2.0
    result = detect_evening_star(2, op, hi, lo, cl, atr)
    assert result is not None
    assert result["signal"] == "bearish"


# ── Three White Soldiers / Three Black Crows ───────────────────────────────────

def test_three_white_soldiers_detected():
    op = [10.0, 10.8, 11.7]
    hi = [11.0, 11.8, 12.8]
    lo = [9.9,  10.7, 11.6]
    cl = [10.9, 11.75, 12.7]
    atr = 0.8
    result = detect_three_white_soldiers(2, op, hi, lo, cl, atr)
    assert result is not None
    assert result["signal"] == "bullish"


def test_three_black_crows_detected():
    # Each opens strictly inside prior body (close < open, so prev_close < curr_open < prev_open)
    op = [13.0, 12.3, 11.4]
    hi = [13.1, 12.4, 11.5]
    lo = [12.1, 11.2, 10.2]
    cl = [12.2, 11.3, 10.3]
    atr = 0.8
    result = detect_three_black_crows(2, op, hi, lo, cl, atr)
    assert result is not None
    assert result["signal"] == "bearish"


# ── Scan function integration ──────────────────────────────────────────────────

def _flat_series(n, base=100.0):
    return [base] * n


def test_scan_returns_list():
    n = 20
    op = _flat_series(n)
    hi = [x + 1 for x in op]
    lo = [x - 1 for x in op]
    cl = _flat_series(n)
    vols = [1_000_000] * n
    dates = [f"2026-07-{i + 1:02d}" for i in range(n)]
    result = scan_patterns_last_7days(op, hi, lo, cl, vols, 1.0, dates)
    assert isinstance(result, list)


def test_scan_enriches_fields():
    """Any detected pattern must carry all new enrichment fields."""
    # Build a clear downtrend + hammer at the end so a bullish pattern fires
    closes = [100.0 - i * 0.8 for i in range(25)]
    opens  = [c + 0.2 for c in closes]
    # Inject a hammer on the last bar
    opens[-1]  = 85.5
    closes[-1] = 85.4
    highs      = [max(o, c) + 0.3 for o, c in zip(opens, closes)]
    lows       = [min(o, c) - 0.3 for o, c in zip(opens, closes)]
    lows[-1]   = 82.0   # long lower shadow → hammer geometry
    highs[-1]  = 85.6
    vols = [500_000] * 25
    vols[-1] = 900_000   # above-average volume → volume_confirmed
    dates = [f"2026-07-{i + 1:02d}" for i in range(25)]
    atr = 1.5

    results = scan_patterns_last_7days(opens, highs, lows, closes, vols, atr, dates)
    for p in results:
        assert "category" in p and p["category"] == "candlestick"
        assert "candles" in p and isinstance(p["candles"], int)
        assert "volume_ratio" in p
        assert "volume_confirmed" in p
        assert "trend_context_ok" in p
        assert p["confidence"] >= CONF_FLOOR


def test_scan_dedup_keeps_highest_confidence():
    """On any single day only one pattern (highest confidence) should be reported."""
    n = 25
    op    = _flat_series(n, 10.0)
    hi    = [x + 1 for x in op]
    lo    = [x - 1 for x in op]
    cl    = _flat_series(n, 10.0)
    vols  = [1_000_000] * n
    dates = [f"2026-07-{i + 1:02d}" for i in range(n)]

    results = scan_patterns_last_7days(op, hi, lo, cl, vols, 1.0, dates)
    dates_seen = [p["date"] for p in results]
    assert len(dates_seen) == len(set(dates_seen)), "Duplicate date in scan output"


def test_scan_trend_gate_blocks_bullish_in_uptrend():
    """Bullish reversal patterns must be suppressed when prior trend is uptrend."""
    # Strong uptrend with a hammer candle at the end — hammer should be gated out
    closes = [100.0 + i * 1.5 for i in range(25)]
    opens  = [c - 0.1 for c in closes]
    highs  = [c + 0.3 for c in closes]
    lows   = list(closes)
    # Inject hammer geometry on last bar
    lows[-1]   = closes[-1] - 3.0
    highs[-1]  = closes[-1] + 0.1
    opens[-1]  = closes[-1] - 0.05
    vols = [500_000] * 25
    dates = [f"2026-07-{i + 1:02d}" for i in range(25)]

    results = scan_patterns_last_7days(opens, highs, lows, closes, vols, 1.0, dates)
    bullish_reversals = [p for p in results if p["signal"] == "bullish"
                         and p["pattern"] in ("hammer", "bullish_engulfing", "morning_star",
                                               "piercing_line")]
    assert bullish_reversals == [], "Bullish reversal fired in an uptrend"
