import os
import time
import torch
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, AutoModelForSequenceClassification
from torch.optim import AdamW
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
EXP_DIR = "experiments/distilbert"
MODEL_CHECKPOINT = "distilbert-base-uncased"
MAX_LEN = 128
BATCH_SIZE = 32
LR = 2e-5
EPOCHS = 3
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))

os.makedirs(EXP_DIR, exist_ok=True)

class PromptDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "label": torch.tensor(label, dtype=torch.long)
        }

def load_data(path):
    df = pd.read_csv(path)
    df["prompt"] = df["prompt"].fillna("").astype(str)
    return df["prompt"].values, df["label"].values

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

def main():
    print("=" * 60)
    print("PROMPT INJECTION DETECTOR - DISTILBERT EXPERIMENT")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    
    # 1. Load data
    print("\nLoading datasets...")
    X_train, y_train = load_data(TRAIN_PATH)
    X_val, y_val = load_data(VAL_PATH)
    X_test, y_test = load_data(TEST_PATH)
    
    print(f"Train samples:      {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Test samples:       {len(X_test)}")
    
    # 2. Tokenizer and DataLoader
    print(f"\nLoading tokenizer: {MODEL_CHECKPOINT}...")
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_CHECKPOINT)
    
    train_dataset = PromptDataset(X_train, y_train, tokenizer, MAX_LEN)
    val_dataset = PromptDataset(X_val, y_val, tokenizer, MAX_LEN)
    test_dataset = PromptDataset(X_test, y_test, tokenizer, MAX_LEN)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    train_eval_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=False)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    # 3. Load Model
    print(f"Loading pretrained model: {MODEL_CHECKPOINT}...")
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT, num_labels=2)
    model = model.to(DEVICE)
    
    optimizer = AdamW(model.parameters(), lr=LR)
    
    # 4. Training loop with early stopping / best validation checkpoint tracking
    print("\nTraining DistilBERT model...")
    best_val_loss = float('inf')
    best_model_state = None
    
    train_start_time = time.time()
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0
        
        for batch in train_loader:
            optimizer.zero_grad()
            
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].to(DEVICE)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_train_loss = total_loss / len(train_loader)
        
        # Validation loss tracking
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(DEVICE)
                attention_mask = batch["attention_mask"].to(DEVICE)
                labels = batch["label"].to(DEVICE)
                
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                val_loss += outputs.loss.item()
                
        avg_val_loss = val_loss / len(val_loader)
        print(f"Epoch {epoch}/{EPOCHS} - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            
    train_time = time.time() - train_start_time
    print(f"DistilBERT training completed in {train_time:.2f} seconds")
    
    # Restore best checkpoint
    model.load_state_dict({k: v.to(DEVICE) for k, v in best_model_state.items()})
    
    # Save the model
    torch.save(best_model_state, f"{EXP_DIR}/distilbert_model.pt")
    
    # 5. Predict probabilities
    print("\nPredicting probabilities for threshold tuning and evaluation...")
    
    start_time = time.time()
    y_train_probs, y_train_true = get_predictions(model, train_eval_loader)
    train_inf_time = time.time() - start_time
    
    start_time = time.time()
    y_val_probs, y_val_true = get_predictions(model, val_loader)
    val_inf_time = time.time() - start_time
    
    start_time = time.time()
    y_test_probs, y_test_true = get_predictions(model, test_loader)
    test_inf_time = time.time() - start_time
    
    # 6. Threshold Selection on Validation Set Only
    print("\nTuning decision threshold on validation set...")
    thresholds = np.linspace(0.0, 1.0, 101)
    valid_thresholds = []
    
    for t in thresholds:
        preds = (y_val_probs >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_val_true, preds).ravel()
        
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        f1 = f1_score(y_val_true, preds, zero_division=0)
        
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
        best_candidate = constrained_candidates.loc[constrained_candidates["f1"].idxmax()]
        chosen_threshold = best_candidate["threshold"]
        print(f"Optimal threshold meeting constraints (Recall >= 95%, FPR <= 5%): {chosen_threshold:.2f}")
    else:
        constraint_failure = True
        best_candidate = valid_df.loc[valid_df["f1"].idxmax()]
        chosen_threshold = best_candidate["threshold"]
        print(f"WARNING: No threshold satisfied both Recall >= 95% and FPR <= 5% simultaneously.")
        print(f"Falling back to threshold with best F1-score: {chosen_threshold:.2f}")
        
    print(f"Validation F1 at chosen threshold: {best_candidate['f1']:.4f}")
    print(f"Validation Recall at chosen threshold: {best_candidate['recall']:.4f}")
    print(f"Validation FPR at chosen threshold: {best_candidate['fpr']:.4f}")
    
    # 7. Evaluation Function
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

    # Evaluate
    evaluate_model(y_train_true, y_train_probs, chosen_threshold, "DistilBERT (Train - Diagnostic)", len(y_train_true), train_inf_time)
    evaluate_model(y_val_true, y_val_probs, chosen_threshold, "DistilBERT (Validation - Tuned)", len(y_val_true), val_inf_time)
    test_metrics = evaluate_model(y_test_true, y_test_probs, chosen_threshold, "DistilBERT (Test - Final Evaluation)", len(y_test_true), test_inf_time)
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY SCREENSHOT CAPTURE READY")
    print("=" * 60)
    print("Model Name:                  DistilBERT")
    print(f"Pretrained Model Name:      {MODEL_CHECKPOINT}")
    print(f"Configuration:              Batch size={BATCH_SIZE}, LR={LR}, Epochs={EPOCHS}, Max Len={MAX_LEN}, threshold={chosen_threshold:.2f}")
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
