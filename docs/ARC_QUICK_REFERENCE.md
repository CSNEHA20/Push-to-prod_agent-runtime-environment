# ARC — Quick Reference Card
## Keep this open on the day

---

## One-Line Pitch
> "ARC is the missing reliability layer between Claude and the real world — flight recorder, context firewall, and recovery engine for AI agents."

## The Three Engines
| Engine | What it does | The wow moment |
|---|---|---|
| ✈️ Flight Recorder | Records every Claude decision | Replay shows exactly where it went wrong |
| 🛡️ Context Firewall | Filters what Claude knows | Catches conflicting data sources live |
| ⚡ Recovery Engine | Checkpoints + resumes | Agent recovers from failure mid-task |

## Tech Stack
- Backend: Python + FastAPI + PostgreSQL + Redis
- Frontend: React + Vite + Tailwind
- AI: Claude claude-sonnet-4-6 via Anthropic SDK
- Real-time: WebSockets

## Start Commands
```bash
# Start everything
docker-compose up

# Run demo
python demo/hackathon_demo.py

# Frontend
http://localhost:3000

# Backend
http://localhost:8000
```

## Demo Flow
1. Run agent WITHOUT ARC → fails silently
2. Run agent WITH ARC → watch live trace
3. Conflict detected → context firewall fires
4. API failure → recovery engine kicks in
5. Open replay → show flight recorder

## If Demo Breaks
- Keep talking, switch to dashboard screenshots
- "The live demo showed us a real recovery — which is appropriate"
- Show the code instead — it's impressive on its own

## Judging Criteria Checklist
- ✅ New frontier capability — agent reliability infra doesn't exist
- ✅ Billion dollar idea — every Claude agent deployment needs this
- ✅ Redefines a category — debugging AI is now visual
- ✅ Interface that doesn't exist — flight recorder replay for AI
- ✅ Infrastructure others build on — SDK for all Claude agent teams
- ✅ Uses Claude as core — context firewall runs on Claude

## Team
- Vishal: Backend + ARC engines + SDK
- Sneha: Frontend + Dashboard + Demo UI
