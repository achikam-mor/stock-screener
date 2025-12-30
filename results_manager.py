import json
from datetime import datetime
from models import ScreenerResults

class ResultsManager:
    @staticmethod
    def print_results(results: ScreenerResults) -> None:
        print("\n=== Hot Stocks (Last Close above SMA150) ===\n")
        # Sort hot stocks by distance from SMA and ATR
        sorted_stocks = sorted(
            results.hot_stocks.items(),
            key=lambda x: (
                abs((x[1].last_close - x[1].sma150) / x[1].sma150 * 100),  # Distance from SMA as percentage
                x[1].atr  # ATR as tiebreaker
            )
        )
        for symbol, stock in sorted_stocks:
            distance_pct = (stock.last_close - stock.sma150) / stock.sma150 * 100
            volume_ratio = stock.last_volume / stock.avg_volume_14d if stock.avg_volume_14d > 0 else 0
            print(f"🔥 {symbol}: LastClose=${stock.last_close:.2f}, "
                  f"SMA150=${stock.sma150:.2f} (Distance: {distance_pct:.2f}%), "
                  f"ATR14=${stock.atr:.2f} ({stock.atr_percent:.2f}%), "
                  f"Volume: {stock.last_volume:,.0f} (Avg 14d: {stock.avg_volume_14d:,.0f}, Ratio: {volume_ratio:.2f}x)")

        print(f"\n=== Watch List (Last Close below SMA150) ===\n")
        # Sort watch list by distance from SMA (same as hot stocks)
        sorted_watch_list = sorted(
            results.watch_list.items(),
            key=lambda x: (
                abs((x[1].last_close - x[1].sma150) / x[1].sma150 * 100),  # Distance from SMA as percentage
                x[1].atr  # ATR as tiebreaker
            )
        )
        for symbol, stock in sorted_watch_list:
            volume_ratio = stock.last_volume / stock.avg_volume_14d if stock.avg_volume_14d > 0 else 0
            print(f"👀 {symbol}: LastClose=${stock.last_close:.2f}, "
                  f"SMA150=${stock.sma150:.2f}, "
                  f"ATR14=${stock.atr:.2f} ({stock.atr_percent:.2f}%), "
                  f"Volume: {stock.last_volume:,.0f} (Avg 14d: {stock.avg_volume_14d:,.0f}, Ratio: {volume_ratio:.2f}x)")

        if results.failed_tickers:
            print("\n=== Failed to fetch data for the following tickers ===")
            print(results.failed_tickers)
        else:
            print("\n✅ Successfully fetched data for all tickers!")

        if results.filtered_by_sma:
            print(f"\n=== Filtered by SMA conditions ({len(results.filtered_by_sma)} tickers) ===")
            print(results.filtered_by_sma)

    @staticmethod
    def save_to_json(results: ScreenerResults, total_tickers: int, filename: str = "results.json", scan_mode: str = "all") -> None:
        """Save screening results to JSON file for web display."""
        import os
        
        # Helper function to load candlestick patterns from chart file
        def load_patterns(symbol: str) -> list:
            chart_path = os.path.join('charts', f'{symbol}.json')
            if os.path.exists(chart_path):
                try:
                    with open(chart_path, 'r') as f:
                        chart_data = json.load(f)
                        return chart_data.get('candlestick_patterns', [])
                except:
                    pass
            return []
        
        # Initialize pattern summary counters
        pattern_summary = {
            "bullish_confirmed": 0,
            "pending_bullish": 0,
            "pending_bearish": 0,
            "bearish_confirmed": 0
        }
        
        # Sort hot stocks by distance from SMA
        sorted_hot_stocks = sorted(
            results.hot_stocks.items(),
            key=lambda x: abs((x[1].last_close - x[1].sma150) / x[1].sma150 * 100)
        )
        
        hot_stocks_list = []
        for symbol, stock in sorted_hot_stocks:
            distance_pct = (stock.last_close - stock.sma150) / stock.sma150 * 100
            
            # Load candlestick patterns for this stock
            patterns = load_patterns(symbol)
            
            # Update pattern summary counts
            for pattern in patterns:
                signal = pattern.get('signal', '')
                status = pattern.get('status', '')
                if signal == 'bullish' and status == 'confirmed':
                    pattern_summary['bullish_confirmed'] += 1
                elif signal == 'bullish' and status == 'pending':
                    pattern_summary['pending_bullish'] += 1
                elif signal == 'bearish' and status == 'pending':
                    pattern_summary['pending_bearish'] += 1
                elif signal == 'bearish' and status == 'confirmed':
                    pattern_summary['bearish_confirmed'] += 1
            
            hot_stocks_list.append({
                "symbol": symbol,
                "last_close": round(stock.last_close, 2),
                "sma150": round(stock.sma150, 2),
                "distance_percent": round(distance_pct, 2),
                "atr": round(stock.atr, 2),
                "atr_percent": round(stock.atr_percent, 2),
                "last_volume": int(stock.last_volume),
                "avg_volume_14d": int(stock.avg_volume_14d),
                "golden_cross": stock.golden_cross,
                "death_cross": stock.death_cross,
                "patterns": patterns  # Add patterns array
            })

        # Sort watch list by distance from SMA (same as hot stocks)
        sorted_watch_list = sorted(
            results.watch_list.items(),
            key=lambda x: abs((x[1].last_close - x[1].sma150) / x[1].sma150 * 100)
        )
        
        watch_list = []
        for symbol, stock in sorted_watch_list:
            distance_pct = (stock.last_close - stock.sma150) / stock.sma150 * 100
            
            # Load candlestick patterns for this stock
            patterns = load_patterns(symbol)
            
            # Update pattern summary counts
            for pattern in patterns:
                signal = pattern.get('signal', '')
                status = pattern.get('status', '')
                if signal == 'bullish' and status == 'confirmed':
                    pattern_summary['bullish_confirmed'] += 1
                elif signal == 'bullish' and status == 'pending':
                    pattern_summary['pending_bullish'] += 1
                elif signal == 'bearish' and status == 'pending':
                    pattern_summary['pending_bearish'] += 1
                elif signal == 'bearish' and status == 'confirmed':
                    pattern_summary['bearish_confirmed'] += 1
            
            watch_list.append({
                "symbol": symbol,
                "last_close": round(stock.last_close, 2),
                "sma150": round(stock.sma150, 2),
                "distance_percent": round(distance_pct, 2),
                "atr": round(stock.atr, 2),
                "atr_percent": round(stock.atr_percent, 2),
                "last_volume": int(stock.last_volume),
                "avg_volume_14d": int(stock.avg_volume_14d),
                "golden_cross": stock.golden_cross,
                "death_cross": stock.death_cross,
                "patterns": patterns  # Add patterns array
            })

        output = {
            "timestamp": datetime.now().isoformat(),
            "scan_mode": scan_mode,
            "hot_stocks": hot_stocks_list,
            "watch_list": watch_list,
            "failed_tickers": results.failed_tickers,
            "filtered_by_sma": results.filtered_by_sma,
            "summary": {
                "hot_stocks_count": len(hot_stocks_list),
                "watch_list_count": len(watch_list),
                "failed_count": len(results.failed_tickers),
                "filtered_by_sma_count": len(results.filtered_by_sma),
                "total_analyzed": total_tickers
            },
            "pattern_summary": pattern_summary  # Add pattern summary
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to {filename}")
        
        # Log pattern summary
        total_patterns = sum(pattern_summary.values())
        if total_patterns > 0:
            print(f"🕯️ Pattern Summary:")
            print(f"   Bullish Confirmed: {pattern_summary['bullish_confirmed']}")
            print(f"   Pending Bullish: {pattern_summary['pending_bullish']}")
            print(f"   Pending Bearish: {pattern_summary['pending_bearish']}")
            print(f"   Bearish Confirmed: {pattern_summary['bearish_confirmed']}")
