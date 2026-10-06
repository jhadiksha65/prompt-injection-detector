# Dataset Lineage & Model Provenance

## Executive Summary

The Prompt Security detection system utilizes a fine-tuned DistilBERT classifier operating as Layer 1 in a defense-in-depth architecture. Throughout project development, the datasets evolved across multiple experimental, adversarial, and generalization stages to address specific failure modes (such as false positives on benign security questions and evasions via short prompt injections).

This document details the exact lineage, row counts, label balances, and roles of all CSV files stored in `data/final/`, `data/staging/`, and `data/eval/`.

```
Lineage Progression:
ORIGINAL (Phase 1 Base)
    ↓
AUGMENTED (Adversarial & Hard-Negative Injection)
    ↓
GENERALIZATION (Phase 2 Expanded Multi-Domain Split)
    ↓
V3 (Dual-Reviewer Curated Short & Boundary Prompts)
    ↓
CURRENT PRODUCTION MODEL (distilbert_model_augmented.pt)
```

---

## 1. Dataset Lineage Overview

The datasets evolved through several experimental and validation stages. Later CSVs are not necessarily replacements for every earlier CSV.

Rather than each CSV file representing a disconnected dataset, each file served a distinct purpose in the experimental pipeline:
- **Phase 1 (Base & Augmented)**: Established initial model baselines and incorporated synthetic prompt variations.
- **Phase 2 (Generalization)**: Created a clean, balanced 15,500-sample training corpus across multiple public benchmarks and established a strict 0.38 decision threshold.
- **Phase 3 (V3 Production Candidate)**: Addressed boundary edge cases—specifically short (<20 character) prompt injections and conversational false positives—via rigorous human review, producing the current production model.
- **Evaluation & Benchmark Sets**: Independent holdout sets designed strictly to test edge cases, hard negatives, and out-of-distribution attacks without leaking into training splits.

---

## 2. Original Dataset Stage (Phase 1 Base)

The original dataset stage represented the baseline prompt injection corpus compiled during early project development.

### Verified Files & Counts

| File | Exact Rows | Benign (0) | Malicious (1) | Role |
| :--- | :--- | :--- | :--- | :--- |
| `data/final/train.csv` | **14,317** | 6,979 | 7,338 | Initial Phase 1 training split |
| `data/final/validation.csv` | **3,068** | 1,496 | 1,572 | Initial Phase 1 validation split |
| `data/final/test.csv` | **3,069** | 1,496 | 1,573 | Initial Phase 1 held-out test split |

### Characteristics
- Drawn from aggregated initial sources (including Kaggle, Deepset, and WamboSec corpora).
- Provided the initial baseline evaluation for DistilBERT, DeBERTa, and classical ML benchmarks (Logistic Regression, Random Forest, XGBoost).
- **Production Status**: Superseded by subsequent iterations; **not** used to train the current production model.

---

## 3. Augmented Dataset Stage

The augmented dataset stage introduced targeted adversarial variations and synthetic injections to teach the classifier invariant patterns.

### Verified Files & Counts

| File | Exact Rows | Benign (0) | Malicious (1) | Role |
| :--- | :--- | :--- | :--- | :--- |
| `data/final/train_augmented.csv` | **11,769** | 5,834 | 5,935 | Early augmented experimental training split |

### Characteristics & Context
- In this repository, "augmented" refers to injecting known jailbreak prefixes, persona mutations, system-prompt extraction patterns, and initial hard-negative benign queries into the training distribution.
- Note: Neither `validation_augmented.csv` nor `test_augmented.csv` exist in `data/final/`—evaluation for this phase utilized the standard validation and test holdouts.
- **Production Status**: Early experimental iteration; **not** the current production training dataset.

---

## 4. Generalization Dataset Stage (Phase 2 Production)

The Generalization stage was created to resolve out-of-distribution drop-offs and prevent overfitting to specific phrasing patterns. It incorporated broader datasets (including OpenAssistant, Squad v2, Anthropic HH-RLHF, and JailbreakHub).

