# ARC — Hackathon Pitch Script
## Push to Prod | August 8, 2026 | Bengaluru

---

## ⏱️ Total Time: 5 minutes

---

## SLIDE 1 — HOOK (20 seconds)

> *"Raise your hand if you've built something with Claude."*

[wait]

> *"Keep it up if it's ever failed and you had absolutely no idea why."*

[pause — most hands stay up]

> *"That's the problem we solved."*

---

## SLIDE 2 — THE PROBLEM (40 seconds)

> *"When you give Claude an agentic task today, one of two things happens.*
> *It works perfectly.*
> *Or it fails silently.*
> *No trace. No reason. No way to fix it.*
> 
> *There's no black box recorder. No memory management. No recovery when things break midway.*
> 
> *LangChain, CrewAI, AutoGen — they solve orchestration. How to chain calls.*
> Nobody has solved reliability. What happens when those chains break.*
> 
> *Every company trying to deploy Claude agents in production hits this exact wall.*"*

---

## SLIDE 3 — THE SOLUTION (30 seconds)

> *"We built ARC — Agent Runtime Core.*
> *The missing layer between Claude and the real world.*
> 
> *Three primitives fused into one runtime:*
> *A Flight Recorder — that records every decision Claude makes.*
> *A Context Firewall — that filters what Claude knows.*
> *A Recovery Engine — that brings agents back from failure.*
> 
> *Let us show you."*

---

## SLIDE 4 — LIVE DEMO (3 minutes)

### Act 1 — Without ARC (45 seconds)

> *"Here's a Claude agent doing a real task — researching a company, extracting financials, writing an investment brief.*
> *We inject a conflicting data source and an API failure midway.*
> *Watch what happens."*

[Run agent without ARC]
[Agent produces wrong output silently]

> *"Wrong answer. No error. No trace. No idea what happened.*
> *This is what every developer experiences today."*

---

### Act 2 — ARC ON (90 seconds)

> *"Same agent. Same task. Same chaos. ARC is on."*

[Run agent with ARC — dashboard visible on screen]

**As Flight Recorder populates:**
> *"Every decision Claude makes — recorded in real time. Every tool call. Every confidence level. Watch step 3 — confidence drops because Claude hit ambiguous data. That's visible now."*

**As Context Firewall fires:**
> *"There — conflict detected. Two sources disagree on the revenue figure. Seven point three billion vs eight point one billion. ARC catches it before Claude acts on the wrong number. It flags it, picks the more recent source, and continues."*

**As Recovery Engine triggers:**
> *"API failure at step 7. Without ARC — the run dies. Watch."*

[Recovery animation on dashboard]

> *"ARC detects the failure. Finds the checkpoint at step 6. Restores state. Retries. And the agent completes successfully.*
> *Zero data lost. Zero restart needed."*

---

### Act 3 — The Replay (45 seconds)

> *"Now here's the part no one has ever seen before.*
> *Open the Flight Recorder for that failed run.*
> *And replay it."*

[Open replay — steps animate one by one]

> *"Every step Claude took. Every decision. Every piece of context it had.*
> *The exact moment it would have gone wrong — and why.*
> *This is Chrome DevTools for AI agents."*

---

## SLIDE 5 — WHY THIS WINS (30 seconds)

> *"ARC isn't another chatbot. It's not a wrapper.*
> *It's the reliability infrastructure that makes Claude deployable in the real world.*
> 
> *Three months from now, every team building Claude agents in production will need this.*
> *We built it today.*
> 
> *ARC — because AI agents shouldn't fail silently."*

---

## ANTICIPATED QUESTIONS

**Q: Doesn't LangSmith already do this?**
> "LangSmith does observability — logs after the fact. ARC does active intervention — it filters context before Claude sees it, and recovers from failures in real time. It's the difference between a camera and a co-pilot."

**Q: How does the Context Firewall work technically?**
> "It uses Claude itself to score relevance and detect conflicts before the agent call. Every context chunk gets a relevance score. Conflicts get classified and resolved. Claude gets clean, sourced, verified context — not a dump."

**Q: What's the startup model?**
> "Open source SDK for adoption. ARC Cloud for teams — hosted dashboard, collaboration, retention. Enterprise tier for compliance — audit logs, SOC2, on-premise. Every company deploying Claude agents in production is the market."

**Q: Why Claude specifically?**
> "ARC is built around Claude's specific tool use format, message structure, and API patterns. The Context Firewall uses Claude to validate context. The confidence scoring is tuned to Claude's output patterns. It works with Claude — not around it."

---

## CLOSING LINE

> *"The world is about to run on AI agents.*
> *ARC makes sure they don't fail silently.*
> *Thank you."*

---
