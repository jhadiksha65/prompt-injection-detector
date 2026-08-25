# System Architecture & Component Interaction

## 1. High-Level Architecture

The Prompt Injection Detection Framework operates as an intelligent client-server security middleware designed to safeguard Web-Based LLM applications (such as ChatGPT, Gemini, and Claude) from adversarial prompt manipulation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLIENT (BROWSER EXTENSION)                         │
│                                                                             │
│   ┌─────────────────────┐   Prompt Capture     ┌────────────────────────┐   │
│   │ ChatGPT / LLM Input │ ───────────────────> │  content.js            │   │
│   │ DOM (Input / Area)  │ <─────────────────── │  (Interception & Modal)│   │
│   └─────────────────────┘    Allow / Block     └───────────┬────────────┘   │
│                                                            │                │
│                                                     Message│Passing         │
│                                                            ▼                │
│   ┌─────────────────────┐   Sync State         ┌────────────────────────┐   │
│   │ popup.html / js     │ <─────────────────── │  background.js         │   │
│   │ (Security Dashboard)│                      │  (API Bridge Worker)   │   │
│   └─────────────────────┘                      └───────────┬────────────┘   │
└────────────────────────────────────────────────────────────┼────────────────┘
                                                             │ POST /detect
                                                             │ JSON Payload
                                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BACKEND (CENTRAL FLASK SECURITY API)                  │
│                                                                             │
│                        ┌───────────────────────────────┐                    │
│                        │       Flask API (app.py)      │                    │
│                        └───────────────┬───────────────┘                    │
│                                        │                                    │
│                        ┌───────────────▼───────────────┐                    │
│                        │ NLP Preprocessing / Normalize │                    │
│                        └───────────────┬───────────────┘                    │
│                                        │                                    │
│                    ┌───────────────────┴───────────────────┐                │
│                    ▼                                       ▼                │
│       ┌────────────────────────┐              ┌────────────────────────┐    │
│       │  Rule-Based Detector   │              │   ML-Based Detector    │    │
│       │  (Regex / Indicators)  │              │ (Calibrated Classifier)│    │
│       └────────────┬───────────┘              └────────────┬───────────┘    │
│                    │                                       │                │
│                    └───────────────────┬───────────────────┘                │
│                                        ▼                                    │
│                        ┌───────────────────────────────┐                    │
│                        │    Decision Fusion Engine     │                    │
│                        │  (Weighted Risk 0-100 Score)  │                    │
│                        └───────────────┬───────────────┘                    │
│                                        │                                    │
│                        ┌───────────────▼───────────────┐                    │
│                        │ Threat Categorizer & Decision │                    │
│                        │    (ALLOW / WARNING / BLOCK)  │                    │
│                        └───────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Workflow

1. **Prompt Interception**:
   - The user inputs text into ChatGPT and triggers submission (by pressing Enter or clicking the Send button).
   - `content.js` intercepts the DOM event in the capture phase, preventing premature dispatch to OpenAI servers.
2. **Asynchronous API Dispatch**:
   - `content.js` passes the prompt text to `background.js`, which sends an HTTP POST request to `http://localhost:5000/detect`.
3. **Hybrid Detection Engine**:
   - **Rule-Based Engine**: Inspects for explicit instruction override keywords, jailbreak signatures, system prompt extraction syntax, and goal hijacking patterns.
   - **ML Classifier**: Evaluates subword and word n-gram features against our calibrated model to produce a posterior probability $P(\text{Malicious})$.
   - **Decision Fusion**: Combines scores into a unified 0–100 risk score and maps it to `ALLOW` ($\le 30$), `WARNING` ($31-60$), or `BLOCK` ($>60$).
4. **Enforcement & User Feedback**:
   - **If Safe (`ALLOW`)**: The prompt is allowed through; a subtle green verification toast appears.
   - **If Threat Detected (`BLOCK` / `WARNING`)**: Submission is halted, and a prominent on-page cybersecurity warning modal displays the threat category, risk score, and explainable reason.
