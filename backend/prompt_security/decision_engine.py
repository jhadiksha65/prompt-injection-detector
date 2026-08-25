"""
decision_engine.py
Unified prompt security engine orchestrating Preprocessing, Rule-Based Detection,
ML Classification, and Risk Scoring into a single entry-point.
"""

from typing import Dict, Any, Optional
from .rule_detector import RuleBasedDetector
from .ml_detector import MLPromptDetector
from .risk_scoring import RiskScorer


class PromptSecurityEngine:
    """
    Main engine combining Rule-Based and ML-Based detection layers
    to analyze prompts and output actionable security decisions.
    """

    def __init__(self, models_dir: Optional[str] = None):
        self.rule_detector = RuleBasedDetector()
        self.ml_detector = MLPromptDetector(models_dir=models_dir)
        self.risk_scorer = RiskScorer(rule_weight=0.40, ml_weight=0.60)

    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Executes end-to-end prompt injection analysis pipeline:
        1. Rule-Based Heuristic Scan
        2. ML Model Probability Estimation
        3. Decision Fusion & Risk Scoring
        4. Attack Classification
        """
        # 1. Rule Scan
        rule_result = self.rule_detector.analyze(prompt)

        # 2. ML Probability
        ml_result = self.ml_detector.predict_probability(prompt)

        # 3. Decision Fusion & Scoring
        fused_result = self.risk_scorer.calculate_risk(rule_result, ml_result)

        # 4. Assemble Final Response Schema
        return {
            "prompt_length": len(prompt) if prompt else 0,
            "is_injection": fused_result["is_injection"],
            "classification": fused_result["classification"],
            "risk_score": fused_result["risk_score"],
            "risk_level": fused_result["risk_level"],
            "attack_type": fused_result["attack_type"],
            "decision": fused_result["decision"],
            "reason": fused_result["reason"],
            "rule_result": rule_result,
            "ml_result": ml_result
        }
