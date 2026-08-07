# ARC - Agent Runtime Core

**The missing layer between Claude and the real world.**

![ARC](https://img.shields.io/badge/ARC-Agent_Runtime_Core-blue)
![Hackathon](https://img.shields.io/badge/Hackathon-Push_to_Prod-green)
![Anthropic](https://img.shields.io/badge/Powered_By-Claude-orange)

---

## 🎯 The Problem

Right now when you give Claude an agentic task — it either works perfectly or fails silently and you have no idea why, what it knew, what it decided, or how to fix it.

There's no black box recorder. No memory that persists correctly. No recovery when it breaks. No way to verify it did what it was supposed to.

**ARC is that missing layer.**

---

## 🚀 What ARC Actually Is

Three things fused into one runtime:

### 1. 🛫 Flight Recorder
*(From TRACE)*

Every single thing the agent does gets recorded:
- What context it had at each decision point
- What it decided and why
- What tools it called
- What it was uncertain about
- Where it failed

When something goes wrong — and it will — you don't guess. You replay exactly what happened. Step by step. Like Chrome DevTools but for agent reasoning.

**The demo moment:** Agent fails on a complex task. You open ARC. You see the exact decision where it went wrong, what context it was missing, and why. You fix it in one line. Run again. Perfect.

### 2. 🧠 Context Firewall
*(From ContextOS)*

Right now agents get confused because they receive too much context, contradictory context, or stale context. They hallucinate not because they're dumb — but because nobody is managing what they know.

ARC sits between your data and Claude and does three things:
- **Relevance filtering** — only sends what actually matters for this specific task
- **Conflict resolution** — if two sources say different things, ARC flags it before Claude acts on wrong information
- **Provenance tracking** — every piece of context is tagged with where it came from, when, and how confident it is

Claude doesn't get a dump of information. It gets curated, verified, sourced context.

**The demo moment:** Same agent, same task. Without ARC — hallucinates because it mixed up two conflicting documents. With ARC — flags the conflict, asks for clarification, executes correctly.

### 3. ⚡ Recovery Engine
*(TRACE + ContextOS combined)*

When an agent fails mid-task — currently everything dies. You restart from zero.

ARC checkpoints agent state continuously. When failure happens:
- It knows exactly where execution stopped
- It knows what context was valid at that point
- It recovers and continues from the last good checkpoint

Like Git commits but for agent execution.

**The demo moment:** Agent is 7 steps into a 10-step task. Network fails. External API returns garbage. Normally — dead. With ARC — recovers, replays from step 6, completes the task.

---

## 🏗️ Architecture

```
Your App
    ↓
ARC Runtime Layer
    ├── Context Firewall (what Claude knows)
    ├── Flight Recorder (what Claude did)
    └── Recovery Engine (what Claude retries)
    ↓
Claude
    ↓
Tools / APIs / World
```

Claude doesn't change. Your app doesn't change much. ARC sits in the middle and makes everything reliable.

---

## 🏆 Why This Wins the Hackathon

| Criterion | How ARC Hits It |
|-----------|-----------------|
| **New frontier capability** | Nobody has built agent reliability infrastructure on top of Claude |
| **Infrastructure others build on** | Every team building Claude agents needs this immediately |
| **Redefines a category** | LangGraph, CrewAI do orchestration — ARC does reliability. Completely different |
| **Technically deep** | Flight recorder + context firewall + recovery is genuinely hard engineering |
| **Claude as the core** | ARC makes Claude agents production-ready — Anthropic wants this to exist |

### Why Anthropic Judges Specifically Will Love This

They built Claude. They want people to build serious things with Claude. But right now every developer building Claude agents hits the same wall — unreliability in production.

You walk in and say:

> "We built the reliability layer that makes Claude agents production-ready. Here's the flight recorder showing exactly what Claude decided and why. Here's the context firewall preventing hallucination from bad inputs. Here's the recovery engine that means a Claude agent never fails silently again."

That's not a hackathon project to them. That's infrastructure they wish existed.

---

## 🛠️ What We Built in 2 Days

### Day 1:
- ✅ Flight recorder — wrap Claude API calls, log full decision trace, build the replay visualizer
- ✅ Context firewall — relevance scoring, conflict detection between sources
- ✅ Basic dashboard showing agent execution in real time

### Day 2:
- ✅ Recovery engine — checkpoint system, failure detection, resume from last good state
- ✅ Demo scenario — build one compelling end-to-end agent task that fails without ARC and works perfectly with it
- ✅ Clean UI that shows the flight recorder replay visually

---

## 🎬 The Demo Flow

**Step 1:** Show a Claude agent doing a complex real task. Research a company, write a report, send a summary. Works fine.

**Step 2:** Introduce chaos. Conflicting documents. API failure midway. Bad context injected.

**Step 3:** Without ARC — agent produces wrong output silently. No idea why.

**Step 4:** Turn on ARC. Run again. Context firewall catches the conflict. Flight recorder shows every decision. Recovery engine handles the API failure. Agent completes correctly.

**Step 5:** Open the flight recorder. Show the judges exactly what Claude was thinking at each step. Show the context provenance. Show the recovery checkpoint.

Judges lose their minds.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Anthropic API Key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/agent-runtime-core.git
cd agent-runtime-core

# Backend setup
cd arc/backend
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Frontend setup
cd ../frontend
npm install
npm run dev

# Run the backend
cd ../backend
python main.py
```

### Usage

```python
from arc_sdk import ARC

# Initialize ARC
arc = ARC(api_key="your-anthropic-api-key")

# Wrap your Claude agent
@arc.agent
def my_agent(task):
    # Your agent logic here
    response = claude.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": task}]
    )
    return response

# Run with ARC
result = my_agent("Research company X and write a report")

# Access flight recorder
arc.flight_recorder.replay()

# View context provenance
arc.context_firewall.get_provenance()

# Recover from failure
arc.recovery_engine.resume_from_checkpoint()
```

---

## 📁 Project Structure

```
agent-runtime-core/
├── arc/
│   ├── backend/           # Python backend with ARC runtime
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core ARC logic
│   │   ├── main.py       # FastAPI server
│   │   └── requirements.txt
│   ├── frontend/         # React dashboard
│   │   ├── src/
│   │   ├── package.json
│   │   └── index.html
│   ├── sdk/              # Python SDK
│   │   └── arc_sdk/
│   └── demo/             # Demo agent
│       └── demo_agent.py
├── docs/                 # Documentation
├── docker-compose.yml    # Docker setup
└── README.md
```

---

## 🌟 The Startup Vision

### Open Source Core
- Gets adoption fast
- Community contributions
- Standard for agent reliability

### Paid Cloud Version
- Hosted ARC for teams building Claude agents
- Managed infrastructure
- Analytics and insights

### Enterprise
- Compliance, audit logs, SOC2
- Every enterprise deploying agents needs this for legal reasons alone

**Every company deploying Claude agents in production will pay for this. That's the entire Claude enterprise market.**

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas for Contribution
- Flight recorder visualizations
- Context filtering algorithms
- Recovery strategies
- Dashboard UI improvements
- Additional language SDKs

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built for **Push to Prod Hackathon** organized by:
- **Anthropic**
- **Elevate**
- **Mesa School of Business**

Bangalore, 2026

---

## 📞 Contact

- **Twitter:** [@arc_runtime](https://twitter.com/arc_runtime)
- **GitHub:** [agent-runtime-core](https://github.com/yourusername/agent-runtime-core)
- **Discord:** [Join our community](https://discord.gg/arc)

---

**Made with ❤️ for the Claude agent ecosystem**
