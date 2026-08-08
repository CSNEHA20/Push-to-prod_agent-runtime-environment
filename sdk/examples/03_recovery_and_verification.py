"""
ARC SDK Example 03: Recovery & Verification
Demonstrates top-level arc.recover() and arc.verify().
"""

import arc

arc.init(server_url="http://localhost:8000")

agent = arc.Agent(name="Compliance Agent", task="Check data conflict")
session_id = agent.session_id

# Verify sample trace with Context Firewall rules
sample_trace = [
    {
        "step_id": "step-1",
        "action": "call_claude",
        "content": "Series A funding total was $7.3M",
        "context": "Deck A states $7.3M",
    },
    {
        "step_id": "step-2",
        "action": "call_claude",
        "content": "Series A funding total was $8.1M",
        "context": "Deck B states $8.1M",
    },
]

try:
    # 1. Run Context Firewall verification
    verification_result = arc.verify(sample_trace)
    print("[ARC] Verification Result:", verification_result)

    # 2. Inspect session recovery status
    recovery_info = arc.recover(session_id)
    print("[ARC] Recovery Info:", recovery_info)

except Exception as e:
    print(f"[ARC Notice] (Server offline fallback notice) {e}")
