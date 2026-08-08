"""
ARC SDK Example 01: Quickstart
Demonstrates initializing ARC, creating a protected ARCAgent, calling Claude, and executing protected tools.
"""

import arc

# 1. Initialize credentials and configuration
arc.init(
    api_key="arc_dev_key",
    anthropic_api_key="mock-key",
    server_url="http://localhost:8000",
    dashboard_url="http://localhost:3000",
)

print(f"[ARC] Using ARC SDK v{arc.__version__}")

# 2. Instantiate ARC Agent wrapper (enable mock_mode for offline testing)
agent = arc.Agent(
    name="Financial Analyst Agent",
    task="Summarize market trends and financial reports",
    mock_mode=True,
)

print(f"[ARC] Session ID: {agent.session_id}")
print(f"[ARC] Dashboard URL: {agent.dashboard_url}")

# 3. Call Claude via ARCAgent (with Flight Recorder & Context Firewall active)
response = agent.call_claude(
    messages=[{"role": "user", "content": "What are key indicators of startup health?"}],
)

print(f"[ARC] Response: {response[:120]}...")

# 4. Execute a protected tool
def calculate_runway(cash: float, burn_rate: float) -> float:
    return cash / burn_rate

runway_months = agent.run_tool("calculate_runway", {"cash": 1200000, "burn_rate": 100000}, calculate_runway)
print(f"[ARC] Tool Output (Runway Months): {runway_months}")

# 5. Mark session complete via arc.run()
result = arc.run(agent)
print("[ARC] Agent session complete:", result)
