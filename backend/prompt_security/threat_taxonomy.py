"""
threat_taxonomy.py
Defines threat taxonomy categories, risk levels, and decision constants for the prompt security engine.
"""

from enum import Enum


class ThreatCategory(str, Enum):
    DIRECT_INJECTION = "Direct Prompt Injection"
    JAILBREAK = "Jailbreak Payload"
    PROMPT_LEAKAGE = "Prompt / System Prompt Leakage"
    GOAL_HIJACKING = "Goal Hijacking"
    BENIGN = "Benign"


class BinaryLabel(str, Enum):
    MALICIOUS = "MALICIOUS"
    BENIGN = "BENIGN"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityDecision(str, Enum):
    ALLOW = "ALLOW"
    WARNING = "WARNING"
    BLOCK = "BLOCK"


# Risk Score Thresholds (Configurable)
RISK_THRESHOLDS = {
    "LOW_MAX": 30,
    "MEDIUM_MAX": 60,
    "HIGH_MAX": 80,
    "CRITICAL_MIN": 81
}

# Decision thresholds based on 0-100 score
def map_risk_level(score: float) -> RiskLevel:
    if score <= RISK_THRESHOLDS["LOW_MAX"]:
        return RiskLevel.LOW
    elif score <= RISK_THRESHOLDS["MEDIUM_MAX"]:
        return RiskLevel.MEDIUM
    elif score <= RISK_THRESHOLDS["HIGH_MAX"]:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def map_security_decision(score: float) -> SecurityDecision:
    if score <= RISK_THRESHOLDS["LOW_MAX"]:
        return SecurityDecision.ALLOW
    elif score <= RISK_THRESHOLDS["MEDIUM_MAX"]:
        return SecurityDecision.WARNING
    else:
        return SecurityDecision.BLOCK
