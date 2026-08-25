# Dataset Documentation & Statistical Summary

## 1. Dataset Overview

The dataset contains **2,240 curated prompt samples** designed specifically for training, validating, and benchmarking the prompt injection detection subsystem. The dataset is strictly balanced with a 50/50 class ratio between malicious and benign inputs and includes a dedicated proportion of **hard negatives** to prevent keyword-based false alarms.

- **Total Samples**: 2,240
- **Malicious Samples**: 1,120 (50.0%)
- **Benign Samples**: 1,120 (50.0%)
- **Hard Negative Samples**: 400 (17.86% of total dataset, 35.71% of benign class)

---

## 2. Attack Category Distribution

| Category | Label | Count | Percentage |
| :--- | :--- | :--- | :--- |
| **Benign (Standard + Hard Negatives)** | `BENIGN` | 1,120 | 50.00% |
| **Jailbreak Payload** | `MALICIOUS` | 421 | 18.79% |
| **Prompt / System Prompt Leakage** | `MALICIOUS` | 324 | 14.46% |
| **Direct Prompt Injection** | `MALICIOUS` | 285 | 12.72% |
| **Goal Hijacking** | `MALICIOUS` | 90 | 4.02% |
| **Total** | — | **2,240** | **100.00%** |

---

## 3. Hard Negatives Design

Hard negatives represent benign prompts that intentionally contain trigger phrases (e.g., `ignore previous instructions`, `override default rules`, `system prompt architecture`, `disregard earlier settings`) in non-adversarial contexts:
1. **AI Security Education**: Conceptual questions about how jailbreaks and prompt injection vulnerabilities function.
2. **Programming & Systems**: Technical questions about method overriding, CSS specificity overrides, and interrupt handling.
3. **Document & Instruction Parsing**: Everyday queries referencing instructions in user manuals, recipes, or legal contracts (e.g., *"In the manual, section 2 says to disregard prior calibration..."*).

---

## 4. File Outputs
- `dataset/dataset.json`: Structured array with fields `prompt`, `label`, `attack_type`, `source`.
- `dataset/dataset.csv`: Comma-separated table for tabular analysis.
- `dataset/dataset_stats.json`: Machine-readable summary statistics.
