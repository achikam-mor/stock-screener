"""
Fetch sector and industry data for all stocks from Yahoo Finance.
Saves data to sectors.json and industries.json for frontend filtering.
Run manually via GitHub Actions workflow every ~4 months.
"""

import json
import time
import yfinance as yf
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed


def load_tickers_from_file(filepath: str) -> list:
    """Load tickers from a text file. Handles both list format and one-per-line format."""
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
        
        # Check if content is a Python list format (starts with [ and ends with ])
        if content.startswith('[') and content.endswith(']'):
            # Parse as Python list
            try:
                tickers = eval(content)  # Safe since it's our own file
                return [t.strip().upper() for t in tickers if t.strip()]
            except:
                pass
        
        # Otherwise, try to parse as comma-separated with quotes
        # Remove brackets if present
        content = content.strip('[]')
        # Split by comma and clean up quotes/whitespace
        tickers = []
        for item in content.replace('\n', ',').split(','):
            # Remove quotes and whitespace
            ticker = item.strip().strip("'\"").strip()
            if ticker:
                tickers.append(ticker.upper())
        
        return tickers
    except FileNotFoundError:
        print(f"⚠️ File not found: {filepath}")
        return []


def fetch_single_stock_info(ticker: str) -> dict:
    """
    Fetch sector and industry info for a single stock using yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Try to get info
        try:
            info = stock.info
            if info and isinstance(info, dict):
                sector = info.get('sector')
                industry = info.get('industry')
                
                # Check if we got valid data
                if sector or industry:
                    return {
                        'ticker': ticker,
                        'sector': sector if sector else None,
                        'industry': industry if industry else None,
                        'success': True
                    }
        except Exception as e:
            pass
        
        # No data found
        return {
            'ticker': ticker,
            'sector': None,
            'industry': None,
            'success': False
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'sector': None,
            'industry': None,
            'success': False
        }


def fetch_all_sectors_and_industries(tickers: list, max_workers: int = 5):
    """
    Fetch sector and industry data for all tickers using parallel processing.
    
    Args:
        tickers: List of stock tickers
        max_workers: Number of parallel threads
    
    Returns:
        Tuple of (sectors_data, industries_data)
    """
    # Data structures for sectors
    sectors_by_name = defaultdict(list)
    stocks_by_sector = {}
    
    # Data structures for industries
    industries_by_name = defaultdict(list)
    stocks_by_industry = {}
    
    total = len(tickers)
    success_count = 0
    failed_count = 0
    processed = 0
    
    print(f"📊 Fetching sector/industry data for {total} stocks...")
    print(f"   Using {max_workers} parallel workers")
    
    # Process in batches
    batch_size = 100
    
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch_tickers = tickers[batch_start:batch_end]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {
                executor.submit(fetch_single_stock_info, ticker): ticker 
                for ticker in batch_tickers
            }
            
            for future in as_completed(future_to_ticker):
                result = future.result()
                ticker = result['ticker']
                sector = result['sector']
                industry = result['industry']
                
                if sector:
                    sectors_by_name[sector].append(ticker)
                    stocks_by_sector[ticker] = sector
                    success_count += 1
                else:
                    sectors_by_name['Other'].append(ticker)
                    stocks_by_sector[ticker] = 'Other'
                    if not industry:
                        failed_count += 1
                
                if industry:
                    industries_by_name[industry].append(ticker)
                    stocks_by_industry[ticker] = industry
                else:
                    industries_by_name['Other'].append(ticker)
                    stocks_by_industry[ticker] = 'Other'
                
                processed += 1
        
        print(f"   Progress: {processed}/{total} ({processed*100//total}%) - Success: {success_count}, Failed: {failed_count}")
        
        if batch_end < total:
            time.sleep(2)
    
    print(f"\n✅ Completed: {success_count} successful, {failed_count} without data")
    
    sectors_data = {
        'sectors': {k: sorted(v) for k, v in sorted(sectors_by_name.items())},
        'stocks': dict(sorted(stocks_by_sector.items())),
        'sector_list': sorted(sectors_by_name.keys()),
        'last_updated': datetime.now().isoformat(),
        'total_stocks': total,
        'success_count': success_count
    }
    
    industries_data = {
        'industries': {k: sorted(v) for k, v in sorted(industries_by_name.items())},
        'stocks': dict(sorted(stocks_by_industry.items())),
        'industry_list': sorted(industries_by_name.keys()),
        'last_updated': datetime.now().isoformat(),
        'total_stocks': total,
        'success_count': success_count
    }
    
    return sectors_data, industries_data


def save_to_json(data: dict, filepath: str):
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved to {filepath}")


def main():
    """Main function to fetch and save sector/industry data."""
    print("=" * 60)
    print("🏢 Stock Sector and Industry Fetcher")
    print("=" * 60)
    
    tickers = load_tickers_from_file("AllStocks.txt")
    
    if not tickers:
        print("❌ No tickers found in AllStocks.txt")
        return
    
    print(f"📋 Loaded {len(tickers)} tickers from AllStocks.txt")
    
    sectors_data, industries_data = fetch_all_sectors_and_industries(
        tickers, 
        max_workers=5
    )
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    print(f"\nSectors ({len(sectors_data['sector_list'])} total):")
    for sector in sectors_data['sector_list']:
        count = len(sectors_data['sectors'][sector])
        print(f"   {sector}: {count} stocks")
    
    print(f"\nIndustries: {len(industries_data['industry_list'])} unique industries")
    
    print("\n" + "=" * 60)
    save_to_json(sectors_data, "sectors.json")
    save_to_json(industries_data, "industries.json")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
