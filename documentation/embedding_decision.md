# Embedding Decision & Text Representation Strategy

## 1. Context & Mentor Requirements

When designing text representations for prompt injection detection, two primary approaches were evaluated:
- **Option A**: Trainable Random-Initialized Embedding Layers (trained from scratch on task-specific corpus).
- **Option B**: Pre-trained Word Embeddings (such as GloVe or FastText).
- **Option C**: High-Dimensional Subword & Word N-Gram Statistical Representations (TF-IDF with sub-linear term frequency scaling).

---

## 2. Comparative Analysis

| Feature | Trainable Embeddings (From Scratch) | Pre-trained Embeddings (GloVe) | N-Gram TF-IDF Representation |
| :--- | :--- | :--- | :--- |
| **Out-of-Vocabulary Handling** | Handled via `<UNK>` token; trainable on specific adversarial tokens. | Fixed vocabulary; struggles with modern LLM adversarial jailbreak tokens (e.g. `DAN`, `ChaosGPT`). | Character and subword n-grams capture arbitrary token combinations. |
| **Inference Latency** | $\sim 5\text{ ms} - 15\text{ ms}$ (CPU) | $\sim 10\text{ ms} - 25\text{ ms}$ (CPU) | $<\mathbf{1\text{ ms}}$ (instantaneous matrix dot product). |
| **Interpretability** | Black-box latent weights. | Black-box static vectors. | **High**: Feature weights directly identify high-risk adversarial n-grams. |
| **Deployment Complexity** | Requires neural framework runtime. | Requires loading large embedding tables ($\ge 100\text{ MB}$). | **Compact**: Serialized model is under $1\text{ MB}$. |

---

## 3. Selected Strategy: Hybrid Representation

For our 50% milestone and real-time browser extension middleware:
1. **N-Gram TF-IDF Vectorizer with Sub-linear Term Scaling**:
   - Word n-grams: $(1, 3)$
   - Sub-linear term frequency scaling ($1 + \log(\text{TF})$)
   - Max features: $10,000$
   - Captures contextual n-gram trigger sequences (e.g., `"ignore all previous"`, `"act as dan"`, `"reveal system prompt"`).
2. **Trainable Vocabulary & Tokenizer Pipeline**:
   - Our modular `TextPreprocessor` indexes the vocabulary and constructs discrete sequence arrays for trainable embedding architectures.
3. **Classification Layer**:
   - Calibrated Logistic Regression with L2 regularization and balanced class weights, outputting continuous posterior probability $P(\text{Malicious}) \in [0, 1]$.
