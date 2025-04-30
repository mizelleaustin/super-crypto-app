"""
address_lookup.py - Unified token address resolution logic for your dashboard
"""
import os
from token_addresses import TOKEN_ADDRESSES, EMPTY_ADDRESSES

class AddressResolver:
    def __init__(self, coingecko_client, moralis_client):
        self.coingecko = coingecko_client
        self.moralis = moralis_client
        self.local_addresses = TOKEN_ADDRESSES

    def get_token_address(self, symbol, chain):
        symbol = symbol.upper()
        chain = chain.lower()
        # 1. Try local mapping
        if symbol in self.local_addresses and chain in self.local_addresses[symbol]:
            return self.local_addresses[symbol][chain]
        # 2. Try CoinGecko
        try:
            address = self.coingecko.get_contract_address(symbol, chain)
            if address:
                return address
        except Exception as e:
            print(f"CoinGecko lookup failed for {symbol} on {chain}: {e}")
        # 3. Try Moralis (EVM only)
        try:
            if chain in ["eth", "bsc", "polygon"]:
                address = self.moralis.get_contract_address(symbol, chain)
                if address:
                    return address
        except Exception as e:
            print(f"Moralis lookup failed for {symbol} on {chain}: {e}")
        # Not found
        print(f"No contract address found for {symbol} on {chain}.")
        return None
