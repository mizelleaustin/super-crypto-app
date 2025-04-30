import streamlit as st
import pandas as pd
import os
import sys
import importlib
import openai
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'crypto_wallet')))

st.set_page_config(page_title="Transaction Insights Dashboard", layout="wide")

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Import analysis logic dynamically ---
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)
try:
    transaction_insights_module_mod = importlib.import_module("transaction_insights_module")
    from crypto_wallet.coingecko_client import CoinGeckoClient
    coingecko_client = CoinGeckoClient()
    TIModule = transaction_insights_module_mod.TransactionInsightsModule(coingecko_client)
except Exception as e:
    st.error(f"Failed to import analysis logic: {e}")
    TIModule = None

output_dir = os.path.join(os.getcwd(), "output")

current_symbol = st.session_state.get('current_symbol', 'N/A')
st.title(f"Insights Dashboard — Showing: {current_symbol}")  # Unified dashboard for all analytics

# --- Chatbot at the Top (ONLY ONCE) ---

# Helper to load CSV safely
def load_csv(filename):
    path = os.path.join(output_dir, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame()

# Use session_state DataFrames if available, else fallback to loaded at startup
raw_df = st.session_state.get('raw_df', load_csv("outputs.csv"))
buyers_df = st.session_state.get('buyers_df', load_csv("buyers_summary.csv"))
sellers_df = st.session_state.get('sellers_df', load_csv("sellers_summary.csv"))
holders_df = st.session_state.get('holders_df', load_csv("holders_summary.csv"))
whales_df = st.session_state.get('whales_df', load_csv("whale_transactions.csv"))
current_symbol = st.session_state.get('current_symbol', 'N/A')

st.header(":robot_face: Insights Assistant (Chatbot)")
st.write("This assistant can help answer crypto questions, explain dashboard features, or provide basic data insights. **Note:** Answers are based on the latest loaded data!")
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def get_data_summary():
    summary = []
    if not raw_df.empty:
        summary.append(f"Raw transactions: {len(raw_df)} rows")
    if not buyers_df.empty:
        summary.append(f"Top buyer: {buyers_df.iloc[0,0] if buyers_df.shape[0]>0 else 'N/A'}")
    if not sellers_df.empty:
        summary.append(f"Top seller: {sellers_df.iloc[0,0] if sellers_df.shape[0]>0 else 'N/A'}")
    if not holders_df.empty:
        summary.append(f"Top holder: {holders_df.iloc[0,0] if holders_df.shape[0]>0 else 'N/A'}")
    if not whales_df.empty:
        summary.append(f"Number of whale transactions: {len(whales_df)}")
    return "\n".join(summary) if summary else "No data loaded."

def calculate_net_difference_simple(buyers_df, sellers_df):
    buyers_sum = buyers_df['value'].sum() if 'value' in buyers_df.columns else 0
    sellers_sum = sellers_df['value'].sum() if 'value' in sellers_df.columns else 0
    return buyers_sum - sellers_sum, buyers_sum, sellers_sum

def get_dashboard_metrics_summary():
    net_diff, total_buys, total_sells = calculate_net_difference_simple(buyers_df, sellers_df)
    return (
        f"Net Difference (Top {top_n} Buyers - Top {top_n} Sellers): ${net_diff:,.2f}\n"
        f"Total bought: ${total_buys:,.2f}\n"
        f"Total sold: ${total_sells:,.2f}"
    )

# --- User Inputs Section (Sidebar) ---
st.sidebar.header("Run New Analysis")
ticker = st.sidebar.text_input(
    "Token Symbol (ERC20 only, e.g., USDT, USDC, DAI, SHIB)",
    value="USDT",
    help="Enter the ERC20 token symbol (not native coins like ETH or BTC). Only ERC20 tokens are supported. For native coins, analytics are not available in this dashboard."
)
days = st.sidebar.number_input("Number of days for analysis", min_value=1, max_value=365, value=30)
whale_usd = st.sidebar.number_input(
    "Minimum USD value for whale transfer",
    min_value=1, value=10000,
    help="Only transactions above this USD value will be considered 'whale' transactions and shown in the table. Lower this if you see no results."
)
top_n = st.sidebar.number_input(
    "How many top buyers/sellers/holders to display?",
    min_value=1, max_value=50, value=5,
    help="This controls how many addresses are shown in each summary table. For example, 5 will show the top 5 buyers, sellers, and holders."
)
run_analysis = st.sidebar.button("Run Analysis")
show_coins = st.sidebar.button("Show Supported Coins")

if run_analysis and TIModule is not None:
    symbol = ticker.strip().upper()
    # List of native coin symbols for blockchains Moralis supports
    native_coins = ["ETH", "BNB", "MATIC", "AVAX", "FTM", "CRO", "ONE", "KLAY", "OKT", "HT", "CELO", "GLMR", "MOVR", "KAVA", "CUBE", "TLOS", "METIS", "BTT", "DFK", "ASTR", "SDN", "EVMOS", "CANTO", "CORE", "DOGE"]
    if symbol in native_coins:
        st.sidebar.error(f"Native coin '{symbol}' is not supported. Only ERC20 tokens are supported in this dashboard. For native coins like ETH, use a dedicated native coin analytics tool.")
    else:
        with st.spinner("Running analysis and exporting data..."):
            TIModule.analyze_and_export(symbol, days=days, whale_usd_threshold=whale_usd, top_n=top_n)
        # Reload DataFrames after analysis and store in session_state
        st.session_state['current_symbol'] = symbol
        st.session_state['raw_df'] = load_csv("outputs.csv")
        st.session_state['buyers_df'] = load_csv("buyers_summary.csv")
        st.session_state['sellers_df'] = load_csv("sellers_summary.csv")
        st.session_state['holders_df'] = load_csv("holders_summary.csv")
        st.session_state['whales_df'] = load_csv("whale_transactions.csv")
        st.success(f"Analysis complete for {symbol}. Data reloaded!")
        st.rerun()

if show_coins:
    try:
        coin_list = coingecko_client.get_coin_list()
        if coin_list:
            with st.expander("Supported Coins List", expanded=True):
                st.write(f"Total supported coins: {len(coin_list)}")
                st.dataframe(pd.DataFrame(coin_list)[[col for col in ['id','symbol','name'] if col in pd.DataFrame(coin_list).columns]])
        else:
            st.warning("No coin data available from CoinGecko.")
    except Exception as e:
        st.error(f"Failed to fetch supported coins: {e}")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask me anything about crypto or this dashboard...")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        try:
            system_prompt = (
                "You are a helpful crypto dashboard assistant. "
                "Always answer using the numbers provided below. "
                "If the user asks about net difference, total bought, or total sold, use only these numbers. "
                "Do not speculate about addresses, wallet overlap, or trends—just report the numbers. "
                "Here are the current dashboard metrics:\n"
                f"{get_dashboard_metrics_summary()}"
            )
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
                ],
                max_tokens=300,
                temperature=0.5,
            )
            bot_reply = response.choices[0].message.content
        except Exception as e:
            bot_reply = f"[Error contacting assistant: {e}]"
    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

