import importlib.util
import sys
import os
from coingecko_client import CoinGeckoClient

TOKEN_ADDRESSES_PATH = os.path.join(os.path.dirname(__file__), 'token_addresses.py')

# Dynamically import token_addresses.py as a module
def import_token_addresses():
    spec = importlib.util.spec_from_file_location("token_addresses", TOKEN_ADDRESSES_PATH)
    token_addresses = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = token_addresses
    spec.loader.exec_module(token_addresses)
    return token_addresses

def main():
    token_addresses = import_token_addresses()
    EMPTY_ADDRESSES = token_addresses.EMPTY_ADDRESSES
    FILLED_ADDRESSES = token_addresses.FILLED_ADDRESSES

    cg = CoinGeckoClient()
    coin_list = cg.get_coin_list()
    symbol_to_id = {coin['symbol'].upper(): coin['id'] for coin in coin_list}

    # Blockchains of interest
    chains = {
        'eth': 'ethereum',
        'bsc': 'binance-smart-chain',
        'polygon': 'polygon-pos'
    }

    updated = False
    for symbol, entry in EMPTY_ADDRESSES.items():
        # Skip if already filled
        if symbol in FILLED_ADDRESSES:
            continue
        coin_id = symbol_to_id.get(symbol.upper())
        if not coin_id:
            print(f"[Not found on CoinGecko] {symbol}")
            continue
        info = cg.get_coin_info(coin_id)
        if not info or 'platforms' not in info:
            print(f"[No platform info] {symbol}")
            continue
        platforms = info['platforms']
        new_entry = {}
        for chain_key, cg_chain in chains.items():
            address = platforms.get(cg_chain)
            if address and address.strip():
                new_entry[chain_key] = address
        if new_entry:
            print(f"[Filled] {symbol}: {new_entry}")
            EMPTY_ADDRESSES[symbol] = new_entry
            updated = True
        else:
            print(f"[No contract addresses found] {symbol}")

    if updated:
        # Write back to token_addresses.py (manual review recommended)
        print("\nSome addresses were filled. Please manually update token_addresses.py accordingly.")
    else:
        print("\nNo new addresses found.")

if __name__ == "__main__":
    main()
