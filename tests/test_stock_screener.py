import pytest
from models import StockData, ScreenerResults
from stock_screener import StockScreener
from stock_analyzer import StockAnalyzer
import pandas as pd
import numpy as np

@pytest.fixture
def sample_stock_data():
    # Create sample data for multiple stocks
    dates = pd.date_range(start="2020-01-01", periods=200, freq="D")

    # Create uptrending stock
    up_stock = pd.DataFrame({
        "Close": np.linspace(100, 200, 200),
        "High": np.linspace(102, 202, 200),
        "Low": np.linspace(98, 198, 200),
        "SMA150": np.linspace(90, 180, 200),  # SMA below price
    }, index=dates)

    # Create flat stock
    flat_stock = pd.DataFrame({
        "Close": np.full(200, 100),
        "High": np.full(200, 102),
        "Low": np.full(200, 98),
        "SMA150": np.full(200, 100),  # SMA at price level
    }, index=dates)

    return {
        "UPTREND": up_stock,
        "FLAT": flat_stock,
    }

def test_screen_stocks(sample_stock_data):
    analyzer = StockAnalyzer()
    screener = StockScreener(analyzer)

    results = screener.screen_stocks(sample_stock_data)

    assert isinstance(results, ScreenerResults)
    assert "UPTREND" in results.hot_stocks  # Should be in hot_stocks as price > SMA
    assert "FLAT" in results.watch_list    # Should be in watch_list as price = SMA
    assert len(results.failed_tickers) == 0

def test_screen_stocks_with_invalid_data():
    analyzer = StockAnalyzer()
    screener = StockScreener(analyzer)

    # Create invalid data
    invalid_data = {
        "INVALID": pd.DataFrame({"Close": [], "High": [], "Low": []})
    }

    results = screener.screen_stocks(invalid_data)

    assert isinstance(results, ScreenerResults)
    assert len(results.hot_stocks) == 0
    assert len(results.watch_list) == 0
    assert "INVALID" in results.failed_tickers

def test_stock_data_classification(sample_stock_data):
    analyzer = StockAnalyzer()
    screener = StockScreener(analyzer)

    results = screener.screen_stocks(sample_stock_data)

    # Check UPTREND stock data
    uptrend_data = results.hot_stocks["UPTREND"]
    assert isinstance(uptrend_data, StockData)
    assert uptrend_data.last_close > uptrend_data.sma150
    assert uptrend_data.atr > 0
    assert uptrend_data.atr_percent > 0

    # Check FLAT stock data
    flat_data = results.watch_list["FLAT"]
    assert isinstance(flat_data, StockData)
    assert abs(flat_data.last_close - flat_data.sma150) < 0.0001
