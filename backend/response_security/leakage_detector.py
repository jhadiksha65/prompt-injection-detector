"""
leakage_detector.py
Layer 2 Security Module: Detects confidential information leakage, system prompt disclosure,
API keys/tokens, credentials, and sensitive PII in LLM-generated responses.
"""

import re
from typing import Dict, List, Any


class ResponseLeakageDetector:
    """
    Scans LLM-generated responses for confidential system prompt leakage,
    secret credentials, API keys, database connection strings, and sensitive PII.
    """

    def __init__(self):
        # 1. System Prompt & Preamble Disclosure Patterns
        self.system_leakage_patterns = [
            (r"\b(my\s+initial\s+instructions\s+(are|were)|my\s+system\s+prompt\s+is)\b", 90, "System prompt disclosure preamble"),
            (r"\b(you\s+are\s+a\s+helpful\s+assistant\s+created\s+by\s+openai|you\s+are\s+claude\s+created\s+by\s+anthropic)\b", 85, "Standard system prompt verbatim regurgitation"),
            (r"(<system>[\s\S]*?<\/system>|\[SYSTEM_PROMPT\][\s\S]*?\[\/SYSTEM_PROMPT\])", 95, "Enclosed system prompt markup tags leaked"),
            (r"\b(confidential\s+internal\s+instructions|hidden\s+developer\s+guidelines:)\b", 90, "Confidential instruction header leakage")
        ]

        # 2. Secrets, API Keys & Credential Patterns
        self.secret_patterns = [
            (r"\b(sk-[a-zA-Z0-9]{20,48}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z-_]{35})\b", 95, "Live API Key leaked (OpenAI / GitHub / Google)"),
            (r"\b(password\s*=\s*['\"][^\s'\"]{6,}['\"]|db_password\s*[:=]\s*[^\s,;]+)\b", 95, "Database password / credential assignment leaked"),
            (r"\b(postgres|mysql|mongodb(\+srv)?):\/\/[^\s:]+:[^\s@]+@[^\s\/]+", 95, "Database connection URI with credentials leaked"),
            (r"-----BEGIN (RSA|OPENSSH|EC|DSA|PRIVATE) KEY-----", 100, "Private cryptographic key leaked"),
            (r"\b(bearer\s+[a-zA-Z0-9_\-\.]{30,})\b", 90, "Bearer authentication token leaked")
        ]

        # 3. Sensitive PII Patterns (Maskable)
        self.pii_patterns = [
            (r"\b\d{3}-\d{2}-\d{4}\b", 80, "US Social Security Number (SSN) detected"),
            (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b", 85, "Credit Card Number detected"),
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", 40, "Email address detected")
        ]

    def scan_response(self, text: str) -> Dict[str, Any]:
        """
        Scans LLM output text for leakage of system prompts, credentials, and sensitive PII.
        """
        if not text or not isinstance(text, str):
            return {
                "leakage_detected": False,
                "leakage_score": 0.0,
                "findings": [],
                "masked_text": text or "",
                "requires_masking": False,
                "requires_blocking": False,
                "reason": "Empty or invalid response."
            }

        findings = []
        max_score = 0.0
        masked_text = text

        # Check System Prompt Leakage
        for pattern, score, reason in self.system_leakage_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                findings.append({"type": "System Prompt Leakage", "match": m.group(0)[:50], "score": score, "reason": reason})
                if score > max_score:
                    max_score = score

        # Check Secrets & Credentials
        for pattern, score, reason in self.secret_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                findings.append({"type": "Credential Leakage", "match": "[REDACTED_SECRET]", "score": score, "reason": reason})
                # Mask secrets
                masked_text = re.sub(pattern, "[CONFIDENTIAL_SECRET_MASKED]", masked_text, flags=re.IGNORECASE)
                if score > max_score:
                    max_score = score

        # Check PII
        for pattern, score, reason in self.pii_patterns:
            matches = re.finditer(pattern, text)
            for m in matches:
                findings.append({"type": "PII Detected", "match": "[REDACTED_PII]", "score": score, "reason": reason})
                # Mask PII
                masked_text = re.sub(pattern, "[REDACTED_PII]", masked_text)
                if score > max_score:
                    max_score = score

        requires_blocking = max_score >= 85.0
        requires_masking = (max_score >= 40.0 and not requires_blocking)

        return {
            "leakage_detected": max_score >= 40.0,
            "leakage_score": round(float(max_score), 2),
            "findings": findings,
            "masked_text": masked_text,
            "requires_masking": requires_masking,
            "requires_blocking": requires_blocking,
            "reason": findings[0]["reason"] if findings else "No sensitive leakage detected."
        }
