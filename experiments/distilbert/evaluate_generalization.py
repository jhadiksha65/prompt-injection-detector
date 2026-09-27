"""
evaluate_generalization.py
Completely isolated evaluation suite for trained Prompt Injection models.
Evaluates the frozen model and frozen threshold on:
  1. Test Generalization Benchmark (data/final/test_generalization.csv)
  2. Challenge Holdout Set (data/final/challenge_holdout.csv)
  3. Expanded Hard-Negatives Benchmark (data/final/hard_negatives_expanded.csv)

Strictly read-only evaluation. Does not alter checkpoint, threshold, or dataset files.
"""

import os
import sys
import json
import argparse
import torch
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    precision_recall_curve,
    auc,
    confusion_matrix
)

# Add repo root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.prompt_security.preprocessing.token_preprocessing import encode_prompt_head_tail, DEFAULT_MAX_LEN

EXP_DIR = "experiments/distilbert"
MODEL_CHECKPOINT = "distilbert-base-uncased"
MAX_LEN = DEFAULT_MAX_LEN  # 256
BATCH_SIZE = 32
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))


class EvalPromptDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=MAX_LEN):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = encode_prompt_head_tail(
            text=text,
            tokenizer=self.tokenizer,
            max_len=self.max_len,
            return_tensors="pt"
        )
        
        return {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "label": torch.tensor(label, dtype=torch.long)
        }


