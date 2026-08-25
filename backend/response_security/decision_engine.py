"""
decision_engine.py
Layer 2 Response Security Engine orchestrating structural validation,
leakage scanning, response masking, and final egress security decision.
"""

from typing import Dict, Any
from .leakage_detector import ResponseLeakageDetector
from .validator import ResponseValidator


class ResponseSecurityEngine:
    """
    Evaluates LLM-generated responses before they reach the user.
    Protects against system prompt leakage, credential exposure, and PII disclosure.
    """

    def __init__(self):
        self.leakage_detector = ResponseLeakageDetector()
        self.validator = ResponseValidator()

    def process_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Validates and secures LLM output.
        Returns:
        - is_safe: bool
        - decision: "SAFE" | "MASK" | "BLOCK"
        - risk_score: float (0 - 100)
        - risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
        - sanitized_response: str (cleared or masked response)
        - reason: str
        - details: Dict
        """
        # 1. Structural Validation
        val_result = self.validator.validate(raw_response)

        # 2. Sensitive Leakage & PII Scan
        leak_result = self.leakage_detector.scan_response(raw_response)

        # Calculate Combined Response Risk Score
        max_score = max(val_result["validation_score"], leak_result["leakage_score"])

        # Determine Decision
        if leak_result["requires_blocking"] or val_result["action"] == "BLOCK":
            decision = "BLOCK"
            risk_level = "CRITICAL" if max_score >= 90 else "HIGH"
            is_safe = False
            sanitized_response = "[SECURITY ALERT: The generated response was blocked because it contained sensitive system instructions or confidential credentials.]"
            reason = leak_result["reason"] if leak_result["leakage_detected"] else val_result["anomaly"]

        elif leak_result["requires_masking"]:
            decision = "MASK"
            risk_level = "MEDIUM"
            is_safe = True
            sanitized_response = leak_result["masked_text"]
            reason = "Response sanitized: sensitive PII or token data was automatically masked."

        else:
            decision = "SAFE"
            risk_level = "LOW"
            is_safe = True
            sanitized_response = raw_response
            reason = "Response validated and verified safe."

        return {
            "is_safe": is_safe,
            "decision": decision,
            "risk_score": max_score,
            "risk_level": risk_level,
            "sanitized_response": sanitized_response,
            "reason": reason,
            "validation_details": val_result,
            "leakage_details": leak_result
        }
