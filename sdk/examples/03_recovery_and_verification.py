"""
ARC SDK Example 03: Recovery & Verification
Demonstrates top-level arc.recover() and arc.verify().
"""

import arc

arc.init(server_url="http://localhost:8000")

agent = arc.Agent(name="Compliance Agent", task="Check data conflict", mock_mode=True)
session_id = agent.session_id

# Sample trace for Context Firewall verification
sample_trace = [
    {
        "step_id": "step-1",
        "step_type": "llm_call",
        "name": "Series A Funding",
        "input_data": {"query": "Deck A"},
        "output_data": {"text": "Series A funding total was $7.3M"},
    },
    {
        "step_id": "step-2",
        "step_type": "llm_call",
        "name": "Audit Report",
        "input_data": {"query": "Deck B"},
        "output_data": {"text": "Series A funding total was $8.1M"},
    },
]

try:
    # 1. Run Context Firewall verification
    verification_result = arc.verify(sample_trace)
    print(f"[ARC] Verification Status: {verification_result.firewall_status} (Is Valid: {verification_result.is_valid})")

    # 2. Inspect session recovery status
    recovery_info = arc.recover(session_id)
    print(f"[ARC] Recovery Status: {recovery_info.status}")

except Exception as e:
    print(f"[ARC Notice] Server offline fallback: {e}")
