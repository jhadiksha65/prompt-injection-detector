"""
risk_scoring.py
Computes normalized risk scores (0-100), risk levels, and security decisions
by fusing rule-based heuristic outputs with machine learning probability estimates.
"""

from typing import Dict, Any
from .threat_taxonomy import (
    ThreatCategory,
    RiskLevel,
    SecurityDecision,
    map_risk_level,
    map_security_decision
)


class RiskScorer:
    """
    Combines rule-based score and ML probability using configurable weights and safety floors.
    """

    def __init__(self, rule_weight: float = 0.40, ml_weight: float = 0.60):
        self.rule_weight = rule_weight
        self.ml_weight = ml_weight

    def calculate_risk(self, rule_result: Dict[str, Any], ml_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fuses Rule and ML scores into a single 0-100 Risk Score and determines
        the risk level, attack classification, and security decision.
        """
        rule_score = float(rule_result.get("rule_score", 0.0))
        ml_score = float(ml_result.get("ml_score", 0.0))
        ml_available = ml_result.get("ml_available", False)

        if ml_available:
            fused_score = (self.rule_weight * rule_score) + (self.ml_weight * ml_score)
        else:
            # Fallback to rule score only if ML is not loaded
            fused_score = rule_score

        # Critical Rule Floor: High-confidence heuristic trigger guarantees at least high risk
        if rule_score >= 90.0:
            fused_score = max(fused_score, 85.0)
        elif rule_score >= 80.0:
            fused_score = max(fused_score, 70.0)

        # Cap fused score in [0.0, 100.0]
        final_risk_score = round(max(0.0, min(100.0, fused_score)), 2)

        risk_level = map_risk_level(final_risk_score)
        decision = map_security_decision(final_risk_score)

        # Determine attack classification
        if final_risk_score > 30.0:
            # Use rule category if rule was triggered; otherwise default to direct injection or generic threat
            if rule_result.get("attack_type") != ThreatCategory.BENIGN.value:
                attack_type = rule_result.get("attack_type")
            else:
                attack_type = ThreatCategory.DIRECT_INJECTION.value
        else:
            attack_type = ThreatCategory.BENIGN.value

        # Generate human-readable reason
        if decision == SecurityDecision.BLOCK:
            reason = rule_result.get("reason") if rule_result.get("rule_triggered") else f"High adversarial probability detected ({final_risk_score}% risk)."
        elif decision == SecurityDecision.WARNING:
            reason = "Potential prompt injection indicators or elevated risk detected. Review before submission."
        else:
            reason = "No prompt injection patterns detected. Prompt is safe."

        return {
            "risk_score": final_risk_score,
            "risk_level": risk_level.value,
            "attack_type": attack_type,
            "decision": decision.value,
            "reason": reason,
            "is_injection": decision == SecurityDecision.BLOCK.value or final_risk_score > 60.0,
            "classification": "MALICIOUS" if final_risk_score > 50.0 else "BENIGN"
        }
