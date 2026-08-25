"""
validator.py
Layer 2 Validation Module: Checks response structure, length bounds,
repetition loops, and anomalous token patterns.
"""

from typing import Dict, Any


class ResponseValidator:
    """
    Validates general structural integrity and safety parameters of LLM output.
    """

    def __init__(self, max_length: int = 8000, min_length: int = 1):
        self.max_length = max_length
        self.min_length = min_length

    def validate(self, response_text: str) -> Dict[str, Any]:
        if not response_text or len(response_text.strip()) < self.min_length:
            return {
                "is_valid": False,
                "validation_score": 50.0,
                "anomaly": "Empty or zero-length response received from LLM.",
                "action": "BLOCK"
            }

        if len(response_text) > self.max_length:
            return {
                "is_valid": False,
                "validation_score": 65.0,
                "anomaly": f"Response exceeds maximum length threshold ({len(response_text)} > {self.max_length}).",
                "action": "TRUNCATE"
            }

        # Check for excessive repetition (infinite generation loops)
        words = response_text.split()
        if len(words) > 30:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.15:
                return {
                    "is_valid": False,
                    "validation_score": 75.0,
                    "anomaly": "Excessive token repetition / infinite generation loop detected.",
                    "action": "BLOCK"
                }

        return {
            "is_valid": True,
            "validation_score": 0.0,
            "anomaly": None,
            "action": "ALLOW"
        }
