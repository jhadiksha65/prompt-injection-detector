\# Evaluation Plan



\## Primary Evaluation Goal



The detector should identify as many malicious prompt injection attempts as possible while minimizing incorrect detection of benign prompts.



\## Evaluation Metrics



\### 1. Recall — Primary Metric



Measures the proportion of actual malicious prompts correctly detected.



A high recall is important because missing a prompt injection attack is a security risk.



\### 2. False Positive Rate — Hard Constraint



Measures the proportion of benign prompts incorrectly classified as malicious.



A low false positive rate is important so that legitimate users are not unnecessarily blocked.



\### 3. Precision



Measures how many prompts classified as malicious are actually malicious.



\### 4. F1-Score



Provides a balance between precision and recall.



\### 5. Inference Latency



Measures the time required to classify a prompt.



Low latency is important because the detector operates before an LLM request is processed.



\## Initial Engineering Targets



| Metric | Target |

|---|---:|

| Recall | ≥ 95% |

| False Positive Rate | ≤ 5% |

| Precision | ≥ 90% |

| F1-Score | ≥ 92% |

| Inference Latency | As low as practical |



These are initial engineering targets and will be validated experimentally after model training.



\## Evaluation Protocol



The dataset will be separated into training, validation, and test sets.



\- Training set: used to train the model

\- Validation set: used for model and threshold selection

\- Test set: used only for final evaluation



The final test set must not be used during training or model selection.



An independent unseen-attack dataset will also be considered for evaluating generalization to attacks not present in the training data.

