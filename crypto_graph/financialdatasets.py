import requests

def fetch_crypto_prices(ticker, interval="day", interval_multiplier=1, start_date="2025-03-01", end_date="2025-03-18"):
    headers = {"X-API-KEY": FIN_API_KEY}
    params = {
        "ticker": ticker,
        "interval": interval,
        "interval_multiplier": interval_multiplier,
        "start_date": start_date,
        "end_date": end_date
    }
    url = "https://api.financialdatasets.ai/crypto/prices/"
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json().get("prices", [])
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None
