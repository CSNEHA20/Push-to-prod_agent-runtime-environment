"""
ARC Score Calculator - Agent Quality Rating System
Computes a composite rating (0 to 100) across 5 core dimensions:
Reliability, Context Quality, Reasoning Depth, Efficiency, and Recovery.
"""

from typing import Dict, Any, List

class ARCScoreCalculator:
    def calculate_score(self, session: Dict[str, Any]) -> Dict[str, Any]:
        steps = session.get("steps", [])
        status = session.get("status", "running")
        recovered = session.get("recovered", False) or session.get("has_recovered", False)
        context_stats = session.get("context_stats", {})

        # 1. Reliability (Base score from step success & status)
        failed_steps = sum(1 for s in steps if s.get("status") == "failed" or "error" in str(s.get("output", "")).lower())
        total_steps = max(len(steps), 1)
        step_success_rate = (total_steps - failed_steps) / total_steps
        
        reliability = step_success_rate * 90.0
        if status == "completed":
            reliability += 10.0
        elif status == "failed" and not recovered:
            reliability -= 30.0
        reliability = round(min(max(reliability, 10.0), 100.0), 1)

        # 2. Context Quality
        avg_relevance = context_stats.get("avg_relevance", 0.85)
        passed_ratio = 1.0 - context_stats.get("rejected_ratio", 0.15)
        context_quality = round(min(max((avg_relevance * 60.0 + passed_ratio * 40.0), 10.0), 100.0), 1)

        # 3. Reasoning Depth
        confidences = [s.get("confidence", 0.85) for s in steps if s.get("confidence") is not None]
        avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.85
        reasoning_depth = round(min(max(avg_conf * 100.0, 10.0), 100.0), 1)

        # 4. Efficiency
        efficiency = 85.0
        if total_steps > 15:
            efficiency -= (total_steps - 15) * 2.0
        elif total_steps < 8:
            efficiency += 10.0
        efficiency = round(min(max(efficiency, 20.0), 100.0), 1)

        # 5. Recovery Score
        recovery_score = 95.0 if recovered else (80.0 if status == "completed" else 50.0)

        # Composite Score Calculation
        overall = round(
            (reliability * 0.30) +
            (context_quality * 0.25) +
            (reasoning_depth * 0.20) +
            (efficiency * 0.15) +
            (recovery_score * 0.10),
            1
        )

        return {
            "overall": overall,
            "metrics": {
                "reliability": reliability,
                "context_quality": context_quality,
                "reasoning_depth": reasoning_depth,
                "efficiency": efficiency,
                "recovery": recovery_score
            },
            "rating_label": self._get_label(overall)
        }

    def _get_label(self, score: float) -> str:
        if score >= 90:
            return "Production Ready (S-Tier)"
        elif score >= 80:
            return "High Reliability (A-Tier)"
        elif score >= 70:
            return "Moderate Risk (B-Tier)"
        else:
            return "Needs Reliability Tuning (C-Tier)"
