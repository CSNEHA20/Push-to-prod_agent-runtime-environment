"""
ARC Predict Engine - Failure Prediction Before It Happens
Analyzes step confidence trends, context quality decay, and tool execution error rates to output failure probability.
"""

from typing import List, Dict, Any, Optional

class FailurePredictor:
    def __init__(self, risk_threshold: float = 60.0):
        self.risk_threshold = risk_threshold

    def predict_failure(
        self,
        steps: List[Dict[str, Any]],
        context_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes the trajectory of steps and context quality to predict failure risk.
        """
        if not steps:
            return {
                "will_fail": False,
                "risk_percent": 10.0,
                "reason": "Insufficient step history to predict failure.",
                "preemptive_checkpoint": False
            }

        risk_score = 15.0
        reasons = []

        # 1. Evaluate Confidence Score Trend
        confidences = [s.get("confidence", 1.0) for s in steps if s.get("confidence") is not None]
        if len(confidences) >= 2:
            recent_conf = confidences[-2:]
            if recent_conf[-1] < recent_conf[-2]:
                drop = recent_conf[-2] - recent_conf[-1]
                risk_score += drop * 80.0
                reasons.append(f"Confidence score dropped by {int(drop*100)}% over recent steps.")
            
            if recent_conf[-1] < 0.65:
                risk_score += 25.0
                reasons.append(f"Low step confidence detected ({int(recent_conf[-1]*100)}%).")

        # 2. Evaluate Context Firewall Quality
        if context_stats:
            rejected_ratio = context_stats.get("rejected_ratio", 0.0)
            avg_relevance = context_stats.get("avg_relevance", 1.0)
            if rejected_ratio > 0.4:
                risk_score += 20.0
                reasons.append(f"High context rejection rate ({int(rejected_ratio*100)}% filtered out).")
            if avg_relevance < 0.6:
                risk_score += 20.0
                reasons.append(f"Degraded context relevance ({int(avg_relevance*100)}% quality score).")

        # 3. Evaluate Tool Call Failures & Errors
        tool_failures = 0
        for step in steps[-3:]:
            output = str(step.get("output", "") or step.get("error", "")).lower()
            if "error" in output or "failed" in output or "timeout" in output or "exception" in output:
                tool_failures += 1
        
        if tool_failures > 0:
            risk_score += tool_failures * 25.0
            reasons.append(f"{tool_failures} tool execution error(s) in recent steps.")

        # Cap risk score between 5% and 98%
        final_risk = round(min(max(risk_score, 5.0), 98.0), 1)
        will_fail = final_risk >= self.risk_threshold

        main_reason = " | ".join(reasons) if reasons else "Execution telemetry indicates stable trajectory."

        return {
            "will_fail": will_fail,
            "risk_percent": final_risk,
            "reason": main_reason,
            "preemptive_checkpoint": will_fail
        }
