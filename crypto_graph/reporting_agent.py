import asyncio
import pandas as pd
import streamlit as st
from research_agent import crypto_data_store

async def reporting_agent(user_input: str):
    ticker = user_input.strip().upper()
    df = crypto_data_store.get(ticker)

    if df is None or (isinstance(df, list) and not df) or (isinstance(df, pd.DataFrame) and df.empty):
        st.warning(f"❌ No usable historical data found for {ticker}. Please fetch it first.")
        return

    if isinstance(df, list):
        df = pd.DataFrame(df)
        df["Date"] = pd.to_datetime(df["time"])
        df["Ticker"] = ticker
        df = df[["Date", "open", "high", "low", "close", "volume", "Ticker"]]
        df.columns = ["Date", "Open", "High", "Low", "Close", "Volume", "Ticker"]
        df = df.drop_duplicates().sort_values("Date")
        crypto_data_store[ticker] = df

    last_price = df["Close"].iloc[-1] if "Close" in df.columns else "N/A"
    avg_volume = df["Volume"].mean() if "Volume" in df.columns else "N/A"
    row_count = len(df)

    st.subheader(f"📊 Summary for {ticker}")
    st.write(f"- Records Analyzed: {row_count}")
    st.write(f"- Last Closing Price: ${last_price:,.2f}")
    st.write(f"- Average Volume: {avg_volume:,.2f}")

if __name__ == "__main__":
    asyncio.run(reporting_agent("BTC-USD"))