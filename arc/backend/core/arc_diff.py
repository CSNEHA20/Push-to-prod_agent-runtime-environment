"""
ARC Diff Engine - Side-by-Side Run Trace Comparison
Compares two agent execution sessions, aligns steps, highlights context/prompt/output differences,
and pinpoints the exact step index where reasoning diverged.
"""

from typing import Dict, Any, List

class SessionDiffer:
    def compare_sessions(
        self,
        session_a: Dict[str, Any],
        session_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        steps_a = session_a.get("steps", [])
        steps_b = session_b.get("steps", [])

        max_len = max(len(steps_a), len(steps_b))
        aligned_steps = []
        divergence_index = None

        for idx in range(max_len):
            step_a = steps_a[idx] if idx < len(steps_a) else None
            step_b = steps_b[idx] if idx < len(steps_b) else None

            # Detect divergence
            is_different = False
            diff_reasons = []

            if step_a and step_b:
                conf_a = step_a.get("confidence", 1.0)
                conf_b = step_b.get("confidence", 1.0)
                if abs(conf_a - conf_b) > 0.1:
                    is_different = True
                    diff_reasons.append(f"Confidence divergence: {int(conf_a*100)}% vs {int(conf_b*100)}%")

                out_a = str(step_a.get("output", "") or step_a.get("decision", ""))
                out_b = str(step_b.get("output", "") or step_b.get("decision", ""))
                if out_a != out_b:
                    is_different = True
                    diff_reasons.append("Decision / tool output mismatch")

                context_a = str(step_a.get("context", ""))
                context_b = str(step_b.get("context", ""))
                if context_a != context_b:
                    is_different = True
                    diff_reasons.append("Context firewall input mismatch")
            else:
                is_different = True
                diff_reasons.append("Execution trace length divergence")

            if is_different and divergence_index is None:
                divergence_index = idx

            aligned_steps.append({
                "step_index": idx + 1,
                "step_a": step_a,
                "step_b": step_b,
                "is_divergent": is_different,
                "diff_reasons": diff_reasons
            })

        return {
            "session_a_id": session_a.get("session_id", "session_a"),
            "session_b_id": session_b.get("session_id", "session_b"),
            "divergence_step_index": (divergence_index + 1) if divergence_index is not None else None,
            "total_aligned_steps": max_len,
            "aligned_steps": aligned_steps,
            "summary": f"Divergence detected at Step {divergence_index + 1}: {aligned_steps[divergence_index]['diff_reasons'][0]}" if divergence_index is not None else "Both execution runs followed identical decision paths."
        }
