"""
Fetch market sentiment data including CNN Fear & Greed Index and Crypto Fear & Greed Index.
Saves data to market_data.json for frontend consumption.
"""

import json
import requests
from datetime import datetime


def fetch_cnn_fear_greed():
    """
    Fetch CNN Fear & Greed Index.
    CNN exposes their data through an API endpoint.
    """
    try:
        # CNN Fear & Greed API endpoint
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.cnn.com/markets/fear-and-greed'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract current Fear & Greed value
            if 'fear_and_greed' in data:
                fg_data = data['fear_and_greed']
                score = fg_data.get('score', None)
                rating = fg_data.get('rating', None)
                
                # Get previous close for comparison
                previous_close = fg_data.get('previous_close', None)
                
                # Get timestamp
                timestamp = fg_data.get('timestamp', None)
                
                return {
                    'score': round(score) if score else None,
                    'rating': rating,
                    'previous_close': round(previous_close) if previous_close else None,
                    'timestamp': timestamp,
                    'success': True
                }
        
        print(f"⚠️ CNN Fear & Greed API returned status {response.status_code}")
        return {'success': False, 'error': f'HTTP {response.status_code}'}
        
    except requests.exceptions.Timeout:
        print("⚠️ CNN Fear & Greed API timeout")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"⚠️ Error fetching CNN Fear & Greed: {str(e)}")
        return {'success': False, 'error': str(e)}


def fetch_crypto_fear_greed():
    """
    Fetch Crypto Fear & Greed Index from alternative.me API.
    """
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                fg_data = data['data'][0]
                return {
                    'score': int(fg_data.get('value', 0)),
                    'rating': fg_data.get('value_classification', ''),
                    'timestamp': fg_data.get('timestamp', ''),
                    'success': True
                }
        
        return {'success': False, 'error': f'HTTP {response.status_code}'}
        
    except Exception as e:
        print(f"⚠️ Error fetching Crypto Fear & Greed: {str(e)}")
        return {'success': False, 'error': str(e)}


def fetch_asset_prices():
    """
    Fetch prices for Gold, Silver, Bitcoin, and Ethereum using Yahoo Finance API.
    Symbols: GC=F (Gold Futures), SI=F (Silver Futures), BTC-USD (Bitcoin), ETH-USD (Ethereum)
    """
    assets = {
        'gold': {'symbol': 'GC=F', 'name': 'Gold'},
        'silver': {'symbol': 'SI=F', 'name': 'Silver'},
        'bitcoin': {'symbol': 'BTC-USD', 'name': 'Bitcoin'},
        'ethereum': {'symbol': 'ETH-USD', 'name': 'Ethereum'}
    }
    
    results = {}
    
    for key, asset in assets.items():
        try:
            symbol = asset['symbol']
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                chart = data.get('chart', {}).get('result', [{}])[0]
                meta = chart.get('meta', {})
                
                current_price = meta.get('regularMarketPrice', 0)
                previous_close = meta.get('previousClose', 0)
                
                # Calculate change
                change = current_price - previous_close if previous_close else 0
                change_percent = (change / previous_close * 100) if previous_close else 0
                
                results[key] = {
                    'name': asset['name'],
                    'symbol': symbol,
                    'price': round(current_price, 2),
                    'previous_close': round(previous_close, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'available': True
                }
                print(f"   ✅ {asset['name']}: ${current_price:,.2f} ({change_percent:+.2f}%)")
            else:
                results[key] = {'name': asset['name'], 'available': False, 'error': f'HTTP {response.status_code}'}
                print(f"   ⚠️ {asset['name']} failed: HTTP {response.status_code}")
                
        except Exception as e:
            results[key] = {'name': asset['name'], 'available': False, 'error': str(e)}
            print(f"   ⚠️ {asset['name']} failed: {str(e)}")
    
    return results


def get_rating_from_score(score):
    """
    Convert numeric score to rating label.
    """
    if score is None:
        return 'Unknown'
    if score <= 25:
        return 'Extreme Fear'
    elif score <= 45:
        return 'Fear'
    elif score <= 55:
        return 'Neutral'
    elif score <= 75:
        return 'Greed'
    else:
        return 'Extreme Greed'


def fetch_and_save_market_data(output_file='market_data.json'):
    """
    Fetch all market sentiment data and save to JSON file.
    """
    print("📊 Fetching market sentiment data...")
    
    # Fetch CNN Fear & Greed
    print("   Fetching CNN Fear & Greed Index...")
    cnn_data = fetch_cnn_fear_greed()
    if cnn_data.get('success'):
        print(f"   ✅ CNN Fear & Greed: {cnn_data.get('score')} ({cnn_data.get('rating')})")
    else:
        print(f"   ⚠️ CNN Fear & Greed failed: {cnn_data.get('error')}")
    
    # Fetch Crypto Fear & Greed
    print("   Fetching Crypto Fear & Greed Index...")
    crypto_data = fetch_crypto_fear_greed()
    if crypto_data.get('success'):
        print(f"   ✅ Crypto Fear & Greed: {crypto_data.get('score')} ({crypto_data.get('rating')})")
    else:
        print(f"   ⚠️ Crypto Fear & Greed failed: {crypto_data.get('error')}")
    
    # Fetch Asset Prices (Gold, Silver, Bitcoin, Ethereum)
    print("   Fetching asset prices (Gold, Silver, Bitcoin, Ethereum)...")
    asset_prices = fetch_asset_prices()
    
    # Compile market data
    market_data = {
        'cnn_fear_greed': {
            'score': cnn_data.get('score'),
            'rating': cnn_data.get('rating') or get_rating_from_score(cnn_data.get('score')),
            'previous_close': cnn_data.get('previous_close'),
            'available': cnn_data.get('success', False)
        },
        'crypto_fear_greed': {
            'score': crypto_data.get('score'),
            'rating': crypto_data.get('rating'),
            'available': crypto_data.get('success', False)
        },
        'assets': asset_prices,
        'last_updated': datetime.now().isoformat()
    }
    
    # Save to JSON file
    with open(output_file, 'w') as f:
        json.dump(market_data, f, indent=2)
    
    print(f"✅ Market data saved to {output_file}")
    return market_data


if __name__ == "__main__":
    fetch_and_save_market_data()