### Verified Files & Counts

| File | Exact Rows | Benign (0) | Malicious (1) | Role |
| :--- | :--- | :--- | :--- | :--- |
| `data/final/train_generalization.csv` | **15,500** | 7,750 | 7,750 | Phase 2 production training set |
| `data/final/validation_generalization.csv` | **3,000** | 1,500 | 1,500 | Phase 2 production validation set |
| `data/final/test_generalization.csv` | **3,000** | 1,500 | 1,500 | Phase 2 held-out test benchmark |
| `data/final/train_generalization_patched.csv` | **15,800** | 8,000 | 7,800 | Intermediate patch exploration set |

### Resulting Phase 2 Model Artifact
- **Trained Model**: `experiments/distilbert/distilbert_model_augmented_production_backup.pt`
- **Model Checkpoint Size**: 267,856,473 bytes
- **SHA-256 Digest**: `a487e0be9008f2e55d44b4a025b2449cf77c94f53ed5582b3cebeee206e4a850`
- **Metadata Record**: `experiments/distilbert/validation_threshold_metadata_augmented.json`
  - Training samples: 15,500
  - Validation samples: 3,000
  - Chosen decision threshold: **0.38**
  - Performance: Validation F1: 0.9904, Recall: 0.9947, FPR: 0.0140 (TN=1,479, FP=21, FN=8, TP=1,492)

> [!IMPORTANT]
> While `train_generalization.csv` served as the Phase 2 production training set, it is **NOT** the training dataset for the current production model. When V3 was promoted, this Phase 2 artifact was safely preserved as `distilbert_model_augmented_production_backup.pt`.

---

## 5. V3 Dataset Stage (Current Production Training Corpus)

The V3 dataset stage resolved critical boundary challenges: short prompt injections (<20 characters, e.g., `"reset context"`, `"drop instructions"`) and conversational benign prompts that were triggering false positives.

### Verified Files & Counts

| File | Exact Rows | Benign (0) | Malicious (1) | Role |
| :--- | :--- | :--- | :--- | :--- |
| `data/final/train_v3.csv` | **16,224** | 8,112 | 8,112 | **Current Production Training Set** |
| `data/final/validation_v3.csv` | **1,500** | 750 | 750 | **Current Production Validation Set** |
| `data/final/test_v3.csv` | *Does not exist* | — | — | N/A |

### Construction & Review Process
V3 was constructed using an evidence-based dual-reviewer protocol located in `data/staging/`:
1. **Candidate Pool**: 2,000+ short prompt candidates were generated in `data/staging/candidates_v3.csv`.
2. **Review Guidelines**: Human review was governed by `data/staging/HUMAN_REVIEW_GUIDELINES.md`, enforcing strict inclusion criteria (instruction override, persona manipulation, system extraction) and exclusion criteria (ordinary dialogue, harmless programming commands).
3. **Consensus Voting**: Two independent reviewers graded candidates (`reviewer_1_prompt_injection_review.csv` and `reviewer_2_prompt_injection_review.csv`).
4. **Resolution**: Disagreements were compared (`reviewer_comparison.csv`) and adjudicated under a fail-closed policy (`manual_resolution_11.csv`).
5. **Selection & Assembly**: Unanimously approved short malicious candidates and balanced benign conversational samples were compiled (`proposed_training_manifest.csv`, `benign_selection_manifest.csv`) and merged with the foundation set to produce `train_v3.csv` (16,224 rows) and `validation_v3.csv` (1,500 rows).

---

## 6. Current Production Model Provenance

The current production model deployed in the system is the artifact produced by training on `train_v3.csv`.

### Production Model Identity
- **Location**: `experiments/distilbert/distilbert_model_augmented.pt`
- **File Size**: 267,856,803 bytes
- **SHA-256 Digest**: `c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93`
- **Decision Threshold**: **0.38** (frozen in `backend/prompt_security/model_integrity.py`)

