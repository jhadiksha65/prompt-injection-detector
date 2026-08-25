# Browser-Based Prompt Injection Detection Framework for Web-Based LLM Applications

**Final Year B.Tech CSE Project — Review Milestone (50% Completion)**

---

## 👥 Project Information
- **Project Title**: Browser-Based Prompt Injection Detection Framework for Web-Based LLM Applications
- **Team Members**:
  - Diksha Jha
  - Nedha Nizamudeen
  - Jesline Pinto
  - Omika Shrestha
- **Guide**: Mrs. Usha Anirudhha Jogalekar
- **Academic Year**: 2025–2026
- **Repository**: [https://github.com/jhadiksha65/prompt-injection-detector](https://github.com/jhadiksha65/prompt-injection-detector)

---

## 🛡️ Project Overview

Large Language Model (LLM) interfaces (such as ChatGPT, Gemini, and Claude) are vulnerable to **Prompt Injection Attacks**, where malicious actors manipulate prompts to bypass safety guardrails, leak confidential system instructions, or hijack operational goals.

This project delivers a **Client-Server Security Middleware** consisting of:
1. **Manifest V3 Browser Extension**: Intercepts user prompt inputs on web-based LLM applications, displays on-page risk alerts, and blocks adversarial submissions before they reach the model.
2. **Central Flask Security API**: Combines **Heuristic Rule-Based Pattern Matching** with **Calibrated Machine Learning Classification** to perform real-time threat detection, risk scoring (0–100), and attack categorization.

---

## 🏗️ Architecture & Dataflow

```
User Input on ChatGPT / LLM
             │
             ▼
[ Browser Extension (content.js) ] ── (Intercepts Submission)
             │
             ▼
[ Background Worker (background.js) ]
             │
             ▼ (HTTP POST /detect)
[ Flask Security API (app.py) ]
             ├── NLP Preprocessing & Normalization
             ├── Heuristic Rule Detector (Direct, Jailbreak, Leakage, Hijacking)
             ├── ML Sequence Classifier (TF-IDF + Calibrated Logistic Regression)
             └── Decision Fusion & Risk Scoring Engine (0-100 Score)
             │
             ▼
Security Decision:
  ├── ALLOW (Risk 0-30)    ──> Prompt forwarded to ChatGPT + Safe Toast
  ├── WARNING (Risk 31-60) ──> Advisory Modal with Confirmation
  └── BLOCK (Risk 61-100)  ──> Submission Blocked + Security Modal
```

---

## 🚀 Quickstart & Setup Guide

### 1. Backend Environment Setup
```powershell
# Navigate to backend directory
cd backend

# Activate existing Python virtual environment
.\venv\Scripts\Activate.ps1

# Ensure dependencies are installed
pip install -r requirements.txt
```

### 2. Start the Security API
```powershell
# From the project root directory
& "backend\venv\Scripts\python.exe" backend\app.py
```
The server will start at: `http://localhost:5000`
- Health check: `http://localhost:5000/health`
- Detection endpoint: `http://localhost:5000/detect`

### 3. Load Browser Extension in Google Chrome / Brave / Edge
1. Open your browser and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right).
3. Click **Load unpacked**.
4. Select the `browser_extension` folder located at `C:\Users\Dell\Desktop\prompt-injection-detector\browser_extension`.
5. The extension icon **Prompt Sentinel 🛡️** will appear in your extension bar.

---

## 🧪 Dataset, Training & Evaluation

The project includes a curated and balanced dataset of **2,240 samples** (50% Malicious / 50% Benign) with 400 **Hard Negatives** (benign prompts analyzing security or containing "instruction" keywords).

### Regenerate Dataset, Splits & Train Model
```powershell
# 1. Generate Dataset
& "backend\venv\Scripts\python.exe" ml\dataset\build_dataset.py

# 2. Perform Stratified Train (70%) / Val (15%) / Test (15%) Split
& "backend\venv\Scripts\python.exe" ml\preprocessing\split.py

# 3. Train Model & Save Artifacts
& "backend\venv\Scripts\python.exe" ml\train.py

# 4. Evaluate on Unseen Test Partition
& "backend\venv\Scripts\python.exe" ml\evaluate.py
```

### Measured Model Performance (Test Set: 334 Samples)
- **Accuracy**: `100.00%`
- **Recall (Malicious Class)**: `100.00%` (Target: $\ge 90\%$)
- **False Positive Rate (FPR)**: `0.00%` (Target: $\le 10\%$)
- **Hard Negatives Accuracy**: `100.00%`
- **Inference Latency**: `0.042 ms` per prompt (Target: $\le 50\text{ ms}$)

---

## 🔬 Automated Test Suite

Run the full automated test suite covering Health Check, Safe Prompts, Direct Injections, Leakage, Jailbreaks, Goal Hijacking, and Hard Negatives:
```powershell
& "backend\venv\Scripts\python.exe" -m unittest testing\test_detection.py
```

---

## 📂 Project Structure

```
prompt-injection-detector/
├── backend/
│   ├── app.py                          # Flask Central Security API (GET /health, POST /detect)
│   ├── requirements.txt                # Python dependencies
│   ├── venv/                           # Python 3.11 Virtual Environment
│   ├── models/                         # Serialized ML model, vectorizer, and vocabulary
│   └── prompt_security/
│       ├── threat_taxonomy.py          # Category, risk level & decision enums
│       ├── rule_detector.py            # Heuristic regex pattern engine
│       ├── ml_detector.py              # ML classifier inference wrapper
│       ├── risk_scoring.py             # Weighted decision fusion & 0-100 scoring
│       └── decision_engine.py          # Unified detection pipeline coordinator
├── browser_extension/
│   ├── manifest.json                   # Chrome Manifest V3 configuration
│   ├── background.js                   # Extension background service worker
│   ├── content.js                      # DOM interception script & warning overlay
│   ├── popup.html                      # Security dashboard popup
│   ├── popup.js                        # Popup interaction & scan logic
│   └── styles.css                      # Cybersecurity theme styling
├── dataset/
│   ├── dataset.json / dataset.csv      # 2,240 balanced samples
│   ├── train.json / val.json / test.json
│   └── dataset_stats.json / split_stats.json
├── ml/
│   ├── dataset/build_dataset.py        # Dataset generation & balancing
│   ├── preprocessing/                  # NLP cleaning, tokenization & splitting
│   ├── train.py                        # Model training & artifact serialization
│   └── evaluate.py                     # Unseen test set evaluation & report generation
├── documentation/                      # Technical reports & taxonomy docs
│   ├── threat_taxonomy.md
│   ├── classification_strategy.md
│   ├── target_metrics.md
│   ├── dataset.md
│   ├── preprocessing.md
│   ├── embedding_decision.md
│   ├── ml_evaluation.md
│   ├── architecture.md
│   └── testing.md
└── testing/
    └── test_detection.py               # Unit & integration test cases
```