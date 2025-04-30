import os
import sys
import pandas as pd
from transaction_insights_module import TransactionInsightsModule
from coingecko_client import CoinGeckoClient
from address_lookup import AddressResolver
from moralis_client import MoralisClient

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Full diagnostic for the transaction insights pipeline.")
    parser.add_argument('--symbol', type=str, default='USDT', help='Token symbol (e.g., USDT, WBTC, DAI)')
    parser.add_argument('--chain', type=str, default=None, help='Blockchain (e.g., eth, bsc, polygon). Leave blank for auto-detect.')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--whale_usd', type=float, default=10000, help='USD threshold for whale transfers')
    parser.add_argument('--top_n', type=int, default=5, help='Top N buyers/sellers/holders')
    args = parser.parse_args()

    print(f"\n[TEST] Running analysis for {args.symbol} on {args.chain or 'auto'} chain, {args.days} days, whale threshold ${args.whale_usd}")

    # Address resolution
    cg = CoinGeckoClient()
    moralis = MoralisClient()
    resolver = AddressResolver(cg, moralis)
    print("[STEP] Resolving contract address...")
    addr_eth = resolver.get_token_address(args.symbol, 'eth')
    addr_bsc = resolver.get_token_address(args.symbol, 'bsc')
    addr_poly = resolver.get_token_address(args.symbol, 'polygon')
    print(f"ETH: {addr_eth}\nBSC: {addr_bsc}\nPolygon: {addr_poly}")

    ti = TransactionInsightsModule(cg)
    try:
        print("[STEP] Running analyze_and_export...")
        result = ti.analyze_and_export(
            token_symbol=args.symbol,
            chain=args.chain,
            days=args.days,
            whale_usd_threshold=args.whale_usd,
            top_n=args.top_n
        )
        if result is None:
            print("[FAIL] No transactions found or analysis failed.")
            sys.exit(1)
        print("\n[PASS] Analysis ran successfully. Output summaries:")
        for key in ['buyers', 'sellers', 'holders', 'whale_tx']:
            print(f"\n[{key.upper()}]:\n", result.get(key))
    except Exception as e:
        print(f"[ERROR] Exception during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

    # Print CoinGecko price
    try:
        print("[STEP] Resolving CoinGecko coin id and price...")
        coin_id = cg.get_coin_id(args.symbol)
        print(f"CoinGecko coin id for {args.symbol}: {coin_id}")
        if coin_id:
            price_info = cg.get_coin_price(coin_id, vs_currency='usd')
            print(f"[CoinGecko] {args.symbol} price info: {price_info}")
        else:
            print(f"[CoinGecko] Could not resolve coin id for {args.symbol}")
    except Exception as e:
        print(f"[CoinGecko] Error fetching price: {e}")

    # Check output files
    output_dir = os.path.join(os.getcwd(), 'output')
    output_files = [
        'outputs.csv',
        'buyers_summary.csv',
        'sellers_summary.csv',
        'holders_summary.csv',
        'whale_transactions.csv',
    ]
    for fname in output_files:
        fpath = os.path.join(output_dir, fname)
        print(f"\n[CHECK] {fname}:", end=' ')
        if os.path.exists(fpath):
            print("FOUND")
            try:
                df = pd.read_csv(fpath)
                print(df.head())
            except Exception as e:
                print(f"[ERROR reading {fname}]: {e}")
        else:
            print("MISSING")
    print("\n[COMPLETE] Diagnostics finished.")
