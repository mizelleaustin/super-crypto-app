"""
coingecko_client.py - Minimal CoinGecko API client for contract address resolution
"""
import requests

class CoinGeckoClient:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.coin_list = None

    def _make_request(self, endpoint, params=None):
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, params=params)
            if response.status_code == 429:
                import time
                print("Rate limited by CoinGecko. Waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(endpoint, params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Exception when making request: {str(e)}")
            return None

    def get_coin_list(self):
        if self.coin_list is None:
            self.coin_list = self._make_request("coins/list")
        return self.coin_list

    def search_coins(self, query):
        coins = self.get_coin_list()
        if not coins:
            return []
        query = query.lower()
        matching_coins = []
        for coin in coins:
            if query in coin.get('id', '').lower() or query in coin.get('symbol', '').lower() or query in coin.get('name', '').lower():
                matching_coins.append(coin)
        return matching_coins

    def get_coin_id(self, symbol):
        coins = self.search_coins(symbol)
        if not coins:
            return None
        for coin in coins:
            if coin.get('symbol', '').lower() == symbol.lower():
                return coin.get('id')
        return coins[0].get('id')

    def get_coin_price(self, coin_id, vs_currency='usd'):
        endpoint = "simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': vs_currency,
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true'
        }
        data = self._make_request(endpoint, params)
        if data and coin_id in data:
            return data[coin_id]
        return None

    def get_historical_prices(self, coin_id, days=7, vs_currency='usd'):
        import pandas as pd
        from datetime import datetime
        endpoint = f"coins/{coin_id}/market_chart"
        params = {
            'vs_currency': vs_currency,
            'days': days,
            'interval': 'daily' if days > 1 else 'hourly'
        }
        data = self._make_request(endpoint, params)
        if not data or 'prices' not in data:
            return None
        prices = []
        for timestamp, price in data['prices']:
            date = datetime.fromtimestamp(timestamp / 1000)
            prices.append({
                'date': date,
                'price': price
            })
        df = pd.DataFrame(prices)
        return df

    def get_contract_address(self, symbol, chain):
        # Map chain to CoinGecko platform
        platform_map = {
            "eth": "ethereum",
            "bsc": "binance-smart-chain",
            "polygon": "polygon-pos"
        }
        platform = platform_map.get(chain.lower())
        if not platform:
            return None
        coin_id = self.get_coin_id(symbol)
        if not coin_id:
            return None
        resp = self._make_request(f"coins/{coin_id}")
        platforms = resp.get("platforms", {}) if resp else {}
        return platforms.get(platform)
