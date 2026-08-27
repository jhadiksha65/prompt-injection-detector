\# Dataset Preparation Report



\## 1. Objective



The dataset is prepared for binary prompt-injection detection:



\- `0` = Benign

\- `1` = Malicious



The dataset supports the project's threat taxonomy and Transformer-based classification model.



\## 2. Data Sources



Three public datasets were used for training:



1\. Kaggle – Prompt Injection \& Benign Prompt Dataset

2\. Neuralchemy – Prompt Injection Dataset

3\. WamboSec – Prompt Injection Dataset



Mirza Akhi's Prompt Injection Detection Dataset is kept completely separate and is reserved for independent final evaluation.



\## 3. Individual Dataset Preparation



Each dataset was standardized into:



\- `prompt`

\- `label`

\- `attack\_type`

\- `source`



Empty prompts were removed and exact duplicate prompts were removed.



\### Kaggle



\- Original: 500

\- After cleaning/deduplication: 498

\- Benign: 249

\- Malicious: 249



\### Neuralchemy



\- Original combined splits: 15,919

\- After cleaning/deduplication: 15,817

\- Benign: 5,953

\- Malicious: 9,864



\### WamboSec



\- Original: 5,766

\- After cleaning/deduplication: 5,766

\- Benign: 2,340

\- Malicious: 3,426



\## 4. Combined Dataset



After combining the three cleaned datasets:



\- Total: 22,046

\- Exact duplicate prompts: 2,847

\- After deduplication: 19,199

\- Malicious: 11,848

\- Benign: 7,351



\## 5. Class Balancing



The final dataset was balanced to prevent class imbalance from biasing the classifier.



Final dataset:



\- Benign: 7,351

\- Malicious: 7,351

\- Total: 14,702



Malicious samples were sampled proportionally by attack type to preserve attack diversity.



\## 6. Final Data Split



The balanced dataset was divided using stratified sampling:



| Split | Samples | Percentage |

|---|---:|---:|

| Training | 10,291 | 70% |

| Validation | 2,205 | 15% |

| Test | 2,206 | 15% |



Stratification preserves the benign/malicious class distribution across all splits.



\## 7. Independent Evaluation



Mirza Akhi's dataset is not included in training, validation, or the internal test split.



It will be used separately to evaluate how well the finalized model generalizes to attack patterns not used during training.



\## 8. Reproducibility



Random seed: `42`



All raw datasets are retained separately from processed datasets.

