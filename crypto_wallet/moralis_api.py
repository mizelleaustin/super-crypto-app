import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from moralis import evm_api
from collections import defaultdict

# Load environment variables
load_dotenv()

# API Keys
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")

class MoralisAPI:
    """Class to interact with the Moralis API for blockchain transaction data"""
    
    def __init__(self):
        self.api_key = MORALIS_API_KEY
        
        # Supported chains in Moralis
        self.chains = {
            "eth": "Ethereum",
            "goerli": "Goerli Testnet",
            "sepolia": "Sepolia Testnet",
            "polygon": "Polygon",
            "mumbai": "Mumbai Testnet",
            "bsc": "Binance Smart Chain",
            "bsc testnet": "BSC Testnet",
            "avalanche": "Avalanche",
            "avalanche testnet": "Avalanche Testnet",
            "fantom": "Fantom",
            "cronos": "Cronos",
            "palm": "Palm",
            "arbitrum": "Arbitrum",
            "arbitrum testnet": "Arbitrum Testnet",
            "optimism": "Optimism"
        }
        
        # Common token addresses for major cryptocurrencies on different chains
        self.token_addresses = {
            "ETH": {
                "eth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH contract
            },
            "BTC": {
                "eth": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
                "bsc": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",  # BTCB
                "polygon": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",  # WBTC on Polygon
                "avalanche": "0x50b7545627a5162F82A992c33b87aDc75187B218",  # WBTC.e on Avalanche
            },
            "WBTC": {
                "eth": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                "polygon": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
            },
            "USDT": {
                "eth": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "polygon": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "bsc": "0x55d398326f99059fF775485246999027B3197955",
                "avalanche": "0xc7198437980c041c805A1EDcbA50c1Ce5db95118",  # USDT.e
                "arbitrum": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
            },
            "USDC": {
                "eth": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "polygon": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "bsc": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
                "avalanche": "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664",  # USDC.e
                "arbitrum": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            },
            "LINK": {
                "eth": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
                "bsc": "0xF8A0BF9cF54Bb92F17374d9e9A321E6a111a51bD",
                "polygon": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
            },
            "UNI": {
                "eth": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
                "bsc": "0xBf5140A22578168FD562DCcF235E5D43A02ce9B1",
            },
            "AAVE": {
                "eth": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                "polygon": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
            },
            "MATIC": {
                "eth": "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",
                "polygon": "0x0000000000000000000000000000000000001010",
            },
            "SHIB": {
                "eth": "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
                "bsc": "0x2859e4544C4bB03966803b044A93563Bd2D0DD4D",
            },
            "CRO": {
                "eth": "0xA0b73E1Ff0B80914AB6fe0444E65848C4C34450b",
                "cronos": "0x0000000000000000000000000000000000000001", # Native token
            },
            "DAI": {
                "eth": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "polygon": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
                "bsc": "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3",
            },
            "SOL": {
                "eth": "0xD31a59c85aE9D8edEFeC411D448f90841571b89c", # Wrapped SOL
            },
            "AVAX": {
                "eth": "0x85f138bfEE4ef8e540890CFb48F620571d67Eda3", # Wrapped AVAX
                "avalanche": "0x0000000000000000000000000000000000000000", # Native token
            },
            "BNB": {
                "eth": "0xB8c77482e45F1F44dE1745F52C74426C631bDD52", # BNB on Ethereum
                "bsc": "0x0000000000000000000000000000000000000000", # Native token
            }
        }
        
        # Known exchange addresses (simplified list)
        self.exchange_addresses = [
            "0x742d35cc6634c0532925a3b844bc454e4438f44e",  # Binance
            "0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2",  # FTX
            "0xc098b2a3aa256d2140208c3de6543aaef5cd3a94",  # Coinbase
            "0x8d12a197cb00d4747a1fe03395095ce2a5cc6819",  # EtherDelta
            "0x2a0c0dbecc7e4d658f48e01e3fa353f44050c208",  # IDEX
        ]
    
    def find_token_address(self, token_symbol, chain="eth"):
        """Find token contract address"""
        # First check our predefined mapping
        if token_symbol in self.token_addresses and chain in self.token_addresses[token_symbol]:
            return self.token_addresses[token_symbol][chain]
            
        try:
            # Alternative method since search_token might not be available
            # For common tokens, we can use a hardcoded list
            common_tokens = {
                "BTC": {
                    "eth": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
                    "bsc": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"  # BTCB
                },
                "ETH": {
                    "bsc": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
                    "polygon": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
                },
                # Add more as needed
            }
            
            if token_symbol in common_tokens and chain in common_tokens[token_symbol]:
                return common_tokens[token_symbol][chain]
            
            # If we can't find it, return None
            print(f"Could not find address for {token_symbol} on {chain} chain")
            return None
        except Exception as e:
            print(f"Error searching for token address: {str(e)}")
            return None
    
    def get_token_metadata(self, token_address, chain="eth"):
        """Get token metadata"""
        try:
            params = {
                "addresses": [token_address],
                "chain": chain
            }
            
            result = evm_api.token.get_token_metadata(
                api_key=self.api_key,
                params=params
            )
            
            if result and len(result) > 0:
                return result[0]
            else:
                return None
        except Exception as e:
            print(f"Error getting token metadata: {str(e)}")
            return None
    
    def get_token_transfers(self, token_address, chain="eth", days=7):
        """Get token transfers for a specific token contract address"""
        try:
            # Calculate from_date based on days parameter
            from_date = datetime.now() - timedelta(days=days)
            from_timestamp = int(from_date.timestamp())  # Keep as int
            
            params = {
                "address": str(token_address),  # Ensure address is a string
                "chain": str(chain),          # Ensure chain is a string
                "from_date": int(from_timestamp)   # Pass as int
            }
            
            print(f"Fetching transfers for token {token_address} on {chain} chain...")
            
            # Try a different approach - get token transfers by contract
            try:
                result = evm_api.token.get_token_transfers(
                    api_key=self.api_key,
                    params=params
                )
                return result
            except Exception as specific_error:
                print(f"Specific error with get_token_transfers: {str(specific_error)}")
                
                # Alternative approach - try to get ERC20 transfers
                try:
                    alt_params = {
                        "address": str(token_address),
                        "chain": str(chain)
                    }
                    
                    result = evm_api.token.get_erc20_transfers(
                        api_key=self.api_key,
                        params=alt_params
                    )
                    return result
                except Exception as alt_error:
                    print(f"Alternative approach also failed: {str(alt_error)}")
                    return {"result": []}
        except Exception as e:
            print(f"Error fetching token transfers: {str(e)}")
            return {"result": []}
    
    def get_token_holders(self, token_address, chain="eth"):
        """Get current token holders for a specific token contract address"""
        try:
            params = {
                "address": token_address,
                "chain": chain
            }
            
            result = evm_api.token.get_token_holders(
                api_key=self.api_key,
                params=params
            )
            
            return result
        except Exception as e:
            print(f"Error fetching token holders: {str(e)}")
            return {"result": []}
    
    def analyze_token_transactions(self, token_symbol, chain="eth", days=7):
        """Analyze token transactions to find unique buyers and investment amounts"""
        # Find token address
        token_address = self.find_token_address(token_symbol, chain)
        
        if not token_address:
            print(f"Token address for {token_symbol} on {chain} chain not found.")
            return None
        
        print(f"Found token address: {token_address}")
        
        # Get token metadata
        token_metadata = self.get_token_metadata(token_address, chain)
        
        if not token_metadata:
            print(f"Could not fetch token metadata for {token_symbol}")
            token_name = token_symbol
            token_decimals = 18
        else:
            token_name = token_metadata.get("name", token_symbol)
            token_decimals = int(token_metadata.get("decimals", "18"))
        
        # Get token transfers
        transfers = self.get_token_transfers(token_address, chain, days)
        
        if not transfers or "result" not in transfers or not transfers["result"]:
            print(f"No transfer data found for {token_symbol} on {chain} chain.")
            return None
        
        print(f"Found {len(transfers['result'])} transfers")
        
        # Analyze transfers
        buyers = {}  # address -> total amount
        sellers = {}  # address -> total amount
        unique_addresses = set()
        total_buy_volume = 0
        total_sell_volume = 0
        
        for transfer in transfers["result"]:
            to_address = transfer.get("to_address", "").lower()
            from_address = transfer.get("from_address", "").lower()
            value = int(transfer.get("value", "0")) / (10 ** token_decimals)
            
            unique_addresses.add(to_address)
            unique_addresses.add(from_address)
            
            # Consider it a buy if receiving from an exchange or if it's not from a known exchange
            if to_address and from_address:
                if from_address in self.exchange_addresses:
                    # Definitely a buy from exchange
                    if to_address not in buyers:
                        buyers[to_address] = 0
                    buyers[to_address] += value
                    total_buy_volume += value
                elif to_address not in self.exchange_addresses:
                    # Likely a transfer between users - count as buy for receiver
                    if to_address not in buyers:
                        buyers[to_address] = 0
                    buyers[to_address] += value
                    total_buy_volume += value
                    
                    # Count as sell for sender
                    if from_address not in sellers:
                        sellers[from_address] = 0
                    sellers[from_address] += value
                    total_sell_volume += value
        
        # Prepare results
        results = {
            "token_symbol": token_symbol,
            "token_name": token_name,
            "token_address": token_address,
            "chain": chain,
            "days_analyzed": days,
            "unique_buyers": len(buyers),
            "unique_sellers": len(sellers),
            "total_unique_addresses": len(unique_addresses),
            "total_buy_volume": total_buy_volume,
            "total_sell_volume": total_sell_volume,
            "net_volume": total_buy_volume - total_sell_volume,
            "top_buyers": sorted(buyers.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_sellers": sorted(sellers.items(), key=lambda x: x[1], reverse=True)[:10],
            "buyer_distribution": self._calculate_distribution(buyers),
            "seller_distribution": self._calculate_distribution(sellers)
        }
        
        return results
    
    def _calculate_distribution(self, addresses_dict):
        """Calculate distribution of addresses by amount"""
        if not addresses_dict:
            return {}
            
        # Define amount ranges
        ranges = [
            (0, 10),
            (10, 100),
            (100, 1000),
            (1000, 10000),
            (10000, float('inf'))
        ]
        
        distribution = {f"{r[0]}-{r[1] if r[1] != float('inf') else 'inf'}": 0 for r in ranges}
        
        for _, amount in addresses_dict.items():
            for r in ranges:
                if r[0] <= amount < r[1]:
                    distribution[f"{r[0]}-{r[1] if r[1] != float('inf') else 'inf'}"] += 1
                    break
        
        return distribution


# Example usage
if __name__ == "__main__":
    api = MoralisAPI()
    
    # List supported chains
    print("Supported chains:")
    for chain_code, chain_name in api.chains.items():
        print(f"- {chain_code}: {chain_name}")
    
    # Find token address
    token_symbol = "LINK"
    chain = "eth"
    token_address = api.find_token_address(token_symbol, chain)
    print(f"\n{token_symbol} address on {chain}: {token_address}")
    
    # Get token metadata
    if token_address:
        metadata = api.get_token_metadata(token_address, chain)
        print(f"\nToken metadata: {metadata}")
        
        # Analyze token transactions
        print(f"\nAnalyzing {token_symbol} transactions...")
        results = api.analyze_token_transactions(token_symbol, chain, days=7)
        
        if results:
            print(f"\nAnalysis Results:")
            print(f"Token: {results['token_name']} ({results['token_symbol']})")
            print(f"Unique Buyers: {results['unique_buyers']}")
            print(f"Unique Sellers: {results['unique_sellers']}")
            print(f"Total Unique Addresses: {results['total_unique_addresses']}")
            print(f"Buy Volume: {results['total_buy_volume']:.2f} {token_symbol}")
            print(f"Sell Volume: {results['total_sell_volume']:.2f} {token_symbol}")
            print(f"Net Volume: {results['net_volume']:.2f} {token_symbol}")