def get_predictions(model, dataloader):
    model.eval()
    all_probs = []
    all_labels = []
    
    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].to(DEVICE)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=1)[:, 1]
            
            all_probs.extend(probs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
    return np.array(all_probs), np.array(all_labels)


def evaluate_dataset(y_true, y_probs, threshold, name, df=None):
    preds = (y_probs >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, preds).ravel()
    
    acc = accuracy_score(y_true, preds)
    prec = precision_score(y_true, preds, zero_division=0)
    rec = recall_score(y_true, preds, zero_division=0)
    f1 = f1_score(y_true, preds, zero_division=0)
    roc_auc = roc_auc_score(y_true, y_probs) if len(np.unique(y_true)) > 1 else 1.0
    
    if len(np.unique(y_true)) > 1:
        p_curve, r_curve, _ = precision_recall_curve(y_true, y_probs)
        pr_auc = auc(r_curve, p_curve)
    else:
        pr_auc = 1.0
        
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    print("\n" + "=" * 80)
    print(f"BENCHMARK EVALUATION: {name}")
    print("=" * 80)
    print(f"Total Samples:       {len(y_true)}")
    print(f"Frozen Threshold:    {threshold:.2f}")
    print(f"Accuracy:            {acc:.4f} ({acc*100:.2f}%)")
    print(f"Precision:           {prec:.4f}")
    print(f"Recall:              {rec:.4f}")
    print(f"F1-score:            {f1:.4f}")
    print(f"ROC-AUC:             {roc_auc:.4f}")
    print(f"PR-AUC:              {pr_auc:.4f}")
    print(f"False Positive Rate: {fpr:.4f} (FP={fp}, TN={tn})")
    print(f"False Negative Rate: {fnr:.4f} (FN={fn}, TP={tp})")
    print(f"Confusion Matrix:    [[TN={tn}, FP={fp}], [FN={fn}, TP={tp}]]")
    
    if df is not None and "category" in df.columns:
        df = df.copy()
        df["pred"] = preds
        df["prob"] = y_probs
        print("\n--- Per-Category Performance Breakdown ---")
        for cat, group in df.groupby("category"):
            cat_true = group["label"].values
            cat_preds = group["pred"].values
            cat_acc = accuracy_score(cat_true, cat_preds)
            cat_fp = ((cat_true == 0) & (cat_preds == 1)).sum()
            cat_fn = ((cat_true == 1) & (cat_preds == 0)).sum()
            print(f"  {cat:38s} (N={len(group):4d}): Accuracy = {cat_acc*100:5.1f}% | FP={cat_fp} | FN={cat_fn}")
            
    # Deep dive for Challenge Holdout Set
    if name == "Challenge Holdout Set" and df is not None:
        print("\n" + "-" * 80)
        print("SPECIFIC CHALLENGE SUBSET AUDIT")
        print("-" * 80)
        
        # 1. Tail injections
        tail_df = df[df["category"] == "indirect_carrier_injection"]
        tail_acc = accuracy_score(tail_df["label"], tail_df["pred"])
        tail_fn = (tail_df["pred"] == 0).sum()
        print(f"Tail Injections (N={len(tail_df)}): Accuracy = {tail_acc*100:.2f}% | Caught = {len(tail_df)-tail_fn}/{len(tail_df)} | FN = {tail_fn}")
        
        # 2. Head injections
        head_df = df[df["prompt"].str.contains(r'\[SYSTEM OVERRIDE|\[ROOT COMMAND|\[SECURITY NOTICE|\[ADMIN HOTFIX|\[MAINTENANCE TRIGGER', case=False, na=False)]
        head_acc = accuracy_score(head_df["label"], head_df["pred"])
        head_fn = (head_df["pred"] == 0).sum()
        print(f"Head Injections (N={len(head_df)}): Accuracy = {head_acc*100:.2f}% | Caught = {len(head_df)-head_fn}/{len(head_df)} | FN = {head_fn}")
        
        # 3. Long benign
        long_b_df = df[df["prompt"].str.contains(r'Comprehensive Academic Inquiry', case=False, na=False)]
        long_b_acc = accuracy_score(long_b_df["label"], long_b_df["pred"])
        long_b_fp = (long_b_df["pred"] == 1).sum()
        print(f"Long Benign     (N={len(long_b_df)}): Accuracy = {long_b_acc*100:.2f}% | Allowed = {len(long_b_df)-long_b_fp}/{len(long_b_df)} | FP = {long_b_fp}")
        
        # Detail any false positives
        fps = df[(df["label"] == 0) & (df["pred"] == 1)]
        print(f"\nTotal Challenge False Positives: {len(fps)}")
        for i, (_, r) in enumerate(fps.iterrows(), start=1):
            print(f"  FP {i} [Prob: {r['prob']:.4f}, Cat: {r['category']}]: {r['prompt'][:120]}...")
            
        # Detail any false negatives
        fns = df[(df["label"] == 1) & (df["pred"] == 0)]
        print(f"\nTotal Challenge False Negatives: {len(fns)}")
        for i, (_, r) in enumerate(fns.iterrows(), start=1):
            print(f"  FN {i} [Prob: {r['prob']:.4f}, Cat: {r['category']}]: {r['prompt'][:120]}...")
            
    # Deep dive for Hard Negatives Expanded
    if name == "Expanded Hard-Negatives Benchmark" and df is not None:
        print("\n" + "-" * 80)
        print("SPECIFIC HARD-NEGATIVE / HARD-POSITIVE BREAKDOWN")
        print("-" * 80)
        b_df = df[df["label"] == 0]
        m_df = df[df["label"] == 1]
        
        b_acc = accuracy_score(b_df["label"], b_df["pred"])
        m_acc = accuracy_score(m_df["label"], m_df["pred"])
        
        b_fps = b_df[b_df["pred"] == 1]
        m_fns = m_df[m_df["pred"] == 0]
        
        print(f"Benign Hard Negatives (N={len(b_df)}): Accuracy = {b_acc*100:.2f}% (Correctly Allowed: {len(b_df)-len(b_fps)}, FP: {len(b_fps)})")
        print(f"Malicious Hard Positives (N={len(m_df)}): Accuracy = {m_acc*100:.2f}% (Correctly Blocked: {len(m_df)-len(m_fns)}, FN: {len(m_fns)})")
        
        print(f"\nAll False Positives in Hard-Negatives ({len(b_fps)}):")
        if len(b_fps) == 0:
            print("  None. Clean 0 FP on hard negatives!")
        else:
            for i, (_, r) in enumerate(b_fps.iterrows(), start=1):
                print(f"  FP {i} [Prob: {r['prob']:.4f}, Cat: {r['category']}]: {r['prompt'][:120]}...")
                
        print(f"\nAll False Negatives in Hard-Positives ({len(m_fns)}):")
        if len(m_fns) == 0:
            print("  None. Clean 0 FN on hard positives!")
        else:
            for i, (_, r) in enumerate(m_fns.iterrows(), start=1):
                print(f"  FN {i} [Prob: {r['prob']:.4f}, Cat: {r['category']}]: {r['prompt'][:120]}...")

    return {
        "dataset": name,
        "samples": len(y_true),
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "fpr": fpr,
        "fnr": fnr,
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "tp": int(tp)
    }


def run_evaluation(
    model_path="experiments/distilbert/distilbert_model_improved.pt",
    threshold_meta_path="experiments/distilbert/validation_threshold_metadata.json"
):
    print("=" * 80)
    print("STARTING INDEPENDENT BENCHMARK EVALUATION")
    print("=" * 80)
    
    # 1. Load threshold metadata
    if not os.path.exists(threshold_meta_path):
        print(f"Warning: {threshold_meta_path} not found. Defaulting to threshold 0.33.")
        frozen_threshold = 0.33
    else:
        with open(threshold_meta_path) as f:
            meta = json.load(f)
            frozen_threshold = float(meta["chosen_threshold"])
        print(f"Loaded frozen threshold from validation metadata: {frozen_threshold:.2f}")
        
    # 2. Load model
    print(f"Loading trained model checkpoint from: {model_path} onto {DEVICE}...")
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_CHECKPOINT)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT, num_labels=2)
    state_dict = torch.load(model_path, map_location=DEVICE)
    model.load_state_dict(state_dict)
    model = model.to(DEVICE)
    model.eval()
    
    # 3. Evaluate on the 3 isolated benchmarks
    benchmarks = [
        ("Test Generalization Benchmark", "data/final/test_generalization.csv"),
        ("Challenge Holdout Set", "data/final/challenge_holdout.csv"),
        ("Expanded Hard-Negatives Benchmark", "data/final/hard_negatives_expanded.csv")
    ]
    
    results = {}
    for name, path in benchmarks:
        df = pd.read_csv(path)
        ds = EvalPromptDataset(df["prompt"].values, df["label"].values, tokenizer, MAX_LEN)
        loader = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False)
        probs, true_labels = get_predictions(model, loader)
        res = evaluate_dataset(true_labels, probs, frozen_threshold, name, df)
        results[name] = res
        
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="experiments/distilbert/distilbert_model_improved.pt")
    parser.add_argument("--threshold_meta", type=str, default="experiments/distilbert/validation_threshold_metadata.json")
    args = parser.parse_args()
    
    run_evaluation(args.model_path, args.threshold_meta)