### Training & Validation Parameters
- **Training Corpus**: `data/final/train_v3.csv` (**16,224 samples**)
- **Validation Corpus**: `data/final/validation_v3.csv` (**1,500 samples**)
- **Test Corpus**: No dedicated `test_v3.csv` exists in the repository. The V3 training run has documented training and validation datasets only.
- **Candidate Artifact**: `experiments/distilbert/distilbert_model_v3_candidate.pt`
  - SHA-256: `c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93`
  - Verified **byte-for-byte identical** (`cmp` zero exit code) to `distilbert_model_augmented.pt`.
- **Candidate Training Metadata** (`experiments/distilbert/validation_v3_candidate_metadata.json`):
  - Training samples: 16,224
  - Validation samples: 1,500
  - Max sequence length: 256
  - Best epoch: Epoch 2 (`best_val_loss`: 0.02748)
  - Validation-metadata evaluation threshold: `0.06` (computed strictly during validation grid optimization: Precision: 0.9881, Recall: 0.9973, F1: 0.9927; TN=741, FP=9, FN=2, TP=748)
  - **Production decision threshold**: Remains frozen at **`0.38`** in runtime enforcement (`model_integrity.py`). The metadata threshold of `0.06` is purely an evaluation checkpoint record and is NOT the production operational threshold.

### Promotion Record
- **Promotion Commit**: `5840602338a2e05f199ab30cb8d6f1f80ab6dc54`
- **Date**: Wed Sep 30 00:34:26 2026 +0530
- **Commit Message**: *"Promote V3 model and finalize hard-negative handling"*
- **Actions Taken in Commit**:
  1. Updated `EXPECTED_MODEL_SHA256` in `backend/prompt_security/model_integrity.py` to `c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93`.
  2. Updated Git LFS pointer in `experiments/distilbert/distilbert_model_augmented.pt` to `c15a14ca...`.
  3. Backed up previous Phase 2 weights to `distilbert_model_augmented_production_backup.pt` (`a487e0be...`).
  4. Updated test assertions in `testing/test_model_integrity.py` and `testing/test_detection.py`.

---

## 7. Evaluation & Benchmark Datasets

The repository maintains several specialized datasets that are **not** training datasets. These exist strictly to benchmark specific threat vectors and prevent data leakage:

| File | Exact Rows | Distribution | Purpose |
| :--- | :--- | :--- | :--- |
| `data/final/challenge_holdout.csv` | **600** | 300 Benign / 300 Malicious | Challenging zero-shot and evasion holdout set |
| `data/final/hard_negatives_curated.csv` | **300** | 150 Benign / 150 Malicious | High-difficulty benign questions resembling attack syntax |
| `data/final/hard_negatives_expanded.csv` | **300** | 150 Benign / 150 Malicious | Expanded collection of tricky borderline queries |
| `data/final/hard_negatives.csv` | **41** | 26 Benign / 15 Malicious | Initial seed collection of security-topic benign prompts |
| `data/eval/short_prompt_eval.csv` | **200** | 100 Benign / 100 Malicious | Target evaluation benchmark for short (<20 char) inputs |

> [!CAUTION]
> These files are strictly reserved for testing, adversarial benchmarking, and threshold validation. They must not be conflated with the production training set.

---

## 8. Staging & Review Files (`data/staging/`)

The files located in `data/staging/` are intermediate working artifacts produced during the V3 curation process:
- `candidates_v3.csv`: Raw candidate pool of short prompts mined from public repositories.
- `HUMAN_REVIEW_GUIDELINES.md`: Written criteria for manual annotation.
- `human_review_sheet_short_malicious.csv`: Template spreadsheet provided to human annotators.
- `reviewer_1_prompt_injection_review.csv`: Annotations from Reviewer 1.
- `reviewer_2_prompt_injection_review.csv`: Annotations from Reviewer 2.
- `reviewer_comparison.csv`: Diff identifying annotation discrepancies.
- `manual_resolution_11.csv`: Adjudication log resolving edge cases.
- `benign_selection_manifest.csv`: Curated benign prompts chosen to counterbalance approved attacks.
- `proposed_training_manifest.csv`: Final staging manifest merged into `train_v3.csv`.

