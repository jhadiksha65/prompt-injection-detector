import os
import time
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

# Configuration
TRAIN_PATH = "data/final/train.csv"
VAL_PATH = "data/final/validation.csv"
TEST_PATH = "data/final/test.csv"
EXP_DIR = "experiments/random_forest"
MODEL_PATH = f"{EXP_DIR}/rf_model.joblib"
VEC_PATH = f"{EXP_DIR}/vectorizers.joblib"

os.makedirs(EXP_DIR, exist_ok=True)

def load_data(path):
    df = pd.read_csv(path)
    df["prompt"] = df["prompt"].fillna("").astype(str)
    return df["prompt"].values, df["label"].values

def main():
    print("=" * 60)
    print("PROMPT INJECTION DETECTOR - RANDOM FOREST EXPERIMENT")
    print("=" * 60)
    
    # 1. Load splits
    print("\nLoading datasets...")
    X_train_raw, y_train = load_data(TRAIN_PATH)
    X_val_raw, y_val = load_data(VAL_PATH)
    X_test_raw, y_test = load_data(TEST_PATH)
    
    print(f"Train samples:      {len(X_train_raw)}")
    print(f"Validation samples: {len(X_val_raw)}")
    print(f"Test samples:       {len(X_test_raw)}")
    
    # 2. Text Feature Representation (Combined Word and Character TF-IDF)
    print("\nFitting vectorizers on training data only...")
    word_vec = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), max_features=5000)
    char_vec = TfidfVectorizer(analyzer='char', ngram_range=(3, 5), max_features=5000)
    
    start_time = time.time()
    word_vec.fit(X_train_raw)
    char_vec.fit(X_train_raw)
    vectorizer_fit_time = time.time() - start_time
    print(f"Vectorizer fit time: {vectorizer_fit_time:.2f} seconds")
    
    # Save vectorizers
    joblib.dump({"word_vec": word_vec, "char_vec": char_vec}, VEC_PATH)
    
    # Transform splits
    print("Transforming text splits...")
    X_train_word = word_vec.transform(X_train_raw)
    X_train_char = char_vec.transform(X_train_raw)
    X_train = hstack([X_train_word, X_train_char])
    
    X_val_word = word_vec.transform(X_val_raw)
    X_val_char = char_vec.transform(X_val_raw)
    X_val = hstack([X_val_word, X_val_char])
    
    X_test_word = word_vec.transform(X_test_raw)
    X_test_char = char_vec.transform(X_test_raw)
    X_test = hstack([X_test_word, X_test_char])
    
    print(f"Combined feature shape: {X_train.shape}")
    
    # 3. Model Training
    print("\nTraining Random Forest model (n_estimators=100, n_jobs=-1)...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    
    start_time = time.time()
    clf.fit(X_train, y_train)
    train_time = time.time() - start_time
    print(f"Random Forest training time: {train_time:.2f} seconds")
    
    # Save model
    joblib.dump(clf, MODEL_PATH)
    
    # 4. Predict probabilities on splits
    print("\nPredicting probabilities for threshold tuning and evaluation...")
    
    start_time = time.time()
    y_train_probs = clf.predict_proba(X_train)[:, 1]
    train_inf_time = time.time() - start_time
    
    start_time = time.time()
    y_val_probs = clf.predict_proba(X_val)[:, 1]
    val_inf_time = time.time() - start_time
    
    start_time = time.time()
    y_test_probs = clf.predict_proba(X_test)[:, 1]
    test_inf_time = time.time() - start_time
    
    # 5. Threshold Selection on Validation Set Only
    print("\nTuning decision threshold on validation set...")
    thresholds = np.linspace(0.0, 1.0, 101)
    valid_thresholds = []
    
    for t in thresholds:
        preds = (y_val_probs >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_val, preds).ravel()
        
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        f1 = f1_score(y_val, preds, zero_division=0)
        
        # Check constraints: Recall >= 95% and FPR <= 5%
        meets_constraints = (recall >= 0.95) and (fpr <= 0.05)
        
        valid_thresholds.append({
            "threshold": t,
            "recall": recall,
            "fpr": fpr,
            "f1": f1,
            "meets_constraints": meets_constraints
        })
        
    valid_df = pd.DataFrame(valid_thresholds)
    constrained_candidates = valid_df[valid_df["meets_constraints"]]
    
    constraint_failure = False
    if not constrained_candidates.empty:
        # Select best F1 among those meeting constraints
        best_candidate = constrained_candidates.loc[constrained_candidates["f1"].idxmax()]
        chosen_threshold = best_candidate["threshold"]
        print(f"Optimal threshold meeting constraints (Recall >= 95%, FPR <= 5%): {chosen_threshold:.2f}")
    else:
        constraint_failure = True
        # Select best F1 overall
        best_candidate = valid_df.loc[valid_df["f1"].idxmax()]
        chosen_threshold = best_candidate["threshold"]
        print(f"WARNING: No threshold satisfied both Recall >= 95% and FPR <= 5% simultaneously.")
        print(f"Falling back to threshold with best F1-score: {chosen_threshold:.2f}")
        
    print(f"Validation F1 at chosen threshold: {best_candidate['f1']:.4f}")
    print(f"Validation Recall at chosen threshold: {best_candidate['recall']:.4f}")
    print(f"Validation FPR at chosen threshold: {best_candidate['fpr']:.4f}")
    
    # 6. Evaluation Function
    def evaluate_model(y_true, y_probs, threshold, name, samples_count, inference_time):
        preds = (y_probs >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, preds).ravel()
        
        acc = accuracy_score(y_true, preds)
        prec = precision_score(y_true, preds, zero_division=0)
        rec = recall_score(y_true, preds, zero_division=0)
        f1 = f1_score(y_true, preds, zero_division=0)
        roc_auc = roc_auc_score(y_true, y_probs)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        print("\n" + "=" * 40)
        print(f"RESULTS FOR: {name}")
        print("=" * 40)
        print(f"Number of samples:   {samples_count}")
        print(f"Decision Threshold:  {threshold:.2f}")
        print(f"Accuracy:            {acc:.4f}")
        print(f"Precision:           {prec:.4f}")
        print(f"Recall:              {rec:.4f}")
        print(f"F1-score:            {f1:.4f}")
        print(f"ROC-AUC:             {roc_auc:.4f}")
        print(f"False Positive Rate: {fpr:.4f}")
        print(f"False Negative Rate: {fnr:.4f}")
        print("\nConfusion Matrix:")
        print(f"  [[TN={tn}, FP={fp}],")
        print(f"   [FN={fn}, TP={tp}]]")
        print(f"Inference Time:      {inference_time:.4f} seconds")
        
        return {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": roc_auc,
            "fpr": fpr,
            "fnr": fnr
        }

    # Evaluate all splits
    train_metrics = evaluate_model(y_train, y_train_probs, chosen_threshold, "Random Forest (Train - Diagnostic)", len(y_train), train_inf_time)
    val_metrics = evaluate_model(y_val, y_val_probs, chosen_threshold, "Random Forest (Validation - Tuned)", len(y_val), val_inf_time)
    test_metrics = evaluate_model(y_test, y_test_probs, chosen_threshold, "Random Forest (Test - Final Evaluation)", len(y_test), test_inf_time)
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY SCREENSHOT CAPTURE READY")
    print("=" * 60)
    print("Model Name:                  Random Forest")
    print(f"Configuration:              RandomForestClassifier(n_estimators=100, random_state=42), threshold={chosen_threshold:.2f}")
    print(f"Constraint Failure:         {constraint_failure}")
    print(f"Test Accuracy:              {test_metrics['accuracy']:.4f}")
    print(f"Test Precision:             {test_metrics['precision']:.4f}")
    print(f"Test Recall:                {test_metrics['recall']:.4f}")
    print(f"Test F1-score:              {test_metrics['f1']:.4f}")
    print(f"Test ROC-AUC:               {test_metrics['roc_auc']:.4f}")
    print(f"Test False Positive Rate:   {test_metrics['fpr']:.4f}")
    print(f"Test False Negative Rate:   {test_metrics['fnr']:.4f}")
    print(f"Training Time:              {train_time:.2f} seconds")
    print("=" * 60)

if __name__ == "__main__":
    main()
