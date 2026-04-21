import pytest
from models import StockData, ScreenerResults
import io
import sys
from results_manager import ResultsManager

@pytest.fixture
def sample_results():
    hot_stocks = {
        "AAPL": StockData("AAPL", 150.0, 145.0, 3.0, 2.0),
        "GOOGL": StockData("GOOGL", 2500.0, 2400.0, 50.0, 2.0)
    }
    watch_list = {
        "MSFT": StockData("MSFT", 280.0, 285.0, 5.0, 1.8),
        "AMZN": StockData("AMZN", 3200.0, 3250.0, 60.0, 1.9)
    }
    failed_tickers = ["BAD1", "BAD2"]
    return ScreenerResults(hot_stocks, watch_list, failed_tickers)

def test_print_results(sample_results):
    manager = ResultsManager()

    # Capture stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    manager.print_results(sample_results)

    # Restore stdout
    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()

    # Verify all sections are present
    assert "=== Hot Stocks" in output
    assert "=== Watch List" in output
    assert "Failed to fetch data" in output

    # Verify all stocks are listed
    assert "AAPL" in output
    assert "GOOGL" in output
    assert "MSFT" in output
    assert "AMZN" in output

    # Verify failed tickers are listed
    assert "BAD1" in output
    assert "BAD2" in output

    # Verify some specific values
    assert "150.00" in output  # AAPL last close
    assert "145.00" in output  # AAPL SMA
    assert "2.00" in output    # AAPL ATR%

def test_print_results_no_failures(sample_results):
    manager = ResultsManager()
    sample_results.failed_tickers = []

    # Capture stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    manager.print_results(sample_results)

    # Restore stdout
    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()

    assert "✅ Successfully fetched data for all tickers!" in output
    assert "Failed to fetch data" not in output
