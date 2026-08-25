"""
train.py
Trains the Machine Learning prompt injection classifier on the training partition,
evaluates on validation data, and serializes the trained model artifacts.
"""

import json
import os
import sys
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.preprocessing.preprocessing import TextPreprocessor

def load_data(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    texts = [d["prompt"] for d in data]
    labels = [1 if d["label"] == "MALICIOUS" else 0 for d in data]
    return texts, labels, data

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dataset_dir = os.path.join(base_dir, "dataset")
    models_dir = os.path.join(base_dir, "backend", "models")
    os.makedirs(models_dir, exist_ok=True)

    train_path = os.path.join(dataset_dir, "train.json")
    val_path = os.path.join(dataset_dir, "val.json")

    print(f"Loading training data from {train_path}...")
    X_train_raw, y_train, train_data = load_data(train_path)
    X_val_raw, y_val, val_data = load_data(val_path)

    # 1. Fit & Save TextPreprocessor (Vocabulary & Tokenizer)
    print("Fitting NLP TextPreprocessor...")
    preprocessor = TextPreprocessor(max_seq_len=100, min_word_freq=2, max_vocab_size=10000)
    preprocessor.fit_vocabulary(X_train_raw)
    vocab_path = os.path.join(models_dir, "vocabulary.json")
    preprocessor.save_vocabulary(vocab_path)
    print(f"Vocabulary saved to {vocab_path} (Vocab size: {len(preprocessor.word2idx)})")

    # Clean text for vectorizer
    X_train_clean = [TextPreprocessor.clean_text(t) for t in X_train_raw]
    X_val_clean = [TextPreprocessor.clean_text(t) for t in X_val_raw]

    # 2. Train N-Gram TF-IDF Vectorizer
    print("Fitting TF-IDF Vectorizer (ngram_range=(1, 3), max_features=10000)...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=10000,
        sublinear_tf=True,
        min_df=2
    )
    X_train_vec = vectorizer.fit_transform(X_train_clean)
    X_val_vec = vectorizer.transform(X_val_clean)

    # 3. Train Logistic Regression Classifier
    print("Training Calibrated Logistic Regression Classifier...")
    classifier = LogisticRegression(
        C=2.0,
        penalty="l2",
        class_weight="balanced",
        solver="lbfgs",
        max_iter=1000,
        random_state=42
    )
    classifier.fit(X_train_vec, y_train)

    # 4. Validation Performance
    val_preds = classifier.predict(X_val_vec)
    val_probs = classifier.predict_proba(X_val_vec)[:, 1]

    val_acc = accuracy_score(y_val, val_preds)
    val_prec = precision_score(y_val, val_preds)
    val_rec = recall_score(y_val, val_preds)
    val_f1 = f1_score(y_val, val_preds)
    cm = confusion_matrix(y_val, val_preds)
    tn, fp, fn, tp = cm.ravel()
    val_fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    print("\n--- Validation Partition Results ---")
    print(f"Accuracy:  {val_acc * 100:.2f}%")
    print(f"Precision: {val_prec * 100:.2f}%")
    print(f"Recall:    {val_rec * 100:.2f}%")
    print(f"F1-Score:  {val_f1 * 100:.2f}%")
    print(f"FPR:       {val_fpr * 100:.2f}%")
    print(f"Confusion Matrix: [TN={tn}, FP={fp}, FN={fn}, TP={tp}]")

    # 5. Save Artifacts
    vectorizer_path = os.path.join(models_dir, "vectorizer.joblib")
    classifier_path = os.path.join(models_dir, "classifier.joblib")

    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(classifier, classifier_path)

    metadata = {
        "model_type": "TF-IDF (1,3-gram) + Logistic Regression (L2)",
        "train_samples": len(X_train_raw),
        "validation_samples": len(X_val_raw),
        "val_metrics": {
            "accuracy": round(float(val_acc), 4),
            "precision": round(float(val_prec), 4),
            "recall": round(float(val_rec), 4),
            "f1_score": round(float(val_f1), 4),
            "fpr": round(float(val_fpr), 4)
        },
        "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)}
    }
    with open(os.path.join(models_dir, "model_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel artifacts successfully saved to {models_dir}")

if __name__ == "__main__":
    main()
