# Insights Dashboard for Crypto Transactions

A unified dashboard for analyzing ERC20 token transactions on Ethereum and other EVM-compatible blockchains. It leverages the Moralis API for blockchain data and CoinGecko for price data, providing insights into top buyers, sellers, holders, whale transactions, and more.

## Features
- Analyze any ERC20 token by symbol (e.g., USDT, USDC, DAI, SHIB)
- Whale transaction detection (customizable USD threshold)
- Top buyers, sellers, and holders summaries
- Full raw transaction export
- Streamlit-powered interactive dashboard
- CoinGecko integration for real-time price data
- Robust error handling and clear user guidance

## Requirements
- Python 3.8+
- Moralis Python SDK (`moralis`)
- Streamlit
- pandas
- requests
- python-dotenv

## Setup
1. **Clone the repository**
2. **Install dependencies** (ideally in a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Create a `.env` file with your Moralis API key and OpenAI API key (for chatbot):
     ```env
     MORALIS_API_KEY=your-moralis-key
     OPENAI_API_KEY=your-openai-key
     ```
4. **Run the dashboard:**
   ```bash
   streamlit run streamlit_dashboard.py
   ```

## Usage
- Enter an ERC20 token symbol (e.g., USDT, USDC, DAI, SHIB) in the sidebar and run analysis.
- View top buyers, sellers, holders, whale transactions, and all raw data in the dashboard.
- Download full raw transaction data as CSV.
- Use the chatbot for basic data insights and help.

## Notes
- **Native coins (like ETH, BNB, MATIC) are NOT supported** in this dashboard. Only ERC20 tokens are supported.
- All analytics are routed through `transaction_insights_module.py`.
- Data reloads after each analysis, so you can look up new tokens without refreshing the app.

## Project Structure
See `FILE_OVERVIEW.txt` for a brief description of each file and how the system works together.

## Troubleshooting
- If you see `ModuleNotFoundError: No module named 'moralis'`, install the Moralis SDK:
  ```bash
  pip install moralis
  ```
- For API issues, check your `.env` file and API keys.
- For further help, review logs and debug output in the terminal and dashboard.

---

**Built for robust, user-friendly crypto transaction analytics.**