# --- Dashboard Layout ---
col1, col2 = st.columns(2)

def calculate_net_difference_simple(buyers_df, sellers_df):
    buyers_sum = buyers_df['value'].sum() if 'value' in buyers_df.columns else 0
    sellers_sum = sellers_df['value'].sum() if 'value' in sellers_df.columns else 0
    return buyers_sum - sellers_sum, buyers_sum, sellers_sum

# Ensure this function is defined before chatbot logic

def calculate_net_difference_simple(buyers_df, sellers_df):
    buyers_sum = buyers_df['value'].sum() if 'value' in buyers_df.columns else 0
    sellers_sum = sellers_df['value'].sum() if 'value' in sellers_df.columns else 0
    return buyers_sum - sellers_sum, buyers_sum, sellers_sum

def get_dashboard_metrics_summary():
    net_diff, total_buys, total_sells = calculate_net_difference_simple(buyers_df, sellers_df)
    return (
        f"Net Difference (Top {top_n} Buyers - Top {top_n} Sellers): ${net_diff:,.2f}\n"
        f"Total bought: ${total_buys:,.2f}\n"
        f"Total sold: ${total_sells:,.2f}"
    )

# --- Dashboard Layout ---
col1, col2 = st.columns(2)

# Show warning if all tables are empty
if buyers_df.empty and sellers_df.empty and holders_df.empty and (whales_df is None or whales_df.empty):
    st.warning('No transaction data available for this coin and period. Try a different coin or a longer date range.')

