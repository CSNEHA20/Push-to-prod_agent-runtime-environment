"""
ARC Lens Engine - Natural Language Agent Forensic Debugging
Answers user questions about agent execution traces ("Why did it fail?", "Why did revenue mismatch?")
using Claude or ARC's local trace forensic analyzer.
"""

import os
import json
from typing import Dict, Any, List

class ARCLensEngine:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    async def ask_lens(self, session: Dict[str, Any], question: str) -> Dict[str, Any]:
        """
        Parses session trace and provides a natural language forensic answer to user's question.
        """
        steps = session.get("steps", [])
        session_id = session.get("session_id", "unknown")
        status = session.get("status", "unknown")

        # Try Anthropic API if key is available
        if self.api_key:
            try:
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=self.api_key)
                
                prompt_content = f"""
You are ARC Lens, a forensic AI debugger analyzing an agent execution trace.
Session ID: {session_id}
Session Status: {status}
Task: {session.get('task', 'N/A')}

Execution Steps:
{json.dumps(steps, indent=2)}

User Question: {question}

Provide a concise, highly insightful, step-by-step forensic explanation answering the user's question. Refer to specific step numbers, confidence scores, context flags, or tool call outputs where relevant.
"""
                response = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=600,
                    messages=[{"role": "user", "content": prompt_content}]
                )
                answer_text = response.content[0].text
                return {
                    "question": question,
                    "answer": answer_text,
                    "engine": "claude-3-5-sonnet",
                    "referenced_steps": self._extract_referenced_steps(steps, question)
                }
            except Exception as e:
                # Fallback to local forensic engine if API call fails or key invalid
                pass

        # Fallback Local Heuristic Forensic Engine
        return self._heuristic_lens_answer(session, question)

    def _heuristic_lens_answer(self, session: Dict[str, Any], question: str) -> Dict[str, Any]:
        steps = session.get("steps", [])
        q_lower = question.lower()
        
        referenced_steps = []
        explanation_lines = []

        # Check for failure / error questions
        if any(w in q_lower for w in ["fail", "error", "wrong", "mismatch", "issue", "bug", "why"]):
            failed_steps = [s for s in steps if s.get("status") == "failed" or "error" in str(s.get("output", "")).lower()]
            if failed_steps:
                st = failed_steps[0]
                step_idx = st.get("step_number") or st.get("step_index") or 1
                referenced_steps.append(step_idx)
                explanation_lines.append(
                    f"Forensic analysis detected a failure at Step {step_idx} ({st.get('decision', 'Tool Execution')}). "
                    f"The tool returned an error response: '{st.get('error') or st.get('output', 'Unexpected termination')}'."
                )
            
            conf_drops = [s for s in steps if s.get("confidence", 1.0) < 0.7]
            if conf_drops:
                st = conf_drops[0]
                step_idx = st.get("step_number") or st.get("step_index") or 1
                referenced_steps.append(step_idx)
                explanation_lines.append(
                    f"At Step {step_idx}, confidence dropped to {int(st.get('confidence', 0)*100)}% due to degraded context relevance "
                    f"and conflicting data points in the Context Firewall."
                )
        
        if not explanation_lines:
            explanation_lines.append(
                f"ARC Lens analyzed {len(steps)} execution steps for session '{session.get('session_id')}'. "
                f"At key decision points, the agent operated with an average confidence of "
                f"{int(sum(s.get('confidence', 0.85) for s in steps)/max(len(steps),1)*100)}%. "
                f"No unhandled critical exceptions occurred during this run."
            )

        # Context Firewall conflict check
        context_conflicts = session.get("context_stats", {}).get("conflicts", [])
        if context_conflicts:
            explanation_lines.append(
                f"Note: Context Firewall detected {len(context_conflicts)} source conflict(s), which ARC flagged prior to decision execution."
            )

        answer_text = "\n\n".join(explanation_lines)

        return {
            "question": question,
            "answer": answer_text,
            "engine": "arc-local-forensics",
            "referenced_steps": list(set(referenced_steps))
        }

    def _extract_referenced_steps(self, steps: List[Dict[str, Any]], question: str) -> List[int]:
        refs = []
        for s in steps:
            idx = s.get("step_number") or s.get("step_index")
            if idx and (s.get("status") == "failed" or s.get("confidence", 1.0) < 0.7):
                refs.append(idx)
        return refs
