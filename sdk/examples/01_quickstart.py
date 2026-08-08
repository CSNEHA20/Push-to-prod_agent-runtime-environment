"""
ARC SDK Example 01: Quickstart
Demonstrates initializing ARC, creating a protected ARCAgent, and running a task.
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

# 2. Instantiate ARC Agent wrapper
agent = arc.Agent(
    name="Financial Analyst Agent",
    task="Summarize market trends and financial reports",
)

print(f"[ARC] Session ID: {agent.session_id}")
print(f"[ARC] Dashboard URL: {agent.dashboard_url}")

# 3. Call Claude via ARC Runtime (with Flight Recorder & Context Firewall active)
response = agent.call_claude(
    messages=[{"role": "user", "content": "What are key indicators of startup health?"}],
    context_sources=[
        {"name": "investor_deck.pdf", "content": "ARR grew 120% YoY to $12M."},
        {"name": "audit_report.pdf", "content": "ARR grew 120% YoY to $12M."},
    ],
)

print(f"[ARC] Response: {response[:120]}...")

# 4. Mark session complete via arc.run()
result = arc.run(agent)
print("[ARC] Agent session complete:", result)
