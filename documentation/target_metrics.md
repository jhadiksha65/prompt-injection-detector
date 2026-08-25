# Target Metrics & Evaluation Framework

## 1. Objective

Before training and testing the machine learning and hybrid detection components, we define formal target evaluation metrics. In a defensive cybersecurity context, metrics must balance the detection of true adversarial attempts against user workflow disruption (false alarms).

---

## 2. Formal Target Metrics

| Metric | Target Goal | Justification / Operational Importance |
| :--- | :--- | :--- |
| **Recall (Malicious Class)** | $\ge \mathbf{90.0\%}$ | **Primary Security Metric**: High recall ensures that adversarial injections are rarely missed (minimizing False Negatives). |
| **False Positive Rate (FPR)** | $\le \mathbf{10.0\%}$ | **Hard Ceiling**: A low FPR prevents benign user prompts (especially hard negatives like documentation review) from being erroneously blocked. |
| **Precision (Malicious Class)** | $\ge \mathbf{85.0\%}$ | Ensures that flagged prompts have a high likelihood of being genuinely adversarial. |
| **F1-Score (Macro / Malicious)** | $\ge \mathbf{88.0\%}$ | Harmonic mean balancing recall and precision across both classes. |
| **Accuracy (Overall)** | $\ge \mathbf{88.0\%}$ | Overall correctness across stratified test distribution. |
| **Detection Latency (API)** | $\le \mathbf{50\text{ ms}}$ | Ensures real-time performance for browser prompt interception without noticeable UI lag. |

---

## 3. Mathematical Definitions

Let:
- $TP$ = True Positives (Malicious correctly flagged as Malicious)
- $FP$ = False Positives (Benign incorrectly flagged as Malicious)
- $TN$ = True Negatives (Benign correctly identified as Benign)
- $FN$ = False Negatives (Malicious missed and flagged as Benign)

$$\text{Recall} = \frac{TP}{TP + FN}$$

$$\text{Precision} = \frac{TP}{TP + FP}$$

$$\text{False Positive Rate (FPR)} = \frac{FP}{FP + TN}$$

$$\text{F1-Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$

---

## 4. Evaluation Protocol

1. **Stratified Split**: Fixed $70\%$ train, $15\%$ validation, and $15\%$ test split with seed reproducibility.
2. **Hard Negative Stress Test**: Explicit evaluation subset containing benign prompts designed to trigger heuristic keyword false positives.
3. **Hybrid Evaluation**: Separate evaluation of Rule-Only, ML-Only, and Hybrid (Rule + ML) pipelines to quantify the performance gain of multi-layered detection.
4. **Transparent Reporting**: Actual measured metrics will be computed on the unseen test split and recorded in `documentation/ml_evaluation.md` without data fabrication.
