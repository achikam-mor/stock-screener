import json
import os
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
        
        # Helper function to load cup and handle patterns from chart file
        def load_cup_handle_patterns(symbol: str) -> list:
            chart_path = os.path.join('charts', f'{symbol}.json')
            if os.path.exists(chart_path):
                try:
                    with open(chart_path, 'r') as f:
                        chart_data = json.load(f)
                        return chart_data.get('cup_and_handle_patterns', [])
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
        
        # Generate all stocks with patterns data
        all_stocks_with_patterns = ResultsManager.generate_all_stocks_data()
        
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
            cup_handle_patterns = load_cup_handle_patterns(symbol)
            
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
                "patterns": patterns,  # Add patterns array
                "cup_handle_patterns": cup_handle_patterns  # Add cup and handle patterns
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
            cup_handle_patterns = load_cup_handle_patterns(symbol)
            
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
                "patterns": patterns,  # Add patterns array
                "cup_handle_patterns": cup_handle_patterns  # Add cup and handle patterns
            })

        output = {
            "timestamp": datetime.now().isoformat(),
            "scan_mode": scan_mode,
            "hot_stocks": hot_stocks_list,
            "watch_list": watch_list,
            "all_stocks_with_patterns": all_stocks_with_patterns,  # Add all stocks data
            "failed_tickers": results.failed_tickers,
            "filtered_by_sma": results.filtered_by_sma,
            "summary": {
                "hot_stocks_count": len(hot_stocks_list),
                "watch_list_count": len(watch_list),
                "all_stocks_count": len(all_stocks_with_patterns),  # Add count
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

    @staticmethod
    def generate_all_stocks_data():
        """
        Generate pattern data for ALL stocks by loading individual chart files.
        Returns an array of stock objects with pattern metadata.
        """
        print("\n🔍 Generating pattern detector data for all stocks...")
        
        # Load all stock symbols from stock-list.json
        all_stocks_data = []
        stock_symbols = []
        
        if os.path.exists('stock-list.json'):
            try:
                with open('stock-list.json', 'r') as f:
                    stock_list = json.load(f)
                    stock_symbols = stock_list.get('symbols', [])
            except Exception as e:
                print(f"⚠️ Could not load stock-list.json: {e}")
                return []
        
        if not stock_symbols:
            print("⚠️ No stock symbols found in stock-list.json")
            return []
        
        # Load sector data
        sectors_map = {}
        if os.path.exists('sectors.json'):
            try:
                with open('sectors.json', 'r') as f:
                    sectors_data = json.load(f)
                    # Create reverse mapping: ticker -> sector
                    for sector, tickers in sectors_data.get('sectors', {}).items():
                        for ticker in tickers:
                            sectors_map[ticker] = sector
            except Exception as e:
                print(f"⚠️ Could not load sectors.json: {e}")
        
        # Load chart data for each stock
        charts_dir = 'charts'
        if not os.path.exists(charts_dir):
            print(f"⚠️ Charts directory not found: {charts_dir}")
            return []
        
        success_count = 0
        error_count = 0
        
        for symbol in stock_symbols:
            chart_path = os.path.join(charts_dir, f'{symbol}.json')
            
            if not os.path.exists(chart_path):
                error_count += 1
                continue
            
            try:
                with open(chart_path, 'r') as f:
                    chart_data = json.load(f)
                
                # Extract required metadata
                closes = chart_data.get('close', [])
                sma150_values = chart_data.get('sma150', [])
                volumes = chart_data.get('volume', [])
                
                if not closes or not sma150_values:
                    error_count += 1
                    continue
                
                # Get last values
                last_close = closes[-1] if closes else None
                
                # Find last non-null SMA150
                last_sma150 = None
                for sma_val in reversed(sma150_values):
                    if sma_val is not None:
                        last_sma150 = sma_val
                        break
                
                if last_close is None or last_sma150 is None or last_sma150 == 0:
                    error_count += 1
                    continue
                
                # Calculate distance percentage
                distance_percent = ((last_close - last_sma150) / last_sma150) * 100
                
                # Get ATR data
                atr = chart_data.get('atr')
                atr_percent = chart_data.get('atr_percent')
                
                # Get volume data
                last_volume = chart_data.get('last_volume', volumes[-1] if volumes else 0)
                avg_volume_14d = chart_data.get('avg_volume_14d', 0)
                
                # Get pattern data
                patterns = chart_data.get('candlestick_patterns', [])
                cup_handle_patterns = chart_data.get('cup_and_handle_patterns', [])
                golden_cross = chart_data.get('golden_cross', False)
                death_cross = chart_data.get('death_cross', False)
                
                # Get sector
                sector = sectors_map.get(symbol, 'Unknown')
                
                # Create stock object
                stock_obj = {
                    "symbol": symbol,
                    "last_close": round(last_close, 2),
                    "sma150": round(last_sma150, 2),
                    "distance_percent": round(distance_percent, 2),
                    "atr": round(atr, 2) if atr is not None else None,
                    "atr_percent": round(atr_percent, 2) if atr_percent is not None else None,
                    "last_volume": int(last_volume),
                    "avg_volume_14d": int(avg_volume_14d),
                    "golden_cross": golden_cross,
                    "death_cross": death_cross,
                    "patterns": patterns,
                    "cup_handle_patterns": cup_handle_patterns,
                    "sector": sector
                }
                
                all_stocks_data.append(stock_obj)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                continue
        
        print(f"✅ Pattern detector data generated: {success_count} stocks, {error_count} errors")
        return all_stocks_data
