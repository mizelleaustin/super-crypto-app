import asyncio
import pandas as pd
import streamlit as st
from research_agent import crypto_data_store  
from graphing import plot_candlestick_from_store, plot_line_chart_from_store

async def graphing_tool(user_input: str):
    st.info(f"📩 Received graphing request: {user_input}")

    ticker = user_input.strip().upper()
    if not ticker:
        st.warning("❌ No ticker found in prompt.")
        return

    st.success(f"✅ Ticker to graph: {ticker}")

    if ticker not in crypto_data_store or crypto_data_store[ticker].empty:
        st.warning(f"❌ No data found for {ticker}. Please fetch data first.")
        return

    if isinstance(crypto_data_store[ticker], list):
        st.info(f"🔄 Converting raw list data to DataFrame for {ticker}")
        raw = crypto_data_store[ticker]
        df = pd.DataFrame(raw)

        if "time" not in df.columns or not all(col in df.columns for col in ["open", "high", "low", "close"]):
            st.warning(f"❌ Raw data for {ticker} is missing required fields.")
            return

        df["Date"] = pd.to_datetime(df["time"])
        df["Ticker"] = ticker
        df = df[["Date", "open", "high", "low", "close", "Ticker"]]
        df.columns = ["Date", "Open", "High", "Low", "Close", "Ticker"]
        df = df.drop_duplicates().sort_values("Date")
        crypto_data_store[ticker] = df

    candlestick_fig = plot_candlestick_from_store(crypto_data_store, ticker)
    line_fig = plot_line_chart_from_store(crypto_data_store, ticker)
    return candlestick_fig, line_fig

async def graphing_agent(user_input):
    ticker = user_input
    if ticker not in crypto_data_store or not crypto_data_store[ticker]:
        st.warning(f"❌ No historical data found for {ticker}. Cannot generate report.")
        return

    st.info(f"📊 Running graphing agent for {ticker}...")
    result = await graphing_tool(user_input)
    if result:
        candlestick_fig, line_fig = result
        st.subheader(f"📈 Candlestick Chart for {user_input}")
        st.plotly_chart(candlestick_fig, use_container_width=True)
        st.subheader(f"📉 Line Chart for {user_input}")
        st.plotly_chart(line_fig, use_container_width=True)
    else:
        st.warning("No chart data available for this ticker.")

if __name__ == "__main__":
    asyncio.run(graphing_agent("BTC-USD"))