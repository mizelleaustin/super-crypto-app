"""
transaction_module.py - Handles comprehensive token transfer analysis and reporting
"""

import os
import pandas as pd

from address_lookup import AddressResolver
from moralis_client import MoralisClient
from coingecko_client import CoinGeckoClient
from moralis import evm_api

class TransactionModule:
    def __init__(self, coingecko_client):
        self.coingecko = coingecko_client
        self.address_resolver = AddressResolver(CoinGeckoClient(), MoralisClient())

    def analyze_token_transfers(self, token_symbol, chain=None, days=30, max_transfers=500, large_transfer_usd=0):
        """
        Analyze token transfers for a given symbol and chain using Moralis and CoinGecko.
        Returns a dictionary with transfer stats, daily/weekly summaries, and price data.
        """
        import pandas as pd
        from datetime import datetime, timedelta
        import time

        # Validate days input
        try:
            days = int(days)
            if days <= 0:
                print("Days must be positive. Using default (30).")
                days = 30
        except (ValueError, TypeError):
            print("Invalid days input. Using default (30).")
            days = 30

        token_symbol = token_symbol.upper()
        # Automatic chain detection (ETH > BSC > Polygon)
        if not chain:
            for ch in ["eth", "bsc", "polygon"]:
                addr = self.address_resolver.get_token_address(token_symbol, ch)
                if addr:
                    chain = ch
                    break
            if not chain:
                chain = "eth"
            print(f"Using {chain} blockchain for {token_symbol}")
        # Unified address resolution (local > CoinGecko > Moralis)
        token_address = self.address_resolver.get_token_address(token_symbol, chain)
        if not token_address:
            print(f"Cannot analyze {token_symbol}: No contract address available for this coin or chain.")
            return None

        # Fetch transfers from Moralis with pagination
        all_transfers = []
        try:
            from datetime import datetime, timedelta
            from_time_dt = datetime.now() - timedelta(days=days)
            from_time_iso = from_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            to_time_iso = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            print(f"[DEBUG] Using ISO8601 from_date for Moralis: {from_time_iso}")
            print(f"[DEBUG] Using ISO8601 to_date for Moralis: {to_time_iso}")
            import traceback
            import moralis
            import requests
            api_key = os.getenv("MORALIS_API_KEY")
            url = f"https://deep-index.moralis.io/api/v2/erc20/{token_address}/transfers"
            headers = {
                "accept": "application/json",
                "X-API-Key": api_key,
            }
            cursor = None
            fetched = 0
            first_batch = True
            while fetched < max_transfers:
                limit = min(100, max_transfers - fetched)
                params_rest = {
                    "chain": str(chain),
                    "from_date": from_time_iso,
                    "to_date": to_time_iso,
                    "limit": str(limit),
                }
                if cursor:
                    params_rest["cursor"] = cursor
                # Print the full URL with params for the first batch
                if first_batch:
                    import urllib.parse
                    full_url = f"{url}?{urllib.parse.urlencode(params_rest)}"
                    print(f"[REST] FULL URL: {full_url}")
                print(f"[REST] Moralis API call: {url}")
                print(f"[REST] Headers: {headers}")
                print(f"[REST] Params: {params_rest}")
                resp = requests.get(url, headers=headers, params=params_rest)
                print(f"[REST] Status code: {resp.status_code}")
                if resp.status_code != 200:
                    print(f"[REST] Error: {resp.text}")
                    break
                result = resp.json()
                batch = result.get("result", [])
                if first_batch and batch:
                    print(f"[DIAG] First transfer raw JSON: {batch[0]}")
                all_transfers.extend(batch)
                fetched += len(batch)
                print(f"[REST] Transfers fetched this batch: {len(batch)}, total: {fetched}")
                cursor = result.get("cursor")
                if not cursor or not batch:
                    break
                first_batch = False
            print(f"[REST] Total transfers fetched: {len(all_transfers)}")
            # Print diagnostics for transfer timestamps and block numbers
            if all_transfers:
                import pandas as pd
                df_diag = pd.DataFrame(all_transfers)
                if 'block_timestamp' in df_diag.columns:
                    print(f"[DIAG] block_timestamp min: {df_diag['block_timestamp'].min()}, max: {df_diag['block_timestamp'].max()}")
                if 'block_number' in df_diag.columns:
                    print(f"[DIAG] block_number min: {df_diag['block_number'].min()}, max: {df_diag['block_number'].max()}")
        except Exception as e:
            print("[REST] Exception during Moralis REST call:")
            traceback.print_exc()
            print(f"Error fetching token transfers from REST: {e}")
            return None

        if not all_transfers:
            print("No transfers found.")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(all_transfers)
        if df.empty:
            print("No transfer data to analyze.")
            return None
        df['timestamp'] = pd.to_datetime(df['block_timestamp'])
        df['date'] = df['timestamp'].dt.date
        # Daily aggregation
        daily_stats = df.groupby('date').agg({'to_address': 'nunique', 'value': 'sum'}).reset_index()
        # Weekly aggregation
        df['week'] = df['timestamp'].dt.isocalendar().week
        df['year'] = df['timestamp'].dt.isocalendar().year
        df['year_week'] = df['year'].astype(str) + '-' + df['week'].astype(str)
        weekly_stats = df.groupby('year_week').agg({'to_address': 'nunique', 'value': 'sum'}).reset_index()

        # Get price data from CoinGecko
        coin_id = self.coingecko.get_coin_id(token_symbol)
        price_data = None
        if coin_id:
            price_data = self.coingecko.get_historical_prices(coin_id, days)

        results = {
            "token_symbol": token_symbol,
            "token_address": token_address,
            "chain": chain,
            "days_analyzed": days,
            "transfers_count": len(all_transfers),
            "transfers_df": df,
            "daily_stats": daily_stats,
            "weekly_stats": weekly_stats,
            "price_data": price_data,
            "large_transfer_usd": large_transfer_usd
        }
        # Print transfer list and highlight large buys/sells
        self.print_transfer_list(df, price_data, large_transfer_usd)
        # Visualization removed: only print the transfer list in terminal
        return results

    def print_transfer_list(self, transfers_df, price_data, large_transfer_usd=0):
        """
        Print a list of transfers (date/time, from, to, value, hash) and highlight large buys/sells.
        Enhanced error handling and diagnostics for debugging.
        """
        import numpy as np
        import pandas as pd
        if transfers_df is None or transfers_df.empty:
            print("No transfer data to display.")
            return
        # Defensive: check for required columns
        required_cols = ['timestamp', 'block_timestamp', 'from_address', 'to_address', 'value', 'transaction_hash', 'token_decimal']
        missing_cols = [col for col in required_cols if col not in transfers_df.columns]
        if missing_cols:
            print(f"[ERROR] Missing required columns in transfer DataFrame: {missing_cols}")
            return
        print("\nTransfers (date/time, from, to, value, tx_hash):")
        usd_prices = None
        try:
            if price_data is not None and not price_data.empty and 'date' in price_data.columns and 'price' in price_data.columns:
                price_data = price_data.copy()
                price_data['date'] = pd.to_datetime(price_data['date']).dt.tz_localize(None)
                transfers_df['timestamp'] = pd.to_datetime(transfers_df['block_timestamp']).dt.tz_localize(None)
                transfers_df['nearest_price_idx'] = transfers_df['timestamp'].apply(lambda ts: np.argmin(np.abs(price_data['date'] - ts)))
                usd_prices = transfers_df['nearest_price_idx'].apply(lambda idx: price_data.iloc[idx]['price'])
        except Exception as e:
            print(f"[WARNING] Failed to map price data for USD calculation: {e}")
            usd_prices = None
        print(f"{'Date/Time':22} | {'From':42} | {'To':42} | {'Amount':>16} | {'USD':>10} | {'Tx Hash':66} | {'Type':8} | {'LARGE':5}")
        print("-"*170)
        for i, row in transfers_df.iterrows():
            try:
                dt = str(row['timestamp'])[:19] if 'timestamp' in row and pd.notnull(row['timestamp']) else str(row.get('block_timestamp', ''))[:19]
                from_addr = row['from_address'][:40] if pd.notnull(row['from_address']) else ''
                to_addr = row['to_address'][:40] if pd.notnull(row['to_address']) else ''
                value = row['value'] if pd.notnull(row['value']) else 0
                tx_hash = row['transaction_hash'][:64] if pd.notnull(row['transaction_hash']) else ''
                decimals = 18
                if 'token_decimal' in row and pd.notnull(row['token_decimal']):
                    try:
                        decimals = int(row['token_decimal'])
                    except Exception:
                        print(f"[WARNING] Invalid token_decimal: {row['token_decimal']}, defaulting to 18.")
                        decimals = 18
                try:
                    amount = int(value) / (10 ** decimals) if value not in [None, '', np.nan] else 0
                except Exception:
                    print(f"[WARNING] Invalid value for amount calculation: {value}, setting to 0.")
                    amount = 0
                usd = None
                if usd_prices is not None:
                    try:
                        usd = usd_prices[i] * amount
                    except Exception as e:
                        print(f"[WARNING] Error calculating USD value for row {i}: {e}")
                        usd = None
                ttype = 'Buy' if row['to_address'] and row['to_address'].lower() != row.get('token_address','').lower() else ('Sell' if row['from_address'] and row['from_address'].lower() != row.get('token_address','').lower() else 'Other')
                large = ''
                if large_transfer_usd and usd is not None and usd >= large_transfer_usd:
                    large = '***'
                if amount == 0 or usd in [None, 0, np.nan]:
                    print(f"[DEBUG] Suspicious zero or missing value at row {i}: amount={amount}, usd={usd}, tx_hash={tx_hash}")
                print(f"{dt:22} | {from_addr:42} | {to_addr:42} | {amount:16.6f} | {usd if usd is not None else '-':10.2f} | {tx_hash:66} | {ttype:8} | {large:5}")
            except Exception as row_e:
                print(f"[ERROR] Exception processing row {i}: {row_e}")
        print("\nLegend: 'LARGE' = '***' means transfer value >= threshold (USD)")
        print("[INFO] If you see repeated 0.00 values, check upstream data sources and token decimals. If this persists, please report with sample data.")



    def generate_report(self, analysis_results, filename=None):
        """
        Export analysis results to CSV files and print a summary.
        """
        import os
        import pandas as pd
        from datetime import datetime
        if not analysis_results:
            print("No results to export.")
            return
        token_symbol = analysis_results["token_symbol"]
        if filename is None:
            filename_base = f"{token_symbol}_analysis_{datetime.now().strftime('%Y%m%d')}"
        else:
            filename_base = filename
        # Export daily stats
        try:
            daily_file = f"{filename_base}_daily.csv"
            analysis_results["daily_stats"].to_csv(daily_file, index=False)
            print(f"[EXPORT SUCCESS] Daily stats exported to {os.path.abspath(daily_file)}")
        except Exception as e:
            print(f"[EXPORT ERROR] Failed to export daily stats: {e}")
        # Export weekly stats
        try:
            weekly_file = f"{filename_base}_weekly.csv"
            analysis_results["weekly_stats"].to_csv(weekly_file, index=False)
            print(f"[EXPORT SUCCESS] Weekly stats exported to {os.path.abspath(weekly_file)}")
        except Exception as e:
            print(f"[EXPORT ERROR] Failed to export weekly stats: {e}")
        # Export all transfers
        try:
            transfers_file = f"{filename_base}_all_transfers.csv"
            analysis_results["transfers_df"].to_csv(transfers_file, index=False)
            print(f"[EXPORT SUCCESS] All transfers exported to {os.path.abspath(transfers_file)}")
        except Exception as e:
            print(f"[EXPORT ERROR] Failed to export all transfers: {e}")
        # Print summary
        print(f"\nAnalysis Summary for {token_symbol} on {analysis_results['chain']}:")
        print(f"Transfers analyzed: {analysis_results['transfers_count']}")
        print(f"Period: Last {analysis_results['days_analyzed']} days")
        price_data = analysis_results.get("price_data")
        if price_data is not None and not price_data.empty:
            print(f"Price data available for {len(price_data['date'])} days.")
        else:
            print("No price data available.")
