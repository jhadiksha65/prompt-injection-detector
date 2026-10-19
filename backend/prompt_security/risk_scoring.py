"""
risk_scoring.py
Computes normalized risk scores (0-100), risk levels, and security decisions
by fusing rule-based heuristic outputs with machine learning probability estimates.
"""

from typing import Dict, Any
from .threat_taxonomy import (
    ThreatCategory,
    BinaryLabel,
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

        is_hard_negative = rule_result.get("attack_type") == ThreatCategory.SAFE_HARD_NEGATIVE.value

        if not is_hard_negative:
            # 1. Rule Floor: Explicit heuristic attack patterns guarantee high/block severity
            if rule_score >= 85.0:
                fused_score = max(fused_score, 85.0)
            elif rule_score >= 70.0:
                fused_score = max(fused_score, 65.0)
            elif rule_score >= 45.0:
                fused_score = max(fused_score, 45.0)

            # 2. ML Safety Floor: Moderate detection above threshold ensures at least MEDIUM severity
            if ml_available:
                malicious_prob = ml_result.get("malicious_probability", 0.0)
                if malicious_prob >= 0.54:
                    fused_score = max(fused_score, 45.0)
                # When heuristic rules do not trigger, allow high-confidence ML to drive the risk score
                if not rule_result.get("rule_triggered") and malicious_prob >= 0.90:
                    fused_score = max(fused_score, ml_score)
        else:
            # Safe security-related educational inquiries must never be blocked or warned
            fused_score = min(fused_score, 25.0)

        # Cap fused score in [0.0, 100.0]
        final_risk_score = round(max(0.0, min(100.0, fused_score)), 2)

        if is_hard_negative:
            final_risk_score = min(final_risk_score, 25.0)
            risk_level = RiskLevel.LOW
            decision = SecurityDecision.ALLOW
            attack_type = ThreatCategory.SAFE_HARD_NEGATIVE.value
            is_malicious_classification = False
            reason = rule_result.get("reason", "Legitimate educational or analytical inquiry regarding cybersecurity/AI safety.")
        else:
            risk_level = map_risk_level(final_risk_score)
            decision = map_security_decision(final_risk_score)
            is_malicious_classification = final_risk_score > 30.0

            # Determine attack classification
            if is_malicious_classification:
                rule_attack = rule_result.get("attack_type")
                if rule_attack and rule_attack not in (ThreatCategory.BENIGN.value, ThreatCategory.SAFE_HARD_NEGATIVE.value):
                    attack_type = rule_attack
                else:
                    # Honest fallback when ML model detects adversarial probability but rules have no specific category match
                    attack_type = ThreatCategory.UNCLASSIFIED.value
            else:
                attack_type = ThreatCategory.BENIGN.value

            # Generate human-readable reason
            if decision == SecurityDecision.BLOCK:
                reason = rule_result.get("reason") if rule_result.get("rule_triggered") else f"High adversarial probability detected ({final_risk_score}% risk)."
            elif decision == SecurityDecision.WARNING:
                reason = rule_result.get("reason") if rule_result.get("rule_triggered") else "Potential prompt injection indicators or elevated risk detected. Review before submission."
            else:
                reason = "No prompt injection patterns detected. Prompt is safe."

        # Separate binary classification from risk severity:
        return {
            "risk_score": final_risk_score,
            "risk_level": risk_level.value,
            "attack_type": attack_type,
            "decision": decision.value,
            "reason": reason,
            "is_injection": decision == SecurityDecision.BLOCK.value or final_risk_score > 60.0,
            "classification": BinaryLabel.MALICIOUS.value if is_malicious_classification else BinaryLabel.BENIGN.value
        }
