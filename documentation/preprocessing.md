# Preprocessing Pipeline & Dataset Partitioning

## 1. Overview

The NLP preprocessing pipeline transforms unstructured natural language text into standardized token sequences and numerical feature representations suitable for rule inspection and machine learning inference.

---

## 2. Text Cleaning & Normalization

1. **Lowercasing**: Normalizes casing variations across adversarial triggers (e.g., `IGNORE ALL PREVIOUS INSTRUCTIONS` $\to$ `ignore all previous instructions`).
2. **Whitespace & Control Character Stripping**: Removes non-printable characters, tabs, and newline sequences (`[\r\n\t]+` $\to$ `' '`).
3. **Punctuation Token Isolation**: Separates punctuation symbols (`[^\w\s]`) into discrete tokens to preserve syntactic boundary cues (such as brackets `[DAN]`, delimiters `---`, and colons `:`).

---

## 3. Vocabulary Construction & Sequence Padding

- **Vocabulary Indexing**: Special tokens `<PAD>` (index `0`) and `<UNK>` (index `1`) are reserved. Words occurring with frequency $\ge 2$ are indexed up to a maximum vocabulary size of $10,000$.
- **Sequence Conversion**: Text is mapped into an integer index array.
- **Fixed-Length Padding / Truncation**: Sequences are padded or truncated to a fixed length of $L = 100$ tokens.
- **Serialization**: The vocabulary mapping is stored as `backend/models/vocabulary.json` for deterministic reproducibility during real-time API inference.

---

## 4. Stratified Dataset Partitions

A stratified split was executed with fixed random seed $42$ to prevent data leakage and maintain consistent label and attack-type distributions across all partitions:

| Partition | Proportion | Total Samples | Malicious Samples | Benign Samples |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | 70% | 1,569 | 785 (50.03%) | 784 (49.97%) |
| **Validation** | 15% | 337 | 169 (50.15%) | 168 (49.85%) |
| **Test** | 15% | 334 | 166 (49.70%) | 168 (50.30%) |
| **Total** | **100%** | **2,240** | **1,120 (50.0%)** | **1,120 (50.0%)** |

All partitions are saved under `dataset/train.json`, `dataset/val.json`, and `dataset/test.json`.
