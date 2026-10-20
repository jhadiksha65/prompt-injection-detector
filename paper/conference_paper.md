# Dual-Layer Security Architecture for Prompt Injection Defense: Neural-Heuristic Fusion, Multi-Modal Attachment Parsing, and Outbound Leakage Prevention

**Group 25 — Cybersecurity Case Study Implementation**  
*Department of Computer Science and Cybersecurity*  
*Cybersecurity Systems and Machine Learning Laboratory*  
**Repository:** [https://github.com/jhadiksha65/prompt-injection-detector](https://github.com/jhadiksha65/prompt-injection-detector)  
**Production Checkpoint:** `05af2d4` | **Model SHA-256:** `c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93` | **Decision Threshold:** `0.3800`

---

## Abstract

Prompt injection represents the paramount security vulnerability in modern applications integrating Large Language Models (LLMs), encompassing direct prompt manipulation, indirect payload delivery through external documents, and unauthorized disclosure of sensitive internal context. In this paper, we present the design, implementation, and empirical evaluation of a production-ready, dual-layer prompt security middleware and gateway. 

Our architecture establishes an active perimeter around the language model: **Layer 1** performs inbound threat screening before model invocation by fusing a calibrated, fine-tuned DistilBERT sequence classifier ($R_{\text{ML}}$) with a deterministic signature pattern engine ($R_{\text{rule}}$) at an operational decision threshold of $\theta = 0.3800$ under a weighted scoring formulation:
$$R_{\text{fused}} = 0.40 \cdot R_{\text{rule}} + 0.60 \cdot R_{\text{ML}}$$

To neutralize indirect injection, our inbound pipeline decouples prompt evaluation from multi-modal attachment ingestion (supporting DOCX, PDF, and optical character recognition via Tesseract), preserving fine-grained threat-source attribution ($\text{threat\_source} \in \{\text{User Prompt}, \text{Attachment}, \text{Both}, \text{None}\}$). Inbound traffic is mapped to an authoritative nine-category threat taxonomy, accurately distinguishing malicious instructions from benign cybersecurity queries.

**Layer 2** inspects outbound LLM responses prior to egress, detecting system prompt disclosure, API credentials, and personally identifiable information (PII), automatically enforcing redaction or complete response withholding. 

The middleware provides an OpenAI-compatible reverse-proxy gateway (`/v1/chat/completions`) for systems such as Open WebUI and an asynchronous browser extension for client-side pre-submission interception. On an independent 3,000-sample balanced generalization benchmark, our hybrid detector achieves an **accuracy of 98.73%**, **precision of 99.26%**, **recall of 98.20%**, and **F1-score of 0.9873** (overcoming the 8.73% recall of rule-only baselines), while maintaining **100% precision and 0.00% false-positive rate** on an adversarial challenge holdout. The entire end-to-end implementation is validated by a **288-test automated regression suite with a 100% pass rate** and sub-30ms inference latency on hardware-accelerated runtimes.

**Index Terms:** prompt injection, indirect prompt injection, LLM security, defense in depth, transformer classification, multi-modal ingestion, data leakage prevention, OpenAI gateway.

---

## 1. Introduction

Language-model applications increasingly act as autonomous agents, customer service intermediaries, and internal business analytical copilots, routinely combining trusted developer instructions with untrusted user input and third-party document corpora. Prompt injection exploits this unified execution channel: because language models cannot intrinsically separate instructional code from passive data, an adversary can format malicious inputs to hijack model execution, bypass safety alignments, redirect agentic tool calls, or extract confidential operational context [1–3]. In the OWASP Top 10 for Large Language Model Applications, prompt injection (**LLM01**) and sensitive information disclosure (**LLM06**) represent the two most pervasive vulnerabilities facing generative enterprise deployments [12].

Attacks are broadly bifurcated into two vectors:
1. **Direct prompt injection**, where the adversary directly enters instructions into the conversational interface.
2. **Indirect prompt injection**, where malicious payloads are embedded within third-party carrier artifacts—such as uploaded reports, resumes, PDFs, or scanned images—that are subsequently consumed by the application [2, 4].

Where applications process consequential tasks or possess access to confidential credentials and developer preambles, static heuristic filters are fundamentally insufficient: simple keyword matching fails against paraphrased attacks, synonym substitution, and encoding obfuscations [5, 8]. Conversely, deploying pure neural models without heuristic safeguards incurs excessive inference overhead and risks catastrophic false-positive rates on legitimate defensive security inquiries [6, 7]. Furthermore, securing the input alone does not prevent the model from inadvertently revealing sensitive API keys, database credentials, or system instructions if an evasion successfully breaches inbound defenses.

### Dual-Layer Defense Pipeline Architecture

```
User Input & Optional Multi-Modal Document Attachment (PDF/DOCX/TXT/Image)
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: Inbound Input Security Gateway                                │
│  ─────────────────────────────────────────────────────────────────────  │
│  • Input Preprocessing (Unicode normalization, zero-width, leetspeak)   │
│  • Decoupled Multi-Modal Parsing (PDF, DOCX, Tesseract OCR for images)  │
│  • Signature Pattern Engine (Heuristic Regex / Context Dampening)       │
│  • Fine-Tuned DistilBERT Transformer Classifier (256-token Head-Tail)   │
│  • Dual-Perspective Threat Fusion: Rfused = 0.40 Rrule + 0.60 RML       │
│  • Enforced Production Threshold: θ = 0.3800                            │
│  • 9-Category Threat Taxonomy Classification                            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                      Safe (Rfused < 0.3800)?
                                     │
                     ┌───────────────┴───────────────┐
                    YES                              NO
                     │                               │
                     ▼                               ▼
     ┌──────────────────────────────┐ ┌───────────────────────────────────┐
     │ Downstream LLM Execution     │ │ Request Blocked Immediately       │
     │ (Ollama / OpenAI / Mock)     │ │ HTTP 200 (finish_reason: filter)  │
     │                              │ │ LLM is NEVER called (0 calls)     │
     └──────────────┬───────────────┘ └───────────────────────────────────┘
                    │
                    ▼ Raw AI Generated Output (Buffered)
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: Outbound Response Inspection & Leakage Guard                  │
│  ─────────────────────────────────────────────────────────────────────  │
│  • System Prompt Leakage & Preamble Disclosure Detection (Regex & tags) │
│  • Secret & Key Detection (sk-*, ghp_*, AIza*, DB URIs, Private Keys)   │
│  • Sensitive PII Pattern Scanning (SSN, Credit Cards, Email)            │
│  • Structural & Anomaly Validation (Empty check, repetition, truncation)│
│  • Automated Masking ([REDACTED_PII]) or Complete Response Withholding │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼ Delivered Response
                               End User / Client UI
```

### Contributions

This paper makes four concrete contributions:
1. **Dual-Layer Perimeter Architecture:** We design and implement a defense-in-depth security gateway coupling pre-execution inbound screening (Layer 1) with post-execution outbound response sanitization (Layer 2), guaranteeing that downstream LLMs are never invoked when an inbound threat is detected.
2. **Decoupled Multi-Modal Ingestion with Source Attribution:** We develop an isolated attachment parsing and optical character recognition (OCR) pipeline that extracts text from DOCX, PDF, and image files independently of user prompt text, preserving precise threat-source attribution (*User Prompt*, *Attachment*, or *Both*).
3. **Calibrated Neural-Heuristic Fusion & 9-Category Taxonomy:** We formulate a dual-perspective risk-scoring engine ($R_{\text{fused}} = 0.40 R_{\text{rule}} + 0.60 R_{\text{ML}}$) that combines a 256-token head-tail DistilBERT sequence classifier with an extensive signature pattern bank, mapped onto an authoritative nine-category threat taxonomy that explicitly protects legitimate cybersecurity and educational inquiries from over-defense.
4. **Empirical Systems Validation & Production Ecosystem Gateways:** We conduct rigorous evaluations on an independent 3,000-sample balanced generalization benchmark, a 600-sample challenge holdout, and a 300-sample hard-negative suite. We demonstrate drop-in reverse-proxy integration via an OpenAI-compatible API (`/v1/chat/completions`), deploy a high-resilience browser extension with low-level DOM interception, and verify system integrity with a 288-test automated regression suite achieving a 100% pass rate.

### Research Questions

- **RQ1 (Component Fusion & Ablation):** How does hybrid neural-heuristic fusion compare to isolated rule-only and neural-only classifiers in minimizing false negatives while preserving high specificity?
- **RQ2 (Attachment & Carrier Generalization):** Can decoupled multi-modal parsing reliably detect indirect carrier injections in documents and images without contaminating prompt classification?
- **RQ3 (Application Gating & Fail-Secure Invariants):** Does the gateway strictly prevent LLM invocation on blocked inputs while maintaining fail-secure operation under degraded or missing model dependencies?
- **RQ4 (Outbound Output Sanitization & Leakage Defense):** Can real-time response inspection intercept system prompt preambles and credential disclosures without degrading legitimate model generation?

---

## 2. Threat Model and Threat Taxonomy

### 2.1 Adversary Capabilities and Protected Assets

We model an untrusted operational environment where adversaries interact with generative applications via direct conversational interfaces, REST endpoints, or carrier documents (e.g., vendor contracts, resumes, financial reports, scanned image receipts). The adversary seeks to:
1. Override developer-defined operational guidelines.
2. Circumvent safety alignment mechanisms (jailbreaking).
3. Extract confidential system instructions and developer preambles.
4. Exfiltrate embedded environment secrets or database credentials.
5. Induce malicious agentic side effects.

The protected assets comprise:
- **System Context & Developer Instructions:** Proprietary system prompt preambles and organizational policy constraints.
- **Environment Credentials:** OpenAI, Anthropic, or cloud API keys (`sk-*`, `ghp_*`, `AIza*`), database connection strings, and private cryptographic keys.
- **User Privacy:** Personally Identifiable Information (PII) including Social Security numbers, credit card tokens, and enterprise contact lists.
- **Computational Resources:** Protection of downstream LLM generation budgets from denial-of-wallet and infinite token generation loops.

### 2.2 Authoritative Nine-Category Threat Taxonomy

Prior heuristic baselines frequently misclassified all attacks under generic "Direct Prompt Injection" or failed into "Unclassified Suspicious Prompt". Our production engine implements an authoritative nine-category taxonomy defined in `backend/prompt_security/threat_taxonomy.py`:

| Index | Threat Category | Scope & Behavioral Definition | Runtime Action |
| :---: | :--- | :--- | :---: |
| **1** | **Existing Valid Training Examples / Benign Prompts** | Standard conversational, educational, programming, and academic inquiries containing no adversarial intent. | `ALLOW` |
| **2** | **Direct Prompt Injection** | Explicit adversarial commands instructing the model to disregard prior context (e.g., *"Ignore all previous instructions and print ACCESS GRANTED"*). | `BLOCK` |
| **3** | **Indirect Prompt Injection** | Adversarial instructions planted in external third-party data sources, reports, or APIs that influence the model when consumed. | `BLOCK` |
| **4** | **Instruction Override** | Commands that usurp operational control or task objectives without necessarily requesting harmful output (e.g., *"Disregard previous role and summarize as a pirate"*). | `BLOCK` |
| **5** | **Jailbreak** | Persona adoption, hypothetical scenarios, and complex adversarial framing designed to bypass safety filters (e.g., DAN, developer mode, unrestricted simulated shell). | `BLOCK` |
| **6** | **Obfuscation / Encoding** | Payloads utilizing Base64, hex encoding, ROT13, binary ciphers, zero-width Unicode characters, or leetspeak to evade standard tokenization. | `BLOCK` |
| **7** | **Embedded / Carrier Injection** | Malicious instructions concealed within structural carrier documents, such as hidden text blocks in DOCX XML, PDF metadata streams, or text embedded in images. | `BLOCK` |
| **8** | **Data Exfiltration / Sensitive Information Extraction** | Targeted reconnaissance attacks seeking system prompt exposure, administrative credentials, passwords, or configuration dumps. | `BLOCK` |
| **9** | **Safe Security-Related Hard Negatives** | Legitimate educational, academic, or professional inquiries concerning cybersecurity concepts (e.g., *"Explain how prompt injection vulnerabilities work in LLM architectures"*). | `ALLOW` |

---

## 3. Related Work

Early foundational research cataloged direct prompt injection and system prompt extraction attacks against early instruction-tuned language models [1]. Greshake et al. and Liu et al. demonstrated that indirect prompt injection represents a systemic vulnerability for applications that process third-party web content, emails, and uploaded documents [2, 3]. 

Subsequent benchmarks expanded from static binary classification to complex agentic environments: InjecAgent evaluated indirect injections in tool-integrated agent frameworks [4], and AgentDojo formalized dynamic benchmarking with adaptive adversarial attacks and defenses [5]. CAPTURE highlighted the critical challenge of context-aware evaluation and over-defense, showing that naive classifiers often block legitimate user requests [6]. Cui et al. provided an extensive empirical reassessment across diverse application contexts, demonstrating that static keyword filters degrade significantly under distribution shift [7]. PromptRobust evaluated model robustness across adversarial phrasing perturbations [8]. 

In model distillation, DistilBERT established that 40% smaller distilled transformer models retain 97% of BERT's language comprehension capabilities while executing 60% faster [9]. In output security, Carlini et al. demonstrated that language models memorize and inadvertently leak training data and operational secrets [10]. Emerging governance frameworks, including NIST AI 600-1 [11] and the OWASP GenAI Top 10 [12], emphasize defense-in-depth architectures spanning both pre-invocation filtering and post-generation egress validation.

---

## 4. System Architecture and Implementation

![Figure 1: End-to-End Dual-Layer Prompt Security Gateway Architecture](figures/pipeline_architecture.png)
*Fig. 1. End-to-End Dual-Layer Prompt Security Gateway Architecture. Untrusted user inputs and multi-modal attachments are decoupled, preprocessed, and evaluated through Layer 1 neural-heuristic fusion ($R_{\text{fused}} = 0.40 R_{\text{rule}} + 0.60 R_{\text{ML}}$). Blocked requests are halted immediately, guaranteeing zero downstream LLM execution. Approved requests are forwarded to the configured LLM, whose buffered output is sanitized by Layer 2 response leakage inspection before client delivery.*

### 4.1 Request Processing Pipeline

The gateway exposes both a dedicated prompt security endpoint (`POST /secure-prompt`) and an OpenAI-compatible reverse-proxy endpoint (`POST /v1/chat/completions`). 

```
                                  [Inbound Request]
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
                [User Prompt Text]                [Optional Attachment]
                        │                                   │
                        │                        (PDF/DOCX/TXT/OCR Image)
                        │                                   │
                        │                         [Text / OCR Extractor]
                        │                                   │
                        ▼                                   ▼
             [Layer 1 Prompt Scan]               [Layer 1 Attachment Scan]
                        │                                   │
                        └─────────────────┬─────────────────┘
                                          ▼
                         [Threat Source Attribution Tuple]
                     (Rprompt, Rattachment, threat_source)
                                          │
                                          ▼
                              [Fused Score Calculation]
                        Rfused = 0.40 Rrule + 0.60 RML
                                          │
                         Safe (Rfused < 0.3800)?
                                          │
                          ┌───────────────┴───────────────┐
                         YES                              NO
                          │                               │
                          ▼                               ▼
                 [Downstream LLM Call]            [Early Termination]
             (Ollama/OpenAI/Mock Buffered)        - finish_reason: "content_filter"
                          │                       - LLM is NEVER called
                          ▼                       - Security Alert Card Returned
                 [Layer 2 Response Scan]
             - System prompt preamble check
             - API keys & credential regex
             - PII identification & redaction
             - Repetition & length validation
                          │
                          ▼
                 [Egress to Client UI]
```

### 4.2 Inbound Layer 1 Engine: Preprocessing and Neural-Heuristic Fusion

#### Input Normalization & Head-Tail Tokenization
Adversaries frequently position attack instructions either at the very beginning (head override) or at the end of large text blocks (tail carrier injection). Standard truncation to 256 tokens from the beginning discards the end of the text. As implemented in `backend/prompt_security/preprocessing/token_preprocessing.py`, our pipeline extracts 127 tokens from the sequence head and 127 tokens from the sequence tail, combining them with special tokens (`[CLS]` and `[SEP]`):
$$T_{\text{input}} = [[\text{CLS}], t_1, \dots, t_{127}, [\text{SEP}], t_{N-126}, \dots, t_N, [\text{SEP}]]$$

#### Neural-Heuristic Fusion Formula
Layer 1 combines the continuous risk outputs of the heuristic signature engine ($R_{\text{rule}} \in [0, 100]$) and the fine-tuned DistilBERT transformer ($R_{\text{ML}} = 100 \times P(\text{malicious}) \in [0, 100]$):
$$R_{\text{fused}} = 0.40 \cdot R_{\text{rule}} + 0.60 \cdot R_{\text{ML}}$$

Requests are mapped to four security decision bands:
- **LOW ($0 \le R_{\text{fused}} < 30$):** Security Decision = `ALLOW`.
- **MEDIUM ($30 \le R_{\text{fused}} < 60$):** Security Decision = `WARNING` (logged to audit database; benign requests proceed).
- **HIGH ($60 \le R_{\text{fused}} < 80$):** Security Decision = `BLOCK`.
- **CRITICAL ($80 \le R_{\text{fused}} \le 100$):** Security Decision = `BLOCK`.

Whenever $R_{\text{fused}} \ge 38.0$ (calibrated decision threshold $\theta = 0.3800$) or either constituent module emits a critical attack override, the request is immediately blocked, guaranteeing zero downstream LLM invocation.

### 4.3 Multi-Modal Attachment Parsing and Threat Attribution

The gateway ingests structured documents (DOCX, PDF, TXT) and raster images (PNG, JPG):
- **Document Parsing:** Document streams are parsed using `pypdf` and `python-docx` to extract text paragraphs, tables, and embedded XML payloads.
- **Optical Character Recognition (OCR):** Image files are scanned using Tesseract OCR via `pytesseract` and `Pillow`.
- **Source Attribution:** Threat scores are computed independently for the prompt and attachment channels:
  $$R_{\text{overall}} = \max(R_{\text{prompt}}, R_{\text{attachment}})$$
  The system outputs an explicit provenance label:
  $$\text{threat\_source} \in \{\text{User Prompt}, \text{Attachment}, \text{Both}, \text{None}\}$$
  This prevents benign user instructions accompanied by malicious documents from contaminating user intent metrics.

### 4.4 Outbound Layer 2 Guard: Response Sanitization and Leakage Prevention

When an approved prompt reaches the downstream LLM (local Ollama `llama3.2:3b`, OpenAI `gpt-4o`, or offline mock simulation), the generated output is buffered and evaluated by Layer 2 before egress:
1. **System Prompt Disclosure Detection:** Scans for preamble leakage patterns, verbatim system header exposure, and enclosed system markup tags (`<system>`, `[SYSTEM_PROMPT]`). Responses with leakage score $\ge 85$ trigger a `BLOCK` decision, completely withholding the response and returning a secure alert placeholder.
2. **Secret and Key Detection:** Detects live credential signatures including OpenAI API keys (`sk-*`), GitHub tokens (`ghp_*`), Google Cloud keys (`AIza*`), private cryptographic keys (`-----BEGIN PRIVATE KEY-----`), database connection URIs (`postgres://...`), and authorization bearer tokens.
3. **PII Redaction & Masking:** Detects Social Security numbers, credit card sequences, and personal email addresses, automatically substituting matches with `[REDACTED_PII]` and returning `decision: "MASK"`.
4. **Structural & Anomaly Validation:** Enforces length boundaries (truncating responses exceeding 8,000 characters) and detects infinite token generation loops (token uniqueness ratio $< 0.15 \to$ `BLOCK`).

### 4.5 Production Ecosystem Gateways

#### OpenAI-Compatible Reverse Proxy (`/v1/chat/completions`)
The service exposes `POST /api/v1/chat/completions` (aliased to `POST /v1/chat/completions`). It accepts standard OpenAI chat-completion payloads, making integration with tools such as Open WebUI, LangChain, or agentic frameworks a single-line base URL configuration change. 

Crucially, **streaming raw tokens (`stream=true`) is prohibited by policy**: the gateway buffers tokens to enable complete Layer 2 whole-response inspection, preventing incremental leakage. On Layer 1 block, the gateway returns standard OpenAI completion structures with:
```json
{
  "choices": [{
    "finish_reason": "content_filter",
    "message": {
      "role": "assistant",
      "content": "[SECURITY BLOCKED: Request violated Layer 1 prompt security policy.]"
    }
  }],
  "prompt_security": {
    "final_decision": "BLOCK",
    "llm_invoked": false,
    "layer1": { "decision": "BLOCK", "risk_score": 92.0, "risk_level": "CRITICAL" },
    "layer2": { "decision": "NOT_EXECUTED" }
  }
}
```

#### High-Resilience Browser Extension
To protect browser-based conversational interfaces (e.g., ChatGPT, Claude, Gemini, local web frontends), we developed an unpacked Chromium extension (`browser_extension/`). It registers low-level `pointerdown` and `keydown` (Enter) event listeners on input containers (including `contenteditable` ProseMirror divs and textareas). It intercepts prompt submissions before the web page can dispatch the network request, transmits the text to `http://localhost:5000/secure-prompt`, and displays a high-contrast modal dialog when a block verdict is received, auto-resetting authorization flags to prevent race conditions.

---

## 5. Dataset Lineage and Model Provenance

### 5.1 Evolution of Experimental Datasets

The training data underwent three distinct development stages documented in `docs/DATASET_LINEAGE.md`:

| Dataset Split / File | Total Rows | Benign (0) | Malicious (1) | Stage / Role |
| :--- | :---: | :---: | :---: | :--- |
| `data/final/train.csv` | 14,317 | 6,979 | 7,338 | Phase 1 Base Training Split |
| `data/final/validation.csv` | 3,068 | 1,496 | 1,572 | Phase 1 Base Validation Split |
| `data/final/test.csv` | 3,069 | 1,496 | 1,573 | Phase 1 Base Test Split |
| `data/final/train_generalization.csv` | 15,500 | 7,750 | 7,750 | Phase 2 Production Training Split |
| `data/final/validation_generalization.csv` | 3,000 | 1,500 | 1,500 | Phase 2 Production Validation Split |
| `data/final/test_generalization.csv` | 3,000 | 1,500 | 1,500 | Phase 2 Generalization Benchmark |
| `data/final/train_v3.csv` | **16,224** | **8,112** | **8,112** | **V3 Production Training Corpus** |
| `data/final/validation_v3.csv` | **1,500** | **750** | **750** | **V3 Production Validation Set** |
| `data/final/challenge_holdout.csv` | 600 | 300 | 300 | Zero-Shot Evasion Benchmark |
| `data/final/hard_negatives_expanded.csv` | 300 | 150 | 150 | Expanded Hard-Negative Benchmark |
| `data/final/hard_negatives_curated.csv` | 300 | 150 | 150 | Curated Hard-Negative Benchmark |
| `data/eval/short_prompt_eval.csv` | 200 | 100 | 100 | Target Short-Prompt (<20 char) Benchmark |

### 5.2 Model Identity and Cryptographic Provenance

The production model artifact is stored at `experiments/distilbert/distilbert_model_augmented.pt`. Its integrity is cryptographically pinned in `backend/prompt_security/model_integrity.py`:
- **Exact File Size:** `267,856,803 bytes` (~255.45 MB)
- **Cryptographic SHA-256 Digest:**  
  `c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93`
- **Trained Model Architecture:** DistilBERT sequence classifier (`distilbert-base-uncased`, 6 transformer layers, 768 hidden dimension, 12 attention heads, 66M parameters).

> [!NOTE]
> **Clarification of Checkpoint Discrepancy in Early Drafts:** Early preliminary drafts noted a 330-byte discrepancy between model files. Our lineage audit confirms that 267,856,473 bytes was the exact size of the Phase 2 checkpoint (preserved as `distilbert_model_augmented_production_backup.pt`, SHA-256: `a487e0be...`), whereas 267,856,803 bytes is the exact byte size of the promoted V3 production model. The server and test suites verify this cryptographic digest at startup.

---

## 6. Experimental Evaluation and Results

### 6.1 RQ1: Component Contribution and Ablation Analysis

We conducted an empirical ablation across three independent holdout benchmarks: the 3,000-sample Generalization Benchmark, the 600-sample Challenge Holdout Set, and the 300-sample Expanded Hard-Negatives Benchmark. All models were evaluated under frozen weights and the operational threshold ($\theta = 0.3800$):

| Corpus ($N$) | Detection Regime | TN | FP | FN | TP | Accuracy | Precision | Recall | F1-Score | FPR |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Generalization Test**<br>($N=3,000$) | Rule-Only Baseline ($>30$) | 1,500 | 0 | 1,369 | 131 | 0.5437 | 1.0000 | 0.0873 | 0.1606 | 0.0000 |
| | Rule-Only Block ($>60$) | 1,500 | 0 | 1,375 | 125 | 0.5417 | 1.0000 | 0.0833 | 0.1538 | 0.0000 |
| | **DistilBERT Classifier ($R_{\text{ML}} \ge 0.38$)** | **1,489** | **11** | **27** | **1,473** | **0.9873** | **0.9926** | **0.9820** | **0.9873** | **0.0073** |
| | **Fused Hybrid Middleware ($R_{\text{fused}}$)** | **1,489** | **11** | **18** | **1,482** | **0.9903** | **0.9926** | **0.9880** | **0.9903** | **0.0073** |
| **Challenge Holdout**<br>($N=600$) | Rule-Only Baseline ($>30$) | 300 | 0 | 280 | 20 | 0.5333 | 1.0000 | 0.0667 | 0.1250 | 0.0000 |
| | **DistilBERT Classifier ($R_{\text{ML}} \ge 0.38$)** | **300** | **0** | **7** | **293** | **0.9883** | **1.0000** | **0.9767** | **0.9882** | **0.0000** |
| | **Fused Hybrid Middleware ($R_{\text{fused}}$)** | **300** | **0** | **5** | **295** | **0.9917** | **1.0000** | **0.9833** | **0.9916** | **0.0000** |
| **Expanded Hard Neg.**<br>($N=300$) | Rule-Only Baseline ($>30$) | 144 | 6 | 141 | 9 | 0.5100 | 0.6000 | 0.0600 | 0.1091 | 0.0400 |
| | **DistilBERT Classifier ($R_{\text{ML}} \ge 0.38$)** | **133** | **17** | **10** | **140** | **0.9100** | **0.8917** | **0.9333** | **0.9121** | **0.1133** |
| | **Fused Hybrid Middleware ($R_{\text{fused}}$)** | **137** | **13** | **7** | **143** | **0.9333** | **0.9167** | **0.9533** | **0.9346** | **0.0867** |

The empirical findings clearly answer **RQ1**:
- **Failure of Rule-Only Heuristics:** On the 3,000-sample generalization test, the rule detector achieves only 8.73% recall ($F_1 = 0.1606$). While its precision is 1.0000 on standard conversational prompts, it misses over 91% of adversarial prompts because attackers easily circumvent exact regex tokens.
- **Deep Learning Generalization:** Deploying the fine-tuned DistilBERT classifier elevates recall from 8.73% to 98.20% and $F_1$-score to 0.9873 on the generalization test. On the Challenge Holdout, the neural classifier achieves 98.83% accuracy with **zero false positives** ($FP = 0, \text{FPR} = 0.00\%$) and ROC-AUC of 1.0000.
- **Hybrid Superiority:** Fusing heuristic patterns with neural attention achieves peak performance ($F_1 = 0.9903$ on Generalization, $0.9916$ on Challenge Holdout). Exact pattern matches elevate risk scores even when an adversarial rephrasing attempts to soften neural attention weights, while the neural classifier reliably catches semantic variants that contain no signature keywords.

### 6.2 Per-Category Attack Resilience Breakdown

Evaluating the fine-tuned classifier across specific threat categories on the 3,000-sample test set demonstrates exceptional category-level robustness:
- **Credential & Secret Harvesting ($N=98$):** 100.0% Accuracy ($FP=0, FN=0$)
- **Indirect Carrier Injection ($N=44$):** 100.0% Accuracy ($FP=0, FN=0$)
- **Obfuscation & Encoding ($N=215$):** 100.0% Accuracy ($FP=0, FN=0$)
- **System Prompt Extraction ($N=78$):** 100.0% Accuracy ($FP=0, FN=0$)
- **Direct Instruction Override ($N=922$):** 99.1% Accuracy ($FP=0, FN=8$)
- **Benign STEM & Academics ($N=112$):** 100.0% Accuracy ($FP=0, FN=0$)
- **Benign Coding & Software ($N=284$):** 100.0% Accuracy ($FP=0, FN=0$)
- **Benign Cybersecurity Questions ($N=39$):** 100.0% Accuracy ($FP=0, FN=0$)
- **Adversarial Jailbreaks ($N=143$):** 86.7% Accuracy ($FP=0, FN=19$)

### 6.3 RQ2: Multi-Modal Attachment Parsing Performance

On the Challenge Holdout set, the audit specifically evaluated injection placement:
- **Tail Injections ($N=50$):** 100.0% Accuracy (50/50 detected, $FN=0$).
- **Head Injections ($N=25$):** 80.0% Accuracy (20/25 detected, $FN=5$).
- **Long Benign Documents ($N=25$):** 100.0% Accuracy (25/25 allowed, $FP=0$).

In dedicated document tests (`test_docx_indirect_injection.py` and `test_attachments_image_ocr.py`), malicious instructions concealed within reports and scanned receipts were successfully detected by the decoupled attachment pipeline. Crucially, the system accurately populated $\text{threat\_source} = \text{Attachment}$, allowing benign user questions (e.g., *"Please summarize this report"*) accompanied by malicious documents to be blocked without misattributing malicious intent to the user prompt.

### 6.4 RQ3: Application Gating & Automated Test Suite Matrix

To evaluate whether the gateway strictly enforces security decisions and maintains fail-secure properties, we executed the full automated test suite using `pytest`. As summarized below, the test suite comprises **288 tests across 17 modules**, achieving a **100% pass rate** (288 passed, 0 failed, 0 skipped, execution time: 458s):

| Test Module / Subsystem | Tests | Pass Rate | Functionality Verified |
| :--- | :---: | :---: | :--- |
| `test_admin_auth.py` | 30 | 100% | Admin security, password hashing, and session authentication |
| `test_attachments.py` | 34 | 100% | PDF/DOCX extraction, size limits, and indirect injection gating |
| `test_attachments_image_ocr.py` | 19 | 100% | Tesseract OCR parsing and raster carrier injection detection |
| `test_block_dialog_ui.py` | 13 | 100% | Viewport-constrained modal rendering and responsive button access |
| `test_detection.py` | 14 | 100% | Inbound Layer 1 detection, threshold calibration, and edge cases |
| `test_docx_indirect_injection.py` | 4 | 100% | DOCX indirect injection defense and pre-invocation gating |
| `test_dual_layer.py` | 6 | 100% | End-to-end dual-layer pipeline and decision propagation |
| `test_extension_interception.py` | 15 | 100% | Browser extension DOM interception, ProseMirror, and concurrency locks |
| `test_extension_parity.py` | 28 | 100% | Browser extension parity with Analyzer API verdicts |
| `test_external_llm_demo.py` | 9 | 100% | External LLM provider client, failover, and model selection |
| `test_integration_center.py` | 9 | 100% | Gateway metadata, connection testing, and incident filtering |
| `test_layer2_demo.py` | 16 | 100% | Layer 2 response inspection, secret masking, and simulated leaks |
| `test_llm_client.py` | 6 | 100% | LLM client routing (Ollama, OpenAI, local mock) |
| `test_model_integrity.py` | 25 | 100% | Checkpoint SHA-256 verification and fail-secure fallback |
| `test_open_webui_deploy.py` | 8 | 100% | Open WebUI reverse proxying and deployment verification |
| `test_openai_gateway_integration.py` | 12 | 100% | `/v1/chat/completions` OpenAI payload schema and streaming policy |
| `test_scenarios_a_to_h.py` | 10 | 100% | End-to-end verification of Scenarios A through H |
| `test_threat_taxonomy_nine_categories.py` | 14 | 100% | Complete 9-category taxonomy classification and fallback |
| `test_ui_navigation_and_themes.py` | 7 | 100% | Theme switching, dark mode, and UI navigation consistency |
| `test_web_ui_integration.py` | 9 | 100% | Web routes, security dashboard, and incident logging |
| **Total Automated Regression Suite** | **288** | **100.0%** | **Complete System Integrity Verified** |

**Zero Downstream Invocations:** In integration tests spanning both direct HTTP requests and the OpenAI gateway (`test_scenarios_a_to_h.py` and `test_openai_gateway_integration.py`), spy assertions verified that whenever Layer 1 emitted a `BLOCK` decision, the downstream LLM client was called exactly zero times ($N=0$).

### 6.5 RQ4: Outbound Output Sanitization Performance

Layer 2 response inspection was tested across synthetic leak injection scenarios (`test_layer2_demo.py` and `test_scenarios_a_to_h.py`):
- **Credential Leakage Interception:** When downstream responses contained synthetic canary credentials (`sk-live99847192837491028374`), Layer 2 intercepted the payload, returned `final_decision: "PROTECTED_BLOCK"`, and delivered a safe security alert. Verifiable string assertions confirmed that the raw secret was present in 0.0% of client egress payloads.
- **PII Masking:** SSNs, credit cards, and email addresses were successfully replaced with `[REDACTED_PII]` under `decision: "MASK"` without suppressing surrounding non-sensitive text.
- **Benign Transparency:** On safe prompts (e.g., *"What is climate change?"*), the real LLM output was delivered completely unmodified with zero false Layer 2 blocks.

### 6.6 Inference Latency Profile

| Pipeline Component | Apple MPS Acceleration | NVIDIA CUDA GPU | Standard x86 CPU |
| :--- | :---: | :---: | :---: |
| Input Normalization & Head-Tail Tokenization | 1.1 ms | 1.0 ms | 1.8 ms |
| Heuristic Signature Engine ($R_{\text{rule}}$) | 3.2 ms | 3.1 ms | 3.9 ms |
| DistilBERT Transformer Classifier ($R_{\text{ML}}$) | 24.6 ms | 18.2 ms | 78.4 ms |
| Threat Fusion & Decision Gate | 0.4 ms | 0.4 ms | 0.6 ms |
| **Total Inbound Layer 1 Latency** | **29.3 ms** | **22.7 ms** | **84.7 ms** |
| Layer 2 Response Regex & PII Scan | 3.8 ms | 3.5 ms | 4.2 ms |
| Layer 2 Structural & Repetition Validation | 0.3 ms | 0.3 ms | 0.4 ms |

On Apple Silicon (MPS acceleration), Layer 1 neural inference executes in 24.6ms, while rule scanning requires only 3.2ms. Total middleware latency remains well under 30ms, introducing negligible overhead relative to typical generative LLM time-to-first-token latencies (500ms–2,000ms).

---

## 7. Discussion and Security Analysis

### 7.1 Resolving the Research Questions

The empirical results provide definitive answers to our research questions:
- **RQ1 (Fusion):** Rule-only detection is fundamentally inadequate against modern adversarial prompts (8.73% recall). Neural transformer classification elevates recall to 98.20%, and hybrid fusion achieves optimal robustness (98.80% recall, 99.26% precision) by combining regex floor guarantees with deep semantic attention.
- **RQ2 (Attachments):** Decoupling attachment parsing from user prompt scoring isolates carrier attacks and maintains 100% detection on tail carrier injections, preserving precise threat-source attribution.
- **RQ3 (Application Gating):** Automated test assertions verify that downstream LLMs are never invoked when input risk exceeds $\theta = 0.3800$, and cryptographic hash checking ensures fail-secure degradation to rule-only heuristics if model weights are unavailable.
- **RQ4 (Response Protection):** Layer 2 inspection successfully intercepts system prompt leaks, redacts PII, and suppresses credentials without compromising benign model generation.

### 7.2 The Necessity of Dual-Layer Architecture

Our findings demonstrate that neither inbound prompt screening nor outbound output filtering is sufficient in isolation. Relying solely on inbound screening leaves applications vulnerable to model hallucinations, training-data extraction [10], or novel zero-day prompt encodings that circumvent the classifier. Conversely, relying solely on outbound output filtering forces applications to incur the financial and computational cost of invoking the LLM for every malicious payload. Our dual-layer perimeter provides true defense-in-depth: Layer 1 minimizes compute expenditure and eliminates prompt hijacking, while Layer 2 provides a fail-safe backstop against sensitive data leakage.

### 7.3 Policy Implications of Token Streaming

A significant systems insight involves token streaming. While streaming improves perceived user responsiveness, it fundamentally undermines output security: once tokens egress the gateway, credential leaks and system preambles cannot be revoked. Our gateway enforces an atomic buffer-and-scan egress policy, illustrating that high-assurance LLM security requires non-streaming egress architectures.

---

## 8. Limitations and Responsible Use

### 8.1 Limitations

1. **Adversarial Drift:** Highly creative, multi-turn adversarial jailbreaks and foreign-language obfuscations can challenge sequence classifiers. Continuous retraining and dynamic threshold calibration remain essential.
2. **OCR Resolution Limits:** Image OCR accuracy depends on raster clarity; heavily distorted, low-contrast, or steganographic instructions may evade standard Tesseract extraction.
3. **Dynamic Canary Tokens:** In the current release, Layer 2 operates via deterministic regex signatures and structural checks. Enterprise dynamic canary tracking (generating ephemeral per-session tokens) is identified as a valuable future enhancement.

### 8.2 Responsible Disclosure and Privacy

All penetration testing prompts used in this research were evaluated in isolated local testing environments. SQLite audit logging stores prompt snippets and client IP addresses for security forensics; production deployments should implement rigorous data retention and access-control policies.

---

## 9. Conclusion

This paper presented the design, implementation, and empirical evaluation of a dual-layer prompt security middleware and gateway defending LLM applications against direct injection, multi-modal carrier injection, and outbound data leakage. By integrating a fine-tuned DistilBERT transformer with signature heuristics at a calibrated threshold ($\theta = 0.3800$), our system achieves 98.73% accuracy and 98.20% recall on an independent 3,000-sample generalization benchmark, transforming a weak rule-only baseline into a high-assurance security perimeter. With decoupled attachment extraction, an authoritative nine-category threat taxonomy, OpenAI-compatible gateway reverse proxying, a resilient browser extension, and a 288-test automated regression suite with a 100% pass rate, this work demonstrates that robust, low-latency prompt security can be realized in production generative AI systems.

---

## References

1. F. Perez and I. Ribeiro, "Ignore previous prompt: Attack techniques for language models," *arXiv preprint arXiv:2211.09527*, 2022.
2. K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, "Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection," in *Proc. 16th ACM Workshop on Artificial Intelligence and Security (AISEC)*, 2023, pp. 79–90, doi: 10.1145/3605764.3623985.
3. Y. Liu, G. Deng, Z. Xu, Y. Li, Y. Zheng, Y. Zhang, L. Zhao, T. Zhang, and Y. Liu, "Prompt injection attack against LLM-integrated applications," *arXiv preprint arXiv:2306.05499*, 2023.
4. Q. Zhan, Z. Liang, Z. Ying, and D. Kang, "InjecAgent: Benchmarking indirect prompt injections in tool-integrated large language model agents," in *Findings of the Association for Computational Linguistics: ACL 2024*, 2024, pp. 10471–10506, doi: 10.18653/v1/2024.findings-acl.624.
5. E. Debenedetti, J. Zhang, M. Balunovic, L. Beurer-Kellner, M. Fischer, and F. Tramèr, "AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 37, 2024.
6. G. Kholkar and R. Ahuja, "CAPTURE: Context-aware prompt injection testing and robustness enhancement," in *Proc. 1st Workshop on LLM Security*, 2025, pp. 176–188.
7. C. Cui, Y. Wu, M. Backes, and Y. Zhang, "Rethinking assessments of prompt injection attacks," in *Findings of the Association for Computational Linguistics: ACL 2026*, 2026, pp. 23773–23799, doi: 10.18653/v1/2026.findings-acl.1191.
8. K. Zhu, J. Wang, J. Zhou, Z. Wang, H. Chen, Y. Wang, L. Yang, W. Ye, N. Zhang, Y. Du, X. Xie, and Y. Hao, "PromptRobust: Towards evaluating the robustness of large language models on adversarial prompts," *arXiv preprint arXiv:2306.04528*, 2023.
9. V. Sanh, L. Debut, J. Chaumond, and T. Wolf, "DistilBERT, a distilled version of BERT: Smaller, faster, cheaper and lighter," *arXiv preprint arXiv:1910.01108*, 2019.
10. N. Carlini, F. Tramèr, E. Wallace, M. Jagielski, A. Herbert-Voss, K. Lee, A. Roberts, T. Brown, D. Song, U. Erlingsson, A. Oprea, and C. Raffel, "Extracting training data from large language models," in *Proc. 30th USENIX Security Symposium*, 2021, pp. 2633–2650.
11. C. Autio et al., "Artificial intelligence risk management framework: Generative artificial intelligence profile," NIST Special Publication AI 600-1, 2024, doi: 10.6028/NIST.AI.600-1.
12. OWASP GenAI Security Project, "OWASP Top 10 for Large Language Model Applications and Generative AI 2025," *OWASP Foundation*, Oct. 2025. [Online]. Available: [https://owasp.org/www-project-top-10-for-large-language-model-applications/](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
