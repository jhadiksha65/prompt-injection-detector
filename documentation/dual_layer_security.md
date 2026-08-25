# Dual-Layer Security Middleware Specification

## 1. Architectural Overview

The framework provides an end-to-end **Dual-Layer Security Middleware** that secures both the ingress (prompt input) and egress (LLM response) channels of LLM applications.

```
                    ┌────────────────────────────────┐
                    │          User Prompt           │
                    └───────────────┬────────────────┘
                                    │
                                    ▼
       =============================================================
                         LAYER 1: PROMPT SECURITY
       =============================================================
       ├── Text Preprocessing & Vocabulary Normalization
       ├── Heuristic Rule Detector (Direct, Jailbreak, Leakage, Goal)
       ├── ML Sequence Classifier (TF-IDF + Calibrated Logistic Reg)
       └── Decision Fusion Engine (0 - 100 Risk Score)
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
             [ALLOW / LOW RISK]             [BLOCK / CRITICAL]
                    │                               │
                    ▼                               ▼
       ┌────────────────────────┐      ┌─────────────────────────┐
       │   Configured LLM API   │      │ ⛔ Terminate Execution  │
       │    (or Mock Engine)    │      │  - Do NOT Call LLM      │
       └────────────┬───────────┘      │  - Log Security Event   │
                    │                  │  - Dispatch Alerts      │
                    ▼                  │  - Lock Vault Resource  │
       ┌────────────────────────┐      └─────────────────────────┘
       │  Generated Raw Output  │
       └────────────┬───────────┘
                    │
                    ▼
       =============================================================
                        LAYER 2: RESPONSE SECURITY
       =============================================================
       ├── Structural & Repetition Anomaly Validation
       ├── System Prompt Leakage & Preamble Extraction Detection
       ├── Secret Key & Credential Disclosure Detection (sk-, ghp_)
       └── Sensitive PII Detection & Automated Masking
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
              [VERIFIED SAFE]              [LEAKAGE / ANOMALY]
                    │                               │
                    ▼                               ▼
       ┌────────────────────────┐      ┌─────────────────────────┐
       │ Return Response to User│      │ Mask / Block Output     │
       │ (with Security Status) │      │ & Log Incident Event    │
       └────────────────────────┘      └─────────────────────────┘
```

---

## 2. Layer 1 — Prompt Security Pipeline
- **Role**: Protects the LLM from executing malicious directives, unauthorized privilege escalation, persona simulations (`DAN`), and prompt leakage probes.
- **Enforcement**: If a prompt is flagged as `BLOCK` or `CRITICAL` ($\ge 81/100$), execution is halted immediately. The LLM is **not called**, saving computational/API cost and preventing unsafe processing.
- **Incident Response**: Triggers automated email/SMS alerts, logs the request to the SQLite database, and locks sensitive session resources requiring re-authentication.

---

## 3. Layer 2 — Response Security Pipeline
- **Role**: Protects the user and enterprise from unintended LLM disclosures, prompt leakage, leaked API keys (`sk-`, `ghp_`, `AIza`), database credentials, private cryptographic keys, and sensitive PII.
- **Enforcement**:
  - **`SAFE`**: Delivered directly to the client.
  - **`MASK`**: Sensitive tokens (PII, partial credentials) are replaced with `[REDACTED_PII]` or `[CONFIDENTIAL_SECRET_MASKED]`.
  - **`BLOCK`**: Responses containing verbatim system instructions or full API keys are intercepted and replaced with a formal security notification.

---

## 4. End-to-End API Integration: `POST /secure-prompt`

### Request Format
```json
{
  "prompt": "Explain photosynthesis in simple terms."
}
```

### Response Format (Safe Flow)
```json
{
  "request_id": "REQ-7F19AB42",
  "llm_called": true,
  "final_decision": "ALLOW",
  "response": "Photosynthesis is the biological process...",
  "layer1": {
    "is_injection": false,
    "classification": "BENIGN",
    "risk_score": 2.6,
    "risk_level": "LOW",
    "attack_type": "Benign",
    "decision": "ALLOW"
  },
  "layer2": {
    "is_safe": true,
    "decision": "SAFE",
    "risk_score": 0.0,
    "risk_level": "LOW"
  },
  "sensitive_resource_locked": false
}
```
