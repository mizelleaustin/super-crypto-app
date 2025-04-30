"""
transaction_insights_module.py - Combined module for raw transaction export and wallet analytics
"""
import os
import pandas as pd
from transaction_module import TransactionModule


class TransactionInsightsModule:
    def __init__(self, coingecko_client):
        self.transaction_module = TransactionModule(coingecko_client)
        

    def analyze_and_export(self, token_symbol, chain=None, days=30, whale_usd_threshold=10000, top_n=5, output_file=None):
        # Ensure output directory exists
        output_dir = os.path.join(os.getcwd(), 'output')
        os.makedirs(output_dir, exist_ok=True)
        if output_file is None:
            output_file = os.path.join(output_dir, "outputs.csv")
        else:
            output_file = os.path.join(output_dir, output_file) if not os.path.isabs(output_file) else output_file
        # Fetch raw transactions
        print(f"[INFO] Fetching raw transactions for {token_symbol}...")
        results = self.transaction_module.analyze_token_transfers(token_symbol, chain=chain, days=days, max_transfers=1000)
        if results is None:
            print("[ERROR] No transactions found or analysis failed.")
            return
        transfers_df = results.get("transfers_df")
        if transfers_df is None or transfers_df.empty:
            print("[ERROR] No transactions found.")
            return

        # Ensure 'value' and 'usd_value' columns are numeric
        transfers_df["value"] = pd.to_numeric(transfers_df["value"], errors="coerce")
        if "usd_value" in transfers_df.columns:
            transfers_df["usd_value"] = pd.to_numeric(transfers_df["usd_value"], errors="coerce")

        # Use Moralis 'value_decimal' if present for accurate, pre-scaled values
        if 'value_decimal' in transfers_df.columns:
            transfers_df['value'] = pd.to_numeric(transfers_df['value_decimal'], errors='coerce')
            print("[DEBUG] Using value_decimal from Moralis for value column.")
        else:
            try:
                decimals = 18  # Default
                if 'token_decimals' in transfers_df.columns:
                    try:
                        decimals = int(transfers_df['token_decimals'].iloc[0])
                        print(f"[DEBUG] Using token_decimals from Moralis: {decimals}")
                    except Exception as de:
                        print(f"[WARN] Could not parse token_decimals: {de}, defaulting to 18")
                        decimals = 18
                # Only scale if values are not already floats < 1
                if transfers_df['value'].max() > 1000:
                    transfers_df['value'] = pd.to_numeric(transfers_df['value'], errors='coerce') / (10 ** decimals)
                else:
                    transfers_df['value'] = pd.to_numeric(transfers_df['value'], errors='coerce')
            except Exception as e:
                print(f"[WARN] Could not convert token values to human-readable units: {e}")

        # Ensure column alias for downstream compatibility
        if 'token_decimal' not in transfers_df.columns and 'token_decimals' in transfers_df.columns:
            transfers_df['token_decimal'] = transfers_df['token_decimals']

        # Debug: print sample values
        print(f"[DEBUG] Sample values after value_decimal/scaling: {transfers_df['value'].head(5)}")

        # Compute usd_value for each transfer using CoinGecko price (latest available)
        usd_price = None
        try:
            price_data = results.get('price_data') if 'results' in locals() else None
            if price_data is not None and not price_data.empty and 'price' in price_data.columns:
                usd_price = price_data['price'].iloc[-1]  # Use latest available price
            else:
                print("[WARN] Could not get CoinGecko price data for USD calculation. Whale detection may be skipped.")
        except Exception as e:
            print(f"[WARN] Error getting CoinGecko price: {e}")
        if usd_price:
            transfers_df['usd_value'] = transfers_df['value'] * usd_price
            print(f"[DEBUG] Added usd_value column using CoinGecko price: {usd_price}")
        else:
            print("[WARN] No USD price available, usd_value column not added.")

        # Debug: print sample usd_value
        if 'usd_value' in transfers_df.columns:
            print(f"[DEBUG] Sample usd_value: {transfers_df['usd_value'].head(5)}")

        # Calculate top buyers, sellers, holders
        print("[INFO] Calculating top buyers, sellers, holders...")
        buyers = transfers_df.groupby("to_address")["value"].sum().sort_values(ascending=False).head(top_n)
        sellers = transfers_df.groupby("from_address")["value"].sum().sort_values(ascending=False).head(top_n)
        holders = (transfers_df.groupby("to_address")["value"].sum() - transfers_df.groupby("from_address")["value"].sum()).sort_values(ascending=False).head(top_n)

        # Whale monitoring
        print(f"[INFO] Identifying whale transactions (>{whale_usd_threshold} USD)...")
        whale_txs = None
        if "usd_value" in transfers_df.columns:
            whale_txs = transfers_df[transfers_df["usd_value"] > whale_usd_threshold]
            print(f"[DEBUG] Whale transaction count: {len(whale_txs) if whale_txs is not None else 0}")
            if whale_txs is not None and not whale_txs.empty:
                print(f"[DEBUG] Sample whale transactions:\n{whale_txs[['from_address','to_address','value','usd_value']].head(3)}")
        else:
            print("[WARN] No 'usd_value' column present, cannot filter whale transactions.")

        # Export raw and summary CSVs
        print(f"[INFO] Writing raw transfers to {output_file}")
        transfers_df.to_csv(output_file, index=False)
        print(f"[DEBUG] Raw transfers written to {output_file}")
        # Buyers
        buyers_summary = buyers.reset_index().rename(columns={"to_address": "address", "value": "value"})
        buyers_path = os.path.join(output_dir, "buyers_summary.csv")
        if not buyers_summary.empty:
            buyers_summary.to_csv(buyers_path, index=False)
            print(f"[DEBUG] Buyers summary written to {buyers_path}")
        else:
            print(f"[DEBUG] No buyers found. Writing empty buyers_summary.csv with headers.")
            pd.DataFrame(columns=["address", "value"]).to_csv(buyers_path, index=False)
            print(f"[DEBUG] Empty buyers summary written to {buyers_path}")
        # Sellers
        sellers_summary = sellers.reset_index().rename(columns={"from_address": "address", "value": "value"})
        sellers_path = os.path.join(output_dir, "sellers_summary.csv")
        if not sellers_summary.empty:
            sellers_summary.to_csv(sellers_path, index=False)
            print(f"[DEBUG] Sellers summary written to {sellers_path}")
        else:
            print(f"[DEBUG] No sellers found. Writing empty sellers_summary.csv with headers.")
            pd.DataFrame(columns=["address", "value"]).to_csv(sellers_path, index=False)
            print(f"[DEBUG] Empty sellers summary written to {sellers_path}")
        # Holders
        holders_summary = holders.reset_index()
        # The reset_index will create a column named 'index' or 'to_address', depending on pandas version. Rename as needed.
        if holders_summary.columns[0] != 'address':
            holders_summary = holders_summary.rename(columns={holders_summary.columns[0]: 'address'})
        if holders_summary.columns[-1] != 'value':
            holders_summary = holders_summary.rename(columns={holders_summary.columns[-1]: 'value'})
        holders_path = os.path.join(output_dir, "holders_summary.csv")
        if not holders_summary.empty:
            holders_summary.to_csv(holders_path, index=False)
            print(f"[DEBUG] Holders summary written to {holders_path}")
        else:
            print(f"[DEBUG] No holders found. Writing empty holders_summary.csv with headers.")
            pd.DataFrame(columns=["address", "value"]).to_csv(holders_path, index=False)
            print(f"[DEBUG] Empty holders summary written to {holders_path}")
        # Whales
        whales_path = os.path.join(output_dir, "whale_transactions.csv")
        if whale_txs is not None and not whale_txs.empty:
            whale_txs.to_csv(whales_path, index=False)
            print(f"[DEBUG] Whale transactions written to {whales_path}")
        else:
            print(f"[DEBUG] No whale transactions found. Writing empty whale_transactions.csv with headers.")
            pd.DataFrame(columns=transfers_df.columns).to_csv(whales_path, index=False)
            print(f"[DEBUG] Empty whale transactions written to {whales_path}")
        print("[INFO] Export complete.")
        print("[EXPORT SUCCESS] Summaries exported to output folder: buyers_summary.csv, sellers_summary.csv, holders_summary.csv, whale_transactions.csv (if any)")

        return {
            "buyers": buyers,
            "sellers": sellers,
            "holders": holders,
            "whale_tx": whale_txs
        }
