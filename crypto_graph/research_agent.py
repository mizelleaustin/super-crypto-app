import asyncio
import re
import streamlit as st
from financialdatasets import fetch_crypto_prices

crypto_data_store = {}

def extract_ticker(user_input: str):
    match = re.search(r"\b[A-Z]{2,5}-USD\b", user_input)
    ticker = match.group(0) if match else None
    st.info(f"🔍 Extracted Ticker: {ticker}")
    return ticker

async def crypto_data_tool(user_input: str):
    global crypto_data_store
    ticker = extract_ticker(user_input)
    if not ticker:
        st.warning("❌ No ticker found in prompt.")
        crypto_data_store["error"] = "Could not determine the cryptocurrency ticker."
        return

    st.success(f"✅ Extracted ticker: {ticker}")
    prices = fetch_crypto_prices(ticker)

    if not prices:
        st.warning(f"❌ No data returned for {ticker}.")
        return

    if isinstance(prices, dict) and "prices" in prices:
        prices = prices["prices"]

    if not isinstance(prices, list) or len(prices) == 0:
        st.warning("❌ No valid historical data found.")
        return

    if ticker not in crypto_data_store:
        crypto_data_store[ticker] = []

    crypto_data_store[ticker].extend(prices)
    st.success(f"📦 Stored {len(prices)} records for {ticker}")

async def research_agent(user_input):
    global crypto_data_store
    await crypto_data_tool(user_input)

if __name__ == "__main__":
    asyncio.run(research_agent("Fetch BTC-USD data"))