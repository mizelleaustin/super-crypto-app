import os
import pandas as pd
import matplotlib.pyplot as plt
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Moralis SDK
try:
    from moralis import evm_api
    MORALIS_SDK_AVAILABLE = True
    print("Moralis SDK imported successfully")
except ImportError:
    print("Moralis SDK not found. Some functionality may be limited.")
    MORALIS_SDK_AVAILABLE = False

# Import our custom CoinGeckoAPI implementation
try:
    from coingecko_client import CoinGeckoClient
    USE_COINGECKO_MODULE = True
    print("Successfully imported CoinGeckoAPI from coingecko_api.py")
except ImportError:
    print("CoinGeckoAPI module not found. Using direct API calls instead.")
    USE_COINGECKO_MODULE = False

class CryptoAnalyzer:
    """Main class that combines CoinGecko and Moralis APIs for comprehensive crypto analysis"""
    
    def __init__(self, moralis_api_key=None):
        # Set up Moralis API key
        self.moralis_api_key = moralis_api_key or os.getenv("MORALIS_API_KEY")
        if not self.moralis_api_key:
            raise ValueError("Moralis API key not found. Please check your .env file.")
            
        # Create output directory if it doesn't exist
        self.output_dir = "output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Initialize CoinGecko API if module is available
        if USE_COINGECKO_MODULE:
            self.coingecko = CoinGeckoClient()
            
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
        
        # Common token mappings between CoinGecko IDs and symbols
        self.token_mappings = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "USDC": "usd-coin",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "ADA": "cardano",
            "SOL": "solana",
            "DOGE": "dogecoin",
            "MATIC": "matic-network",
            "DOT": "polkadot",
            "DAI": "dai",
            "SHIB": "shiba-inu",
            "AVAX": "avalanche-2",
            "UNI": "uniswap",
            "LINK": "chainlink",
            "LTC": "litecoin",
            "ATOM": "cosmos",
            "XLM": "stellar",
            "NEAR": "near",
            "ALGO": "algorand",
            "ICP": "internet-computer",
            "FIL": "filecoin",
            "APE": "apecoin",
            "MANA": "decentraland",
            "SAND": "the-sandbox",
            "AXS": "axie-infinity",
            "AAVE": "aave"
        }
        
        # Common token addresses for major cryptocurrencies on different chains
        self.token_addresses = {
            "ETH": {
                "eth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH contract
            },
            "USDT": {
                "eth": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "polygon": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "bsc": "0x55d398326f99059fF775485246999027B3197955",
            },
            "USDC": {
                "eth": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "polygon": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "bsc": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
            },
            "BTC": {
                "eth": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC on Ethereum
            }
        }
    
    def get_coin_id(self, token_symbol):
        """Get CoinGecko coin ID from token symbol"""
        # First check our mapping
        if token_symbol.upper() in self.token_mappings:
            return self.token_mappings[token_symbol.upper()]
        
        # If CoinGecko module is available, use it
        if USE_COINGECKO_MODULE:
            try:
                return self.coingecko.get_coin_id(token_symbol)
            except Exception as e:
                print(f"Error using CoinGeckoAPI module: {str(e)}")
                # Fall back to direct API call
        
        # If not in mapping or module failed, try to search CoinGecko directly
        try:
            url = "https://api.coingecko.com/api/v3/coins/list"
            response = requests.get(url)
            if response.status_code == 200:
                coins = response.json()
                for coin in coins:
                    if coin["symbol"].lower() == token_symbol.lower():
                        return coin["id"]
            return None
        except Exception as e:
            print(f"Error searching for coin: {str(e)}")
            return None
    
    def get_token_price(self, coin_id):
        """Get current token price from CoinGecko"""
        # If CoinGecko module is available, use it
        if USE_COINGECKO_MODULE:
            try:
                return self.coingecko.get_coin_price(coin_id)
            except Exception as e:
                print(f"Error using CoinGeckoAPI module: {str(e)}")
                # Fall back to direct API call
        
        # Direct API call as fallback
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
            response = requests.get(url)
            
            # Check if we're being rate limited
            if response.status_code == 429:
                print("Rate limited by CoinGecko. Waiting 60 seconds...")
                time.sleep(60)
                return self.get_token_price(coin_id)
                
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    return data[coin_id]
            return None
        except Exception as e:
            print(f"Error getting token price: {str(e)}")
            return None
    
    def get_historical_prices(self, coin_id, days=30):
        """Get historical price data from CoinGecko"""
        # If CoinGecko module is available, use it
        if USE_COINGECKO_MODULE:
            try:
                return self.coingecko.get_historical_prices(coin_id, days)
            except Exception as e:
                print(f"Error using CoinGeckoAPI module: {str(e)}")
                # Fall back to direct API call
        
        # Direct API call as fallback
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
            response = requests.get(url)
            
            # Check if we're being rate limited
            if response.status_code == 429:
                print("Rate limited by CoinGecko. Waiting 60 seconds...")
                time.sleep(60)
                return self.get_historical_prices(coin_id, days)
                
            if response.status_code == 200:
                data = response.json()
                # Convert to DataFrame
                prices = []
                for timestamp, price in data.get("prices", []):
                    date = datetime.fromtimestamp(timestamp/1000)
                    prices.append({"date": date, "price": price})
                return pd.DataFrame(prices)
            return None
        except Exception as e:
            print(f"Error getting historical prices: {str(e)}")
            return None

    def plot_historical_price(self, token_symbol, days=30):
        """Fetch and plot historical price data for a token symbol using CoinGecko."""
        coin_id = self.get_coin_id(token_symbol)
        if not coin_id:
            print(f"Could not resolve CoinGecko ID for symbol: {token_symbol}")
            return
        df = self.get_historical_prices(coin_id, days)
        if df is None or df.empty:
            print(f"No historical price data available for {token_symbol}")
            return
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['price'], label=f"{token_symbol.upper()} Price (USD)")
        plt.title(f"{token_symbol.upper()} Price History - Last {days} Days")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        filename = f"{token_symbol.upper()}_price_history.png"
        plt.savefig(filename)
        plt.show()
        print(f"Plot saved as {filename}")
    
    def get_token_transfers(self, token_address, chain="eth", days=30, max_transfers=500):
        """Get token transfers from Moralis API"""
        if not token_address:
            print("Token address is required")
            return None
            
        if not MORALIS_SDK_AVAILABLE:
            print("Moralis SDK is not available. Cannot fetch token transfers.")
            return None
            
        # Validate days parameter
        try:
            days = int(days)
            if days <= 0:
                print("Days parameter must be a positive integer. Using default (30).")
                days = 30
        except (ValueError, TypeError):
            print(f"Invalid days parameter: {days}. Using default (30).")
            days = 30
            
        try:
            # Calculate from_date based on days parameter
            from_date = datetime.now() - timedelta(days=days)
            from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            to_date_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
            print(f"Analyzing token with address {token_address} on chain {chain}")
            print(f"Fetching transfers for the past {days} days (up to {max_transfers} transfers)...")
            print(f"Date range: {from_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
            
            # The API has a limit of 100 transfers per request, so we'll use pagination
            all_transfers = []
            cursor = None
            total_fetched = 0
            page = 1
            
            while total_fetched < max_transfers:
                params = {
                    "address": str(token_address),
                    "chain": str(chain),
                    "from_date": int(datetime.strptime(from_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()),
                    "to_date": int(datetime.strptime(to_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()),
                    "limit": 100  # Max allowed by API
                }
                
                if cursor:
                    params["cursor"] = cursor
                
                print(f"Fetching page {page} of transfers...")
                try:
                    result = evm_api.token.get_token_transfers(
                        api_key=self.moralis_api_key,
                        params=params
                    )
                except Exception as e:
                    print(f"Error in Moralis API call: {str(e)}")
                    break
                
                if not result or not result.get("result") or len(result["result"]) == 0:
                    print("No more transfers found.")
                    break
                
                current_batch = len(result["result"])
                all_transfers.extend(result["result"])
                total_fetched += current_batch
                
                print(f"Retrieved {current_batch} transfers (total: {total_fetched})")
                
                cursor = result.get("cursor")
                if not cursor:
                    print("No more pages available.")
                    break
                    
                page += 1
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
            
            print(f"Total transfers fetched: {len(all_transfers)}")
            return all_transfers
        except Exception as e:
            print(f"Error fetching token transfers: {str(e)}")
            return None
    
    def determine_best_chain(self, token_symbol):
        """Determine the best blockchain for a given token symbol"""
        token_symbol = token_symbol.upper()
        
        # Check if token exists in our token_addresses mapping
        if token_symbol in self.token_addresses:
            # If it exists on multiple chains, prioritize them in this order
            for chain in ["eth", "bsc", "polygon"]:
                if chain in self.token_addresses[token_symbol]:
                    return chain
        
        # Default to Ethereum if we can't determine
        return "eth"
    
    def get_token_address(self, token_symbol, chain=None):
        """Get token address from symbol and chain"""
        token_symbol = token_symbol.upper()
        
        # If chain is not specified, determine the best chain
        if not chain:
            chain = self.determine_best_chain(token_symbol)
            print(f"Using {chain} blockchain for {token_symbol}")
        
        # Check if we have this token address in our mapping
        if token_symbol in self.token_addresses and chain in self.token_addresses[token_symbol]:
            return self.token_addresses[token_symbol][chain]
            
        # If not in our mapping, try to search for it using Moralis
        try:
            # This is a placeholder - the actual implementation would depend on
            # what Moralis functions are available in your SDK version
            print(f"Token address for {token_symbol} on {chain} not found in local database.")
            print("Searching for token address is not implemented in this version.")
            return None
        except Exception as e:
            print(f"Error searching for token address: {str(e)}")
            return None
    
    def analyze_token_transfers(self, transfers):
        """Analyze token transfers to get transaction data"""
        if not transfers:
            return None
            
        print(f"Analyzing {len(transfers)} token transfers...")
        
        # Basic transaction analysis
        transaction_data = {
            'total_transfers': len(transfers),
            'unique_senders': set(),
            'unique_receivers': set(),
            'total_volume': 0,
            'buy_volume': 0,
            'sell_volume': 0,
            'buyer_distribution': {},
            'top_buyers': []
        }
        
        # Process each transfer
        for transfer in transfers:
            sender = transfer.get('from_address')
            receiver = transfer.get('to_address')
            value = float(transfer.get('value', 0)) / (10 ** int(transfer.get('decimals', 18)))
            
            transaction_data['unique_senders'].add(sender)
            transaction_data['unique_receivers'].add(receiver)
            transaction_data['total_volume'] += value
            
            # Categorize as buy or sell (simplified)
            if sender == '0x0000000000000000000000000000000000000000':
                # Minting event
                transaction_data['buy_volume'] += value
            elif receiver == '0x0000000000000000000000000000000000000000':
                # Burning event
                transaction_data['sell_volume'] += value
            else:
                # Regular transfer
                transaction_data['buy_volume'] += value
                
            # Categorize buyers by purchase amount
            if value > 0:
                if value < 10:
                    bucket = '< 10'
                elif value < 100:
                    bucket = '10-100'
                elif value < 1000:
                    bucket = '100-1000'
                else:
                    bucket = '> 1000'
                    
                if bucket in transaction_data['buyer_distribution']:
                    transaction_data['buyer_distribution'][bucket] += 1
                else:
                    transaction_data['buyer_distribution'][bucket] = 1
        
        # Convert sets to counts
        unique_senders = len(transaction_data['unique_senders'])
        unique_receivers = len(transaction_data['unique_receivers'])
        transaction_data['unique_senders'] = unique_senders
        transaction_data['unique_receivers'] = unique_receivers
        
        # Add additional fields needed for visualization
        transaction_data['unique_buyers'] = unique_receivers  # Simplification: receivers are buyers
        transaction_data['unique_sellers'] = unique_senders  # Simplification: senders are sellers
        transaction_data['total_unique_addresses'] = len(transaction_data['unique_senders'].union(transaction_data['unique_receivers']))
        transaction_data['total_buy_volume'] = transaction_data['buy_volume']
        transaction_data['total_sell_volume'] = transaction_data['sell_volume']
        transaction_data['net_volume'] = transaction_data['buy_volume'] - transaction_data['sell_volume']
        
        print(f"Analysis complete. Found {unique_senders} unique senders and {unique_receivers} unique receivers.")
        return transaction_data
        
    def analyze_token(self, token_symbol, chain=None, days=30):
        """Analyze a token using both price and transaction data"""
        # Validate days parameter
        try:
            days = int(days)
            if days <= 0:
                print("Days parameter must be a positive integer. Using default (30).")
                days = 30
        except (ValueError, TypeError):
            print(f"Invalid days parameter: {days}. Using default (30).")
            days = 30
            
        # If chain is not specified, determine the best chain
        if not chain:
            chain = self.determine_best_chain(token_symbol)
            print(f"Using {chain} blockchain for {token_symbol}")
            
        print(f"Analyzing {token_symbol} over the past {days} days...")
        
        # Get coin ID from CoinGecko
        coin_id = self.get_coin_id(token_symbol)
        
        if not coin_id:
            print(f"Could not find {token_symbol} on CoinGecko")
            price_data = None
            historical_prices = None
        else:
            print(f"Found coin ID: {coin_id}")
            
            # Get price data
            price_data = self.get_token_price(coin_id)
            
            # Get historical prices
            historical_prices = self.get_historical_prices(coin_id, days)
        
        # Get token address
        token_address = self.get_token_address(token_symbol, chain)
        if not token_address:
            print(f"Could not find token address for {token_symbol} on {chain}")
            transaction_data = None
        else:
            # Get transaction data from Moralis
            transfers = self.get_token_transfers(token_address, chain, days)
            if not transfers:
                print(f"No transfers found for {token_symbol} on {chain}")
                transaction_data = None
            else:
                # Process transfers to get transaction data
                transaction_data = self.analyze_token_transfers(transfers)
        
        # Combine results
        results = {
            "token_symbol": token_symbol,
            "chain": chain,
            "days_analyzed": days,
            "price_data": price_data,
            "historical_prices": historical_prices,
            "transaction_data": transaction_data
        }
        
        # Print summary of analysis
        print(f"\nAnalysis Summary for {token_symbol}:")
        print(f"Chain: {chain}")
        print(f"Period: Last {days} days")
        
        if price_data:
            if isinstance(price_data, dict) and 'usd' in price_data:
                print(f"Current Price: ${price_data['usd']:.2f} USD")
            else:
                print(f"Current Price: {price_data}")
        else:
            print("Price data: Not available")
            
        if historical_prices is not None and not historical_prices.empty:
            print(f"Historical Price Data: Available for {len(historical_prices)} days")
        else:
            print("Historical Price Data: Not available")
            
        if transaction_data:
            print("Transaction Data: Available")
        else:
            print("Transaction Data: Not available")
        
        return results
    
    def visualize_results(self, results):
        """Create visualizations for the analysis results"""
        if not results:
            print("No results to visualize")
            return
        
        token_symbol = results["token_symbol"]
        chain = results["chain"]
        chain_name = self.chains.get(chain, chain)
        
        # Create a figure with multiple subplots
        fig = plt.figure(figsize=(15, 12))
        fig.suptitle(f"Analysis of {token_symbol} on {chain_name}", fontsize=16)
        
        # Define grid layout
        gs = plt.GridSpec(3, 2, figure=fig)
        
        # Plot 1: Price History (if available)
        ax1 = fig.add_subplot(gs[0, :])
        if results["historical_prices"] is not None:
            ax1.plot(results["historical_prices"]["date"], results["historical_prices"]["price"])
            ax1.set_title(f"{token_symbol} Price History - Last {results['days_analyzed']} Days")
            ax1.set_xlabel("Date")
            ax1.set_ylabel("Price (USD)")
            ax1.grid(True)
        else:
            ax1.text(0.5, 0.5, "No price history data available", horizontalalignment='center', verticalalignment='center')
            ax1.set_title("Price History")
        
        # Transaction data plots (if available)
        if results["transaction_data"]:
            tx_data = results["transaction_data"]
            
            # Plot 2: Buyer Distribution
            ax2 = fig.add_subplot(gs[1, 0])
            distribution = tx_data['buyer_distribution']
            ax2.bar(distribution.keys(), distribution.values())
            ax2.set_title('Buyer Distribution by Purchase Amount')
            ax2.set_xlabel('Purchase Amount Range')
            ax2.set_ylabel('Number of Buyers')
            ax2.tick_params(axis='x', rotation=45)
            
            # Plot 3: Transaction Volumes
            ax3 = fig.add_subplot(gs[1, 1])
            volumes = ['Buy Volume', 'Sell Volume', 'Net Volume']
            values = [tx_data['total_buy_volume'], tx_data['total_sell_volume'], tx_data['net_volume']]
            ax3.bar(volumes, values)
            ax3.set_title('Transaction Volumes')
            ax3.set_ylabel(f'Amount of {token_symbol}')
            
            # Plot 4: Top Buyers
            ax4 = fig.add_subplot(gs[2, 0])
            top_buyers = tx_data['top_buyers']
            if top_buyers:
                addresses = [addr[:6] + '...' + addr[-4:] for addr, _ in top_buyers[:5]]
                amounts = [amount for _, amount in top_buyers[:5]]
                ax4.bar(addresses, amounts)
                ax4.set_title('Top 5 Buyers by Volume')
                ax4.set_xlabel('Wallet Address')
                ax4.set_ylabel(f'Amount of {token_symbol}')
                ax4.tick_params(axis='x', rotation=45)
            else:
                ax4.text(0.5, 0.5, "No buyer data available", horizontalalignment='center', verticalalignment='center')
                ax4.set_title("Top Buyers")
        else:
            # If no transaction data, show message
            ax2 = fig.add_subplot(gs[1, 0])
            ax2.text(0.5, 0.5, "No transaction data available", horizontalalignment='center', verticalalignment='center')
            ax2.set_title("Transaction Data")
            
            ax3 = fig.add_subplot(gs[1, 1])
            ax3.text(0.5, 0.5, "No transaction data available", horizontalalignment='center', verticalalignment='center')
            ax3.set_title("Transaction Volumes")
            
            ax4 = fig.add_subplot(gs[2, 0])
            ax4.text(0.5, 0.5, "No transaction data available", horizontalalignment='center', verticalalignment='center')
            ax4.set_title("Top Buyers")
        
        # Plot 5: Summary Metrics
        ax5 = fig.add_subplot(gs[2, 1])
        ax5.axis('off')
        
        # Prepare summary text
        summary_text = f"Token: {token_symbol}\nChain: {chain_name}\nDays Analyzed: {results['days_analyzed']}\n\n"
        
        # Add price data if available
        if results["price_data"]:
            price = results["price_data"].get("usd", "N/A")
            change_24h = results["price_data"].get("usd_24h_change", "N/A")
            volume_24h = results["price_data"].get("usd_24h_vol", "N/A")
            market_cap = results["price_data"].get("usd_market_cap", "N/A")
            
            summary_text += f"Current Price: ${price}\n"
            summary_text += f"24h Change: {change_24h}%\n"
            summary_text += f"24h Volume: ${volume_24h}\n"
            summary_text += f"Market Cap: ${market_cap}\n\n"
        
        # Add transaction data if available
        if results["transaction_data"]:
            tx_data = results["transaction_data"]
            summary_text += f"Unique Buyers: {tx_data['unique_buyers']}\n"
            summary_text += f"Unique Sellers: {tx_data['unique_sellers']}\n"
            summary_text += f"Total Unique Addresses: {tx_data['total_unique_addresses']}\n"
            summary_text += f"Buy Volume: {tx_data['total_buy_volume']:.2f} {token_symbol}\n"
            summary_text += f"Sell Volume: {tx_data['total_sell_volume']:.2f} {token_symbol}\n"
            summary_text += f"Net Volume: {tx_data['net_volume']:.2f} {token_symbol}"
        
        ax5.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center')
        ax5.set_title("Summary Metrics")
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig(f"{token_symbol}_{chain}_analysis.png")
        plt.show()
    
    def analyze_multiple_tokens(self, token_symbols, chain="eth", days=7):
        """Analyze multiple tokens and compare results"""
        all_results = []
        
        for symbol in token_symbols:
            results = self.analyze_token(symbol, chain, days)
            if results:
                all_results.append(results)
                print(f"Analysis complete for {symbol}")
            else:
                print(f"Could not analyze {symbol}")
        
        if not all_results:
            print("No results to compare")
            return
        
        # Create comparison visualizations
        self._visualize_token_comparison(all_results)
        
        return all_results
    
    def _visualize_token_comparison(self, results_list):
        """Create comparison visualizations for multiple tokens"""
        if not results_list:
            return
            
        # Extract data for comparison
        tokens = [r['token_symbol'] for r in results_list]
        
        # Price data (if available)
        prices = []
        for r in results_list:
            if r['price_data'] and 'usd' in r['price_data']:
                prices.append(r['price_data']['usd'])
            else:
                prices.append(0)
        
        # Transaction data (if available)
        tx_data_available = any(r['transaction_data'] is not None for r in results_list)
        
        if tx_data_available:
            # Create figure with price and transaction data
            fig, axs = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f"Comparison of {', '.join(tokens)}", fontsize=16)
            
            # Plot 1: Current Prices
            axs[0, 0].bar(tokens, prices)
            axs[0, 0].set_title('Current Price (USD)')
            axs[0, 0].set_ylabel('USD')
            
            # Transaction data plots
            unique_buyers = []
            buy_volumes = []
            net_volumes = []
            
            for r in results_list:
                if r['transaction_data']:
                    unique_buyers.append(r['transaction_data']['unique_buyers'])
                    buy_volumes.append(r['transaction_data']['total_buy_volume'])
                    net_volumes.append(r['transaction_data']['net_volume'])
                else:
                    unique_buyers.append(0)
                    buy_volumes.append(0)
                    net_volumes.append(0)
            
            # Plot 2: Unique Buyers
            axs[0, 1].bar(tokens, unique_buyers)
            axs[0, 1].set_title('Unique Buyers')
            axs[0, 1].set_ylabel('Count')
            
            # Plot 3: Buy Volume
            axs[1, 0].bar(tokens, buy_volumes)
            axs[1, 0].set_title('Buy Volume')
            axs[1, 0].set_ylabel('Token Amount')
            
            # Plot 4: Net Volume
            axs[1, 1].bar(tokens, net_volumes)
            axs[1, 1].set_title('Net Volume (Buy - Sell)')
            axs[1, 1].set_ylabel('Token Amount')
        else:
            # Only price data available
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.suptitle(f"Price Comparison of {', '.join(tokens)}", fontsize=16)
            
            ax.bar(tokens, prices)
            ax.set_title('Current Price (USD)')
            ax.set_ylabel('USD')
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig(f"token_comparison_{len(tokens)}_tokens.png")
        plt.show()
    
    def search_tokens(self, query):
        """Search for tokens by name or symbol"""
        return self.coingecko.search_coins(query)


def main():
    try:
        analyzer = CryptoAnalyzer()
        
        print("Crypto Analyzer")
        print("==============")
        print("\nOptions:")
        print("1. Analyze a single token")
        print("2. Compare multiple tokens")
        print("3. Search for tokens")
        print("4. List supported chains")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            token = input("Enter token symbol (e.g., BTC, ETH, LINK): ").upper()
            
            print(f"\nAvailable chains: {', '.join(analyzer.chains.keys())}")
            chain = input(f"Enter chain (default is eth): ") or "eth"
            
            if chain not in analyzer.chains:
                print(f"Warning: {chain} is not in the list of supported chains. Proceeding anyway...")
            
            days = int(input("Enter number of days to analyze (default is 7): ") or "7")
            
            results = analyzer.analyze_token(token, chain, days)
            
            if results:
                print("\nAnalysis Results:")
                print(f"Token: {results['token_symbol']}")
                print(f"Chain: {analyzer.chains.get(chain, chain)}")
                
                if results["price_data"]:
                    print(f"Current Price: ${results['price_data'].get('usd', 'N/A')}")
                    print(f"24h Change: {results['price_data'].get('usd_24h_change', 'N/A')}%")
                
                if results["transaction_data"]:
                    tx_data = results["transaction_data"]
                    print(f"\nTransaction Analysis:")
                    print(f"Unique Buyers: {tx_data['unique_buyers']}")
                    print(f"Unique Sellers: {tx_data['unique_sellers']}")
                    print(f"Total Unique Addresses: {tx_data['total_unique_addresses']}")
                    print(f"Buy Volume: {tx_data['total_buy_volume']:.2f} {results['token_symbol']}")
                    print(f"Sell Volume: {tx_data['total_sell_volume']:.2f} {results['token_symbol']}")
                    print(f"Net Volume: {tx_data['net_volume']:.2f} {results['token_symbol']}")
                
                # Ask if user wants to see visualization
                if input("\nShow visualization? (y/n): ").lower() == 'y':
                    analyzer.visualize_results(results)
        
        elif choice == "2":
            tokens_input = input("Enter token symbols separated by comma (e.g., BTC,ETH,LINK): ")
            tokens = [t.strip().upper() for t in tokens_input.split(',')]
            
            print(f"\nAvailable chains: {', '.join(analyzer.chains.keys())}")
            chain = input(f"Enter chain (default is eth): ") or "eth"
            
            if chain not in analyzer.chains:
                print(f"Warning: {chain} is not in the list of supported chains. Proceeding anyway...")
            
            days = int(input("Enter number of days to analyze (default is 7): ") or "7")
            
            analyzer.analyze_multiple_tokens(tokens, chain, days)
        
        elif choice == "3":
            query = input("Enter search term for tokens: ")
            matching_tokens = analyzer.search_tokens(query)
            
            if matching_tokens:
                print(f"\nFound {len(matching_tokens)} matching tokens:")
                for token in matching_tokens[:20]:  # Show first 20 results
                    print(f"ID: {token['id']}, Symbol: {token['symbol']}, Name: {token['name']}")
            else:
                print("No matching tokens found.")
        
        elif choice == "4":
            print("\nSupported chains:")
            for code, name in analyzer.chains.items():
                print(f"- {code}: {name}")
        
        elif choice == "5":
            print("Exiting...")
        
        else:
            print("Invalid choice. Please try again.")
    
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("Please check your input and try again.")


if __name__ == "__main__":
    main()
