import json
from datetime import datetime
from models import ScreenerResults

class ResultsManager:
    @staticmethod
    def print_results(results: ScreenerResults) -> None:
        print("\n=== Hot Stocks (Above SMA150 + Volume > 14d Avg) ===\n")
        # Sort hot stocks by distance from SMA
        sorted_stocks = sorted(
            results.hot_stocks.items(),
            key=lambda x: abs((x[1].last_close - x[1].sma150) / x[1].sma150 * 100)
        )
        for symbol, stock in sorted_stocks:
            distance_pct = (stock.last_close - stock.sma150) / stock.sma150 * 100
            volume_ratio = stock.last_volume / stock.avg_volume_14d
            print(f"🔥 {symbol}: LastClose=${stock.last_close:.2f}, "
                  f"SMA150=${stock.sma150:.2f} (Distance: {distance_pct:.2f}%), "
                  f"ATR14=${stock.atr:.2f} ({stock.atr_percent:.2f}%), "
                  f"Volume: {stock.last_volume:,.0f} (Avg 14d: {stock.avg_volume_14d:,.0f}, Ratio: {volume_ratio:.2f}x)")

        print(f"\n=== Watch List (Above SMA with Low Volume OR Below SMA) ===\n")
        # Sort watch list: above SMA first (by distance), then below SMA (by distance to SMA)
        sorted_watch = sorted(
            results.watch_list.items(),
            key=lambda x: (
                not x[1].above_sma,  # False (above SMA) comes before True (below SMA)
                -((x[1].last_close - x[1].sma150) / x[1].sma150 * 100) if x[1].above_sma else abs((x[1].last_close - x[1].sma150) / x[1].sma150 * 100)
            )
        )
        for symbol, stock in sorted_watch:
            distance_pct = (stock.last_close - stock.sma150) / stock.sma150 * 100
            volume_ratio = stock.last_volume / stock.avg_volume_14d
            status = "Above SMA" if stock.above_sma else "Below SMA"
            print(f"👀 {symbol}: LastClose=${stock.last_close:.2f}, "
                  f"SMA150=${stock.sma150:.2f} (Distance: {distance_pct:+.2f}%, {status}), "
                  f"ATR14=${stock.atr:.2f} ({stock.atr_percent:.2f}%), "
                  f"Volume: {stock.last_volume:,.0f} (Avg 14d: {stock.avg_volume_14d:,.0f}, Ratio: {volume_ratio:.2f}x)")

        if results.failed_tickers:
            print("\n=== Failed to fetch data for the following tickers ===")
            print(results.failed_tickers)
        else:
            print("\n✅ Successfully fetched data for all tickers!")

    @staticmethod
    def save_to_json(results: ScreenerResults, filename: str = "results.json") -> None:
        """Save screening results to JSON file for web display."""
        # Sort hot stocks by distance from SMA
        sorted_hot_stocks = sorted(
            results.hot_stocks.items(),
            key=lambda x: abs((x[1].last_close - x[1].sma150) / x[1].sma150 * 100)
        )
        
        hot_stocks_list = []
        for symbol, stock in sorted_hot_stocks:
            distance_pct = (stock.last_close - stock.sma150) / stock.sma150 * 100
            hot_stocks_list.append({
                "symbol": symbol,
                "last_close": round(stock.last_close, 2),
                "sma150": round(stock.sma150, 2),
                "distance_percent": round(distance_pct, 2),
                "atr": round(stock.atr, 2),
                "atr_percent": round(stock.atr_percent, 2),
                "last_volume": int(stock.last_volume),
                "avg_volume_14d": int(stock.avg_volume_14d),
                "volume_ratio": round(stock.last_volume / stock.avg_volume_14d, 2),
                "above_sma": stock.above_sma
            })

        # Sort watch list: above SMA first, then below SMA
        sorted_watch_list = sorted(
            results.watch_list.items(),
            key=lambda x: (
                not x[1].above_sma,
                -((x[1].last_close - x[1].sma150) / x[1].sma150 * 100) if x[1].above_sma else abs((x[1].last_close - x[1].sma150) / x[1].sma150 * 100)
            )
        )
        
        watch_list = []
        for symbol, stock in sorted_watch_list:
            distance_pct = (stock.last_close - stock.sma150) / stock.sma150 * 100
            watch_list.append({
                "symbol": symbol,
                "last_close": round(stock.last_close, 2),
                "sma150": round(stock.sma150, 2),
                "distance_percent": round(distance_pct, 2),
                "atr": round(stock.atr, 2),
                "atr_percent": round(stock.atr_percent, 2),
                "last_volume": int(stock.last_volume),
                "avg_volume_14d": int(stock.avg_volume_14d),
                "volume_ratio": round(stock.last_volume / stock.avg_volume_14d, 2),
                "above_sma": stock.above_sma
            })

        output = {
            "timestamp": datetime.now().isoformat(),
            "hot_stocks": hot_stocks_list,
            "watch_list": watch_list,
            "failed_tickers": results.failed_tickers,
            "summary": {
                "hot_stocks_count": len(hot_stocks_list),
                "watch_list_count": len(watch_list),
                "failed_count": len(results.failed_tickers),
                "total_analyzed": len(hot_stocks_list) + len(watch_list)
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to {filename}")
