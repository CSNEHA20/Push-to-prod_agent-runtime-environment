"""
ARC SDK Example 02: Tracing, Replay, and Inspection
Demonstrates calling top-level arc.trace(), arc.replay(), and arc.inspect().
"""

import arc

# Initialize SDK
arc.init(server_url="http://localhost:8000")

agent = arc.Agent(name="Research Agent", task="Trace & Replay Demo")

# Execute a call
agent.call_claude([{"role": "user", "content": "Explain quantum computing briefly."}])
session_id = agent.session_id

print(f"[ARC] Session ID: {session_id}")

try:
    # 1. Inspect session details
    session_info = arc.inspect(session_id)
    print("[ARC] Session Details:", session_info)

    # 2. Get step trace
    trace_data = arc.trace(session_id)
    print(f"[ARC] Trace Steps Count: {len(trace_data)}")

    # 3. Get visual replay timeline
    replay_data = arc.replay(session_id)
    print("[ARC] Replay Timeline Keys:", list(replay_data.keys()) if isinstance(replay_data, dict) else type(replay_data))

except Exception as e:
    print(f"[ARC Notice] (Server offline fallback notice) {e}")