These are pipeline audit trails and are **not** independent training datasets.

---

## 9. Reviewer-Friendly Summary: "Why Are There So Many CSV Files?"

When reviewing the project repository, the presence of multiple CSV files reflects standard machine learning engineering hygiene across project phases:

1. **Original (`train.csv`, `val.csv`, `test.csv`)**: Baseline datasets used for initial model selection and prototype benchmarking.
2. **Augmented (`train_augmented.csv`)**: Early iteration testing synthetic injection patterns.
3. **Generalization (`train_generalization.csv`, etc.)**: Balanced multi-domain expansion that produced the Phase 2 production model.
4. **V3 (`train_v3.csv`, `validation_v3.csv`)**: Curated dataset incorporating reviewed short prompt injections, used to train the **current production model**.
5. **Evaluation / Benchmarks (`challenge_holdout.csv`, `hard_negatives_*.csv`, `short_prompt_eval.csv`)**: Held-out benchmark suites to evaluate robustness against evasion without polluting training data.
6. **Staging (`data/staging/*`)**: Audit trails and consensus review sheets documenting dataset construction.

---

## 10. Chronological Provenance Timeline

```
Aug 30, 2026
└── Initial Base Model Training
    └── Artifact: distilbert_model.pt
    └── Data: train.csv, validation.csv

Sep 17–18, 2026 (Commit c30f135)
└── Resplits & Improved Checkpoints
    └── Artifacts: distilbert_5e5_ep2.pt, distilbert_model_improved.pt
    └── Data: train_augmented.csv

Sep 27, 2026 (Commit 5e9eaca)
└── Generalization Phase (Phase 2 Production)
    └── Artifact: distilbert_model_augmented.pt (Original SHA: a487e0be...)
    └── Data: train_generalization.csv (15,500), validation_generalization.csv (3,000)
    └── Metadata: validation_threshold_metadata_augmented.json (Threshold: 0.38)

Sep 29, 2026
└── V3 Staging & Dual-Reviewer Consensus
    └── Artifacts: data/staging/candidates_v3.csv, proposed_training_manifest.csv
    └── Datasets Created: train_v3.csv (16,224), validation_v3.csv (1,500)

Sep 29, 2026 23:52
└── V3 Candidate Training Run
    └── Artifact: distilbert_model_v3_candidate.pt (SHA: c15a14ca...)
    └── Metadata: validation_v3_candidate_metadata.json (16,224 train / 1,500 val)

Sep 30, 2026 00:34 (Commit 5840602)
└── V3 Production Promotion
    └── Action: distilbert_model_v3_candidate.pt promoted to distilbert_model_augmented.pt
    └── Backup: Previous weights saved to distilbert_model_augmented_production_backup.pt
    └── Pinned SHA-256: c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93
    └── Threshold: Frozen at 0.38
```

---

## 11. Production Provenance Clarification

> [!WARNING]
> **Historical Documentation Clarification**:
> Older project documentation or commit notes may reference `train_generalization.csv` (15,500 samples) and `validation_generalization.csv` (3,000 samples) as the production training split.
>
> That documentation describes the **Phase 2 Generalization model** (`distilbert_model_augmented_production_backup.pt`, SHA-256 `a487e0be...`).
>
> In commit `5840602`, the model was formally upgraded to the **V3-trained model** (`distilbert_model_augmented.pt`, SHA-256 `c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93`). The **CURRENT** production model was trained on `train_v3.csv` (**16,224 samples**) and validated on `validation_v3.csv` (**1,500 samples**). Both records are historically accurate for their respective phases of the project lifecycle.
