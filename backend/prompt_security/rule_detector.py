"""
rule_detector.py
Modular heuristic and regular expression rule-based detector for prompt injection patterns.
Categorizes threat patterns into Direct Injection, Jailbreak, Prompt Leakage, and Goal Hijacking.
"""

import re
from typing import Dict, List, Any
from .threat_taxonomy import ThreatCategory


class RuleBasedDetector:
    """
    Heuristic rule engine that scans prompts for known adversarial injection patterns,
    jailbreak tokens, system prompt leakage queries, and goal hijacking attempts.
    """

    def __init__(self):
        # 1. Direct Prompt Injection Patterns
        self.direct_patterns = [
            (r"\b(ignore|disregard|forget|override|bypass|discard|cancel)\s+(all\s+)?(previous|prior|above|preceding|earlier|past)\s+(instructions?|rules?|directives?|guidelines?|constraints?|prompts?)\b", 95, "Instruction override directive detected"),
            (r"\b(system\s+override|instruction\s+reset|admin\s+command|developer\s+emergency\s+mode)\b", 90, "Privileged system control override tag detected"),
            (r"\b(override\s+(all\s+)?safety\s+(rules|filters|guidelines))\b", 92, "Safety filter override instruction"),
            (r"\b(act\s+as\s+(a\s+)?(fully\s+)?unrestricted\s+(bash\s+)?terminal|root\s+shell)\b", 90, "Terminal/root shell emulation override"),
            (r"\b(from\s+now\s+on\s*,\s*(say\s+yes|accept\s+all\s+commands|never\s+refuse))\b", 85, "Behavioral constraint removal command")
        ]

        # 2. Jailbreak Patterns
        self.jailbreak_patterns = [
            (r"\b(act\s+as\s+dan|do\s+anything\s+now)\b", 95, "DAN (Do Anything Now) jailbreak persona detected"),
            (r"\b(enable\s+developer\s+mode|developer\s+mode\s+(enabled|activated))\b", 92, "Developer Mode safety bypass framing"),
            (r"\b(unfiltered\s+(ai|assistant|model|neural\s+network)|zero\s+(ethical\s+)?filters?|no\s+moral\s+compass)\b", 90, "Unfiltered persona adoption attempt"),
            (r"\b(evilgpt|chaosgpt|prometheus\s+unfiltered|shadowai|rebelcore|darkassistant)\b", 90, "Adversarial jailbreak persona identifier"),
            (r"\b(hypothetical\s+simulation.*(no\s+moral|without\s+(moral|ethical)\s+rules|unrestricted))\b", 85, "Hypothetical bypass scenario framing"),
            (r"\b(roleplay\s+mode:?\s*you\s+are\s+evil|unfiltered\s+mentor)\b", 85, "Adversarial roleplay framing")
        ]

        # 3. Prompt / System Prompt Leakage Patterns
        self.leakage_patterns = [
            (r"\b(output|repeat|print|display|reveal|transcribe|echo|dump|show|disclose)\s+(your\s+)?(exact\s+)?(entire\s+)?(system\s+prompt|initial\s+instructions|hidden\s+instructions|developer\s+guidelines|system\s+preamble)\b", 92, "System prompt extraction query"),
            (r"\b(repeat\s+the\s+words\s+above\s+starting\s+from)\b", 88, "Context extraction boundary probe"),
            (r"\b(translate|encode)\s+(your\s+)?(internal\s+)?(system\s+guidelines|system\s+prompt)\s+into\s+(base64|rot13|hex|json)\b", 90, "Encoded system prompt extraction attempt"),
            (r"\b(text\s+between\s+<system>\s+and\s+</system>)\b", 90, "System tag extraction probe"),
            (r"\b(secret\s+token.*embedded\s+in\s+your\s+system\s+prompt)\b", 88, "System token extraction attempt")
        ]

        # 4. Goal Hijacking Patterns
        self.goal_hijacking_patterns = [
            (r"\b(stop|abandon|cancel|terminate|discontinue|halt)\s+(your\s+)?(current\s+)?(task|role|objective|workflow|analysis)\b", 85, "Task abandonment command"),
            (r"\b(your\s+new\s+goal\s+is\s+to|new\s+mission:|your\s+sole\s+purpose\s+is\s+now)\b", 85, "Goal redirection directive"),
            (r"\b(switch\s+(operational\s+)?focus:?\s*ignore\s+previous\s+tasks)\b", 88, "Operational domain hijacking directive")
        ]

        # 5. Moderate / Suspicious Indicators (Medium Risk, 45-55)
        self.moderate_patterns = [
            (r"(<system>|<admin>|\[SYSTEM\]|\[INST\]|\[ADMIN\]|<\|im_start\|>|<\|im_end\|>)", 55, "System/Instruction markup delimiter in user input"),
            (r"\b(pretend\s+(you\s+are|to\s+be)\s+(an?\s+)?(unrestricted|different|fictional\s+character|ai\s+without\s+rules))\b", 55, "Unconstrained roleplay framing"),
            (r"\b(what\s+are\s+your\s+(hidden\s+)?instructions|tell\s+me\s+your\s+(internal\s+)?system\s+rules|reveal\s+internal\s+policies)\b", 50, "Internal policy inquiry probe"),
            (r"\b(do\s+not\s+mention\s+(that\s+you\s+are\s+an\s+ai|your\s+safety\s+rules)|never\s+admit\s+to\s+being\s+an\s+ai)\b", 50, "Identity suppression constraint"),
            (r"\b(decode\s+(and\s+execute|this\s+base64\s+payload)|run\s+the\s+encoded\s+command)\b", 55, "Encoded payload execution instruction")
        ]

        # 6. Weak / Low Suspicion Indicators (Low-Medium Risk, 25-35)
        self.weak_patterns = [
            (r"(###\s*instruction|---\s*system\s*directive|###\s*new\s*prompt)", 30, "Structural markdown boundary marker"),
            (r"\b(execute\s+silently|respond\s+without\s+any\s+disclaimers|omit\s+all\s+warnings)\b", 35, "Disclaimer omission request")
        ]

        # 7. Hard Negative Context Dampeners (Patterns indicating legitimate analysis)
        self.hard_negative_indicators = [
            r"\b(why\s+(do|is|would)|can\s+you\s+explain\s+why|how\s+do\s+researchers|analyze\s+this\s+example|what\s+is\s+the\s+difference\s+between|for\s+an\s+academic\s+research\s+paper)\b",
            r"\b(in\s+object-oriented\s+programming|method\s+overriding\s+in\s+java|css\s+specificity|kubernetes.*override|interrupt\s+handler|git\s+merge\s+conflict)\b",
            r"\b(instruction\s+manual\s+states|policy\s+document|user\s+manual|recipe|contract\s+clause)\b"
        ]

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyzes a prompt using heuristic rule matching.
        Returns a structured dictionary with rule_triggered, rule_score, attack_type,
        matched_indicators, and explanation.
        """
        if not text or not isinstance(text, str):
            return {
                "rule_triggered": False,
                "rule_score": 0.0,
                "attack_type": ThreatCategory.BENIGN.value,
                "matched_indicators": [],
                "reason": "Empty or invalid prompt text."
            }

        text_lower = text.lower()
        matched_indicators = []
        matched_scores = []
        max_score = 0.0
        detected_category = ThreatCategory.BENIGN.value
        detected_reason = "No heuristic injection patterns triggered."

        # Check Direct Injections
        for pattern, score, reason in self.direct_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                matched_str = matches[0] if isinstance(matches[0], str) else " ".join([m for m in matches[0] if m])
                matched_indicators.append(f"Direct Injection: '{matched_str}'")
                matched_scores.append(score)
                if score > max_score:
                    max_score = score
                    detected_category = ThreatCategory.DIRECT_INJECTION.value
                    detected_reason = reason

        # Check Jailbreaks
        for pattern, score, reason in self.jailbreak_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                matched_str = matches[0] if isinstance(matches[0], str) else " ".join([m for m in matches[0] if m])
                matched_indicators.append(f"Jailbreak: '{matched_str}'")
                matched_scores.append(score)
                if score > max_score:
                    max_score = score
                    detected_category = ThreatCategory.JAILBREAK.value
                    detected_reason = reason

        # Check Leakage
        for pattern, score, reason in self.leakage_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                matched_str = matches[0] if isinstance(matches[0], str) else " ".join([m for m in matches[0] if m])
                matched_indicators.append(f"Prompt Leakage: '{matched_str}'")
                matched_scores.append(score)
                if score > max_score:
                    max_score = score
                    detected_category = ThreatCategory.PROMPT_LEAKAGE.value
                    detected_reason = reason

        # Check Goal Hijacking
        for pattern, score, reason in self.goal_hijacking_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                matched_str = matches[0] if isinstance(matches[0], str) else " ".join([m for m in matches[0] if m])
                matched_indicators.append(f"Goal Hijacking: '{matched_str}'")
                matched_scores.append(score)
                if score > max_score:
                    max_score = score
                    detected_category = ThreatCategory.GOAL_HIJACKING.value
                    detected_reason = reason

        # Check Moderate Suspicious Indicators
        for pattern, score, reason in self.moderate_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                matched_str = matches[0] if isinstance(matches[0], str) else " ".join([m for m in matches[0] if m])
                matched_indicators.append(f"Suspicious Indicator: '{matched_str}'")
                matched_scores.append(score)
                if score > max_score:
                    max_score = score
                    if detected_category == ThreatCategory.BENIGN.value:
                        detected_category = ThreatCategory.DIRECT_INJECTION.value
                        detected_reason = reason

        # Check Weak Indicators
        for pattern, score, reason in self.weak_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                matched_str = matches[0] if isinstance(matches[0], str) else " ".join([m for m in matches[0] if m])
                matched_indicators.append(f"Low-Risk Indicator: '{matched_str}'")
                matched_scores.append(score)
                if score > max_score:
                    max_score = score
                    if detected_category == ThreatCategory.BENIGN.value:
                        detected_category = ThreatCategory.DIRECT_INJECTION.value
                        detected_reason = reason

        # Multi-indicator combination: multiple moderate/weak indicators elevate score
        if len(matched_scores) > 1:
            other_sum = sum(matched_scores) - max_score
            max_score = min(85.0 if max_score < 80 else 100.0, max_score + (0.25 * other_sum))

        # Apply Hard Negative Dampener if metalinguistic context is strong
        if max_score > 0:
            for hn_pattern in self.hard_negative_indicators:
                if re.search(hn_pattern, text_lower):
                    # Reduce rule score for educational/exploratory inquiries
                    max_score = max(0.0, max_score - 75.0)
                    matched_indicators.append("Context: Educational/Analytical phrasing detected (Dampened)")
                    if max_score <= 30:
                        detected_category = ThreatCategory.BENIGN.value
                        detected_reason = "Keywords matched in legitimate analytical/educational context."
                    break

        return {
            "rule_triggered": max_score > 30.0,
            "rule_score": round(float(max_score), 2),
            "attack_type": detected_category,
            "matched_indicators": matched_indicators,
            "reason": detected_reason
        }
