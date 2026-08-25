# Machine Learning Evaluation Report

## 1. Overview & Evaluation Setup
- **Model Architecture**: TF-IDF (1 to 3-gram, Sub-linear Scaling) + Calibrated Logistic Regression (L2)
- **Evaluation Partition**: Unseen Test Partition (`dataset/test.json`)
- **Total Test Samples**: 334 (166 Malicious / 168 Benign)
- **Random Seed**: 42 (Reproducible Stratified Partitioning)

---

## 2. Target vs. Actual Metrics Comparison

| Metric | Pre-Defined Target | Actual Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Recall (Malicious Class)** | $\ge 90.0\%$ | **100.00%** | **TARGET EXCEEDED** |
| **False Positive Rate (FPR)** | $\le 10.0\%$ | **0.00%** | **TARGET EXCEEDED** |
| **Precision** | $\ge 85.0\%$ | **100.00%** | **TARGET EXCEEDED** |
| **F1-Score** | $\ge 88.0\%$ | **100.00%** | **TARGET EXCEEDED** |
| **Overall Accuracy** | $\ge 88.0\%$ | **100.00%** | **TARGET EXCEEDED** |
| **Inference Latency** | $\le 50.0\text{ ms}$ | **0.042 ms** | **REAL-TIME READY** |

---

## 3. Confusion Matrix Breakdown

$$\begin{bmatrix}
\text{True Negative (TN)} = 168 & \text{False Positive (FP)} = 0 \\
\text{False Negative (FN)} = 0 & \text{True Positive (TP)} = 166
\end{bmatrix}$$

- **True Negatives (TN)**: 168 benign prompts correctly allowed.
- **False Positives (FP)**: 0 benign prompts erroneously flagged.
- **False Negatives (FN)**: 0 malicious prompts missed.
- **True Positives (TP)**: 166 malicious prompts correctly detected.

---

## 4. Per-Category Performance Breakdown

| Attack Category | Total Samples | Correct Predictions | Category Accuracy | Flagged Malicious Rate |
| :--- | :--- | :--- | :--- | :--- |
| **Jailbreak Payload** | 63 | 63 | **100.00%** | 100.00% |
| **Benign** | 168 | 168 | **100.00%** | 0.00% |
| **Goal Hijacking** | 13 | 13 | **100.00%** | 100.00% |
| **Prompt / System Prompt Leakage** | 48 | 48 | **100.00%** | 100.00% |
| **Direct Prompt Injection** | 42 | 42 | **100.00%** | 100.00% |

---

## 5. Hard Negatives Resilience
- **Hard Negative Samples in Test Set**: 60
- **Hard Negative Classification Accuracy**: **100.00%**
- **Conclusion**: The model successfully differentiates metalinguistic references to prompt injection (e.g. security research questions) from real active injection payloads.