with col1:
    st.markdown('### Top Buyers')
    buyers_fmt = buyers_df.copy()
    for col in buyers_fmt.columns:
        if col in ['to_address', 'from_address', 'address']:
            buyers_fmt.rename(columns={col: 'address'}, inplace=True)
    for col in buyers_fmt.columns:
        if 'value' in col:
            buyers_fmt[col] = buyers_fmt[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else x)
    if not buyers_fmt.empty:
        st.dataframe(buyers_fmt, use_container_width=True)
    else:
        st.info('No buyer data available for this analysis.')

    st.markdown('---')
    st.markdown('### Top Sellers')
    sellers_fmt = sellers_df.copy()
    for col in sellers_fmt.columns:
        if col in ['to_address', 'from_address', 'address']:
            sellers_fmt.rename(columns={col: 'address'}, inplace=True)
    for col in sellers_fmt.columns:
        if 'value' in col:
            sellers_fmt[col] = sellers_fmt[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else x)
    if not sellers_fmt.empty:
        st.dataframe(sellers_fmt, use_container_width=True)
    else:
        st.info('No seller data available for this analysis.')

    st.markdown('---')
    st.markdown('### Top Holders')
    holders_fmt = holders_df.copy()
    for col in holders_fmt.columns:
        if col in ['to_address', 'from_address', 'address']:
            holders_fmt.rename(columns={col: 'address'}, inplace=True)
    for col in holders_fmt.columns:
        if 'value' in col:
            holders_fmt[col] = holders_fmt[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else x)
    if not holders_fmt.empty:
        st.dataframe(holders_fmt, use_container_width=True)
    else:
        st.info('No holder data available for this analysis.')

    st.markdown('---')
    # Net difference summary at the bottom
    net_diff, total_buys, total_sells = calculate_net_difference_simple(buyers_df, sellers_df)
    st.subheader(f"Net Difference (Top {top_n} Buyers - Top {top_n} Sellers): ${net_diff:,.2f}")
    st.caption(f"Total bought: ${total_buys:,.2f}")
    st.caption(f"Total sold: ${total_sells:,.2f}")

with col2:
    st.markdown('### Whale Transactions')
    if whales_df is not None and not whales_df.empty:
        whales_fmt = whales_df.copy()
        for col in whales_fmt.columns:
            if 'value' in col:
                whales_fmt[col] = whales_fmt[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else x)
        st.dataframe(whales_fmt, use_container_width=True)
    else:
        st.info('No whale transactions found or file missing for this analysis.')

    st.markdown('---')
    st.markdown('### All Transactions (Raw Data)')
    raw_fmt = raw_df.copy()
    for col in raw_fmt.columns:
        if 'value' in col:
            raw_fmt[col] = raw_fmt[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else x)
    if not raw_fmt.empty:
        st.dataframe(raw_fmt, use_container_width=True)
        st.markdown('---')
        st.subheader('Export Raw Transactions Data')
        with open(os.path.join(output_dir, "outputs.csv"), "rb") as f:
            st.download_button(
                label="Download Raw Transactions CSV",
                data=f,
                file_name="outputs.csv",
                mime="text/csv"
            )
    else:
        st.info('No raw data available to export.')

st.info("All data is loaded from the latest CSVs in the 'output' folder. Use the sidebar to run new analyses.")
