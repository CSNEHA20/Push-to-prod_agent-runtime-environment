"""
ARC SDK Example 02: Tracing, Replay, and Inspection
Demonstrates calling top-level arc.trace(), arc.replay(), and arc.inspect().
"""

import arc

# Initialize SDK
arc.init(server_url="http://localhost:8000")

agent = arc.Agent(name="Research Agent", task="Trace & Replay Demo", mock_mode=True)

# Execute a protected call
agent.call_claude([{"role": "user", "content": "Explain quantum computing briefly."}])
session_id = agent.session_id

print(f"[ARC] Session ID: {session_id}")

try:
    # 1. Inspect session details
    session_info = arc.inspect(session_id)
    print(f"[ARC] Session Status: {session_info.status} (Agent: {session_info.agent_name})")

    # 2. Get step trace
    trace_steps = arc.trace(session_id)
    print(f"[ARC] Trace Steps Count: {len(trace_steps)}")

    # 3. Get visual replay timeline
    replay_data = arc.replay(session_id)
    print(f"[ARC] Replay Session ID: {replay_data.session_id}")

except Exception as e:
    print(f"[ARC Notice] Server offline fallback: {e}")
