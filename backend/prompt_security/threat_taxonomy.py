"""
threat_taxonomy.py
Defines threat taxonomy categories, risk levels, and decision constants for the prompt security engine.
"""

from enum import Enum


class ThreatCategory(str, Enum):
    # 1. Existing valid training examples / benign prompts
    BENIGN = "Existing valid training examples / benign prompts"
    # 2. Direct Prompt Injection
    DIRECT_INJECTION = "Direct Prompt Injection"
    # 3. Indirect Prompt Injection
    INDIRECT_INJECTION = "Indirect Prompt Injection"
    # 4. Instruction Override
    INSTRUCTION_OVERRIDE = "Instruction Override"
    # 5. Jailbreak
    JAILBREAK = "Jailbreak"
    # 6. Obfuscation / Encoding
    OBFUSCATION_ENCODING = "Obfuscation / Encoding"
    # 7. Embedded / Carrier Injection
    EMBEDDED_CARRIER = "Embedded / Carrier Injection"
    # 8. Data Exfiltration / Sensitive Information Extraction
    DATA_EXFILTRATION = "Data Exfiltration / Sensitive Information Extraction"
    # 9. Safe Security-Related Hard Negatives
    SAFE_HARD_NEGATIVE = "Safe Security-Related Hard Negatives"
    # Fallback when specific category cannot be distinguished
    UNCLASSIFIED = "Unclassified Suspicious Prompt"

    # Backward compatibility aliases
    PROMPT_LEAKAGE = "Data Exfiltration / Sensitive Information Extraction"
    GOAL_HIJACKING = "Instruction Override"


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
