"""
Standalone script to generate stock-names.json: { "TICKER": "Company Full Name", ... }
Run once after cloning, or whenever new tickers are added.
Uses the same parallel approach as sector_fetcher.py (~5 min for 1400 tickers).
"""

import json
import time
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from sector_fetcher import load_tickers_from_file


def fetch_name(ticker: str) -> tuple[str, str | None]:
    try:
        info = yf.Ticker(ticker).info
        if info and isinstance(info, dict):
            name = (info.get('longName') or info.get('shortName') or
                    info.get('displayName') or info.get('name'))
            return ticker, name
    except Exception:
        pass
    return ticker, None


def main():
    tickers = load_tickers_from_file('AllStocks.txt')
    if not tickers:
        print('❌ No tickers found in AllStocks.txt')
        return

    print(f'📋 Fetching names for {len(tickers)} tickers (5 workers)...')
    names: dict[str, str] = {}
    processed = 0
    batch_size = 100

    for batch_start in range(0, len(tickers), batch_size):
        batch = tickers[batch_start:batch_start + batch_size]
        with ThreadPoolExecutor(max_workers=5) as executor:
            for ticker, name in executor.map(fetch_name, batch):
                names[ticker] = name  # None when yfinance couldn't return a name
                processed += 1
        pct = processed * 100 // len(tickers)
        print(f'   {processed}/{len(tickers)} ({pct}%)')
        if batch_start + batch_size < len(tickers):
            time.sleep(2)

    with open('stock-names.json', 'w', encoding='utf-8') as f:
        json.dump(names, f, ensure_ascii=False)

    print(f'\n✅ Saved {len(names)} names to stock-names.json')


if __name__ == '__main__':
    main()
