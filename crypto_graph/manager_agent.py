# manager_agent.py

from graphing_agent import graphing_tool
from reporting_agent import reporting_agent
from research_agent import research_agent

async def manager_agent(user_input: str):
    """
    Executes a fixed pipeline:
    1. Downloads data using research_agent
    2. Generates a report using reporting_agent
    3. Visualizes results using graphing_agent
    """

    print(f"🧠 Manager received input: {user_input}")

    # Step 1: Download Data
    print("🔁 Step 1: Fetching data...")
    await research_agent(user_input)

    # Step 2: Generate Report
    print("📝 Step 2: Writing report...")
    report = await reporting_agent(user_input)
    print(report)

    # Step 3: Generate Graph
    print("📊 Step 3: Creating graph...")
    graph = await graphing_tool(user_input)
    print(graph)
    print("✅ All agents executed successfully.")
