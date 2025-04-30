# main.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'crypto_graph')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'news_agent')))

import asyncio
import crypto_graph.manager_agent

if __name__ == "__main__":
    user_input = input("Enter the trading symbol for a cryptocurrency (e.g., BTC-USD): ")
    asyncio.run(crypto_graph.manager_agent.manager_agent(user_input))

