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


def load_tickers_from_file(filepath: str) -> list:
    """Load tickers from a text file (one per line)."""
    try:
        with open(filepath, 'r') as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
        return tickers
    except FileNotFoundError:
        print(f"⚠️ File not found: {filepath}")
        return []


def fetch_stock_info(ticker: str, retries: int = 3) -> dict:
    """
    Fetch sector and industry info for a single stock.
    Returns dict with sector and industry, or None values if not available.
    """
    for attempt in range(retries):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            sector = info.get('sector', None)
            industry = info.get('industry', None)
            
            return {
                'sector': sector,
                'industry': industry
            }
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)  # Wait before retry
            else:
                print(f"⚠️ Failed to fetch {ticker} after {retries} attempts: {str(e)}")
                return {'sector': None, 'industry': None}
    
    return {'sector': None, 'industry': None}


def fetch_all_sectors_and_industries(tickers: list, batch_size: int = 50, delay: float = 0.5):
    """
    Fetch sector and industry data for all tickers.
    Uses batching and delays to avoid rate limiting.
    
    Args:
        tickers: List of stock tickers
        batch_size: Number of stocks to process before a longer pause
        delay: Delay between each API call in seconds
    
    Returns:
        Tuple of (sectors_data, industries_data)
    """
    # Data structures for sectors
    sectors_by_name = defaultdict(list)  # sector -> [tickers]
    stocks_by_sector = {}  # ticker -> sector
    
    # Data structures for industries
    industries_by_name = defaultdict(list)  # industry -> [tickers]
    stocks_by_industry = {}  # ticker -> industry
    
    total = len(tickers)
    success_count = 0
    failed_count = 0
    
    print(f"📊 Fetching sector/industry data for {total} stocks...")
    print(f"   Estimated time: ~{(total * delay) / 60:.1f} minutes")
    
    for i, ticker in enumerate(tickers):
        # Progress update every 50 stocks
        if i > 0 and i % 50 == 0:
            print(f"   Progress: {i}/{total} ({i*100//total}%) - Success: {success_count}, Failed: {failed_count}")
        
        # Fetch stock info
        info = fetch_stock_info(ticker)
        
        sector = info['sector']
        industry = info['industry']
        
        # Handle sector
        if sector:
            sectors_by_name[sector].append(ticker)
            stocks_by_sector[ticker] = sector
            success_count += 1
        else:
            sectors_by_name['Other'].append(ticker)
            stocks_by_sector[ticker] = 'Other'
            if not industry:  # Only count as failed if both are missing
                failed_count += 1
        
        # Handle industry
        if industry:
            industries_by_name[industry].append(ticker)
            stocks_by_industry[ticker] = industry
        else:
            industries_by_name['Other'].append(ticker)
            stocks_by_industry[ticker] = 'Other'
        
        # Rate limiting
        time.sleep(delay)
        
        # Longer pause every batch_size stocks
        if (i + 1) % batch_size == 0 and i < total - 1:
            print(f"   Batch {(i+1)//batch_size} complete, pausing...")
            time.sleep(2)
    
    print(f"\n✅ Completed: {success_count} successful, {failed_count} without data")
    
    # Sort tickers within each sector/industry
    sectors_data = {
        'sectors': {k: sorted(v) for k, v in sorted(sectors_by_name.items())},
        'stocks': dict(sorted(stocks_by_sector.items())),
        'sector_list': sorted(sectors_by_name.keys()),
        'last_updated': datetime.now().isoformat(),
        'total_stocks': total
    }
    
    industries_data = {
        'industries': {k: sorted(v) for k, v in sorted(industries_by_name.items())},
        'stocks': dict(sorted(stocks_by_industry.items())),
        'industry_list': sorted(industries_by_name.keys()),
        'last_updated': datetime.now().isoformat(),
        'total_stocks': total
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
    
    # Load tickers
    tickers = load_tickers_from_file("AllStocks.txt")
    
    if not tickers:
        print("❌ No tickers found in AllStocks.txt")
        return
    
    print(f"📋 Loaded {len(tickers)} tickers from AllStocks.txt")
    
    # Fetch data
    sectors_data, industries_data = fetch_all_sectors_and_industries(
        tickers, 
        batch_size=50, 
        delay=0.3  # 0.3 seconds between calls
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    print(f"\nSectors ({len(sectors_data['sector_list'])} total):")
    for sector in sectors_data['sector_list']:
        count = len(sectors_data['sectors'][sector])
        print(f"   {sector}: {count} stocks")
    
    print(f"\nIndustries: {len(industries_data['industry_list'])} unique industries")
    
    # Save to files
    print("\n" + "=" * 60)
    save_to_json(sectors_data, "sectors.json")
    save_to_json(industries_data, "industries.json")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
