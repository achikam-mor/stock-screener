import pytest
import pandas as pd
import numpy as np
from stock_analyzer import StockAnalyzer

@pytest.fixture
def sample_data():
    # Create sample stock data
    dates = pd.date_range(start="2020-01-01", periods=200, freq="D")
    data = pd.DataFrame({
        "Close": np.linspace(100, 200, 200),  # Linear trend up
        "High": np.linspace(102, 202, 200),   # Always 2 above close
        "Low": np.linspace(98, 198, 200),     # Always 2 below close
    }, index=dates)
    return data

def test_calculate_sma(sample_data):
    analyzer = StockAnalyzer()
    sma = analyzer.calculate_sma(sample_data, window=50)

    # Check if SMA is calculated correctly
    assert len(sma) == len(sample_data)
    assert pd.isna(sma[0:49]).all()  # First 49 values should be NaN
    assert not pd.isna(sma[49:]).any()  # Rest should be numbers

    # Check if SMA is actually averaging correctly
    test_point = 100  # Some point after the initial window
    expected_avg = sample_data["Close"][test_point-50:test_point].mean()
    assert abs(sma[test_point] - expected_avg) < 0.0001

def test_calculate_atr(sample_data):
    analyzer = StockAnalyzer()
    atr, atr_pct = analyzer.calculate_atr(sample_data, window=14)

    # Check ATR calculation
    # In our sample data, High-Low spread is always 4
    assert abs(atr - 4.0) < 0.0001

    # Check ATR percentage
    first_14_close_avg = sample_data["Close"][:14].mean()
    expected_atr_pct = (4.0 / first_14_close_avg) * 100
    assert abs(atr_pct - expected_atr_pct) < 0.0001

def test_validate_min_data(sample_data):
    analyzer = StockAnalyzer()

    # Test with sufficient data
    assert analyzer.validate_min_data(sample_data, window=150) == True

    # Test with insufficient data
    short_data = sample_data[:100]
    assert analyzer.validate_min_data(short_data, window=150) == False

def test_check_sma_conditions(sample_data):
    analyzer = StockAnalyzer()

    # Add SMA to data
    sample_data["SMA150"] = analyzer.calculate_sma(sample_data, window=150)

    # Test conditions
    met, last_close, last_sma = analyzer.check_sma_conditions(sample_data)

    # In our sample data, the trend is linear up, so conditions should be met
    assert met == True
    assert last_close == sample_data["Close"].iloc[0]
    assert last_sma == sample_data["SMA150"].iloc[0]

    # Test with downtrend data
    down_data = sample_data.copy()
    down_data["Close"] = np.linspace(200, 100, 200)
    down_data["SMA150"] = analyzer.calculate_sma(down_data, window=150)
    met, _, _ = analyzer.check_sma_conditions(down_data)
    assert met == False  # Should fail due to downtrend
