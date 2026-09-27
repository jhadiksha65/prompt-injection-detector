import os
import sys
import time
import argparse
import torch
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizer,
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup
)
from torch.optim import AdamW
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

# Add repo root to path for imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.prompt_security.preprocessing.token_preprocessing import encode_prompt_head_tail, DEFAULT_MAX_LEN

# Configuration Defaults (Phase 2 Generalization Files)
DEFAULT_TRAIN_PATH = "data/final/train_generalization.csv"
DEFAULT_VAL_PATH = "data/final/validation_generalization.csv"
EXP_DIR = "experiments/distilbert"
MODEL_CHECKPOINT = "distilbert-base-uncased"
MAX_LEN = DEFAULT_MAX_LEN  # 256
BATCH_SIZE = 32
DEFAULT_LR = 3e-5
WEIGHT_DECAY = 0.01
EPOCHS = 3
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))

os.makedirs(EXP_DIR, exist_ok=True)


class PromptDataset(Dataset):
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
        
        # Uses shared token-for-token head+tail preservation
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
            
            assert input_ids.shape[-1] <= MAX_LEN, f"Expected input_ids seq_len <= {MAX_LEN}, got {input_ids.shape[-1]}"
            assert attention_mask.shape[-1] <= MAX_LEN, f"Expected attention_mask seq_len <= {MAX_LEN}, got {attention_mask.shape[-1]}"
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=1)[:, 1]
            
            all_probs.extend(probs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
    return np.array(all_probs), np.array(all_labels)


def train_and_evaluate(
    train_path=DEFAULT_TRAIN_PATH,
    val_path=DEFAULT_VAL_PATH,
    lr=DEFAULT_LR,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    output_model_name="distilbert_model_improved.pt",
    output_metadata_name="validation_threshold_metadata.json"
):
    print("=" * 80)
    print("PROMPT INJECTION DETECTOR - DISTILBERT GENERALIZATION TRAINING")
    print("=" * 80)
    print(f"Device:             {DEVICE}")
    print(f"Training Dataset:   {train_path}")
    print(f"Validation Dataset: {val_path}")
    print(f"Base Model:         {MODEL_CHECKPOINT}")
    print(f"Learning Rate:      {lr}")
    print(f"Batch Size:         {batch_size}")
    print(f"Weight Decay:       {WEIGHT_DECAY}")
    print(f"Max Seq Length:     {MAX_LEN} (Head+Tail Preservation)")
    print(f"Max Epochs:         {epochs}")
    print("=" * 80)
    
    # 1. Load data strictly for Training and Validation
    print("\nLoading datasets...")
    X_train, y_train = load_data(train_path)
    X_val, y_val = load_data(val_path)
    
    print(f"Train samples:      {len(X_train)} (Class 0: {(y_train==0).sum()}, Class 1: {(y_train==1).sum()})")
    print(f"Validation samples: {len(X_val)} (Class 0: {(y_val==0).sum()}, Class 1: {(y_val==1).sum()})")
    print("NOTE: Test, Challenge Holdout, and Hard-Negative benchmarks are strictly excluded from training.")
    
    # 2. Tokenizer and DataLoader
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_CHECKPOINT)
    
    train_dataset = PromptDataset(X_train, y_train, tokenizer, MAX_LEN)
    val_dataset = PromptDataset(X_val, y_val, tokenizer, MAX_LEN)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # 3. Model & Optimizer with Weight Decay
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT, num_labels=2)
    model = model.to(DEVICE)
    
    # Group parameters for weight decay (no decay on bias and LayerNorm)
    no_decay = ['bias', 'LayerNorm.weight']
    optimizer_grouped_parameters = [
        {'params': [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)], 'weight_decay': WEIGHT_DECAY},
        {'params': [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
    ]
    optimizer = AdamW(optimizer_grouped_parameters, lr=lr)
    
    total_steps = len(train_loader) * epochs
    warmup_steps = int(total_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)
    
    # 4. Training loop with early stopping / best validation loss checkpoint tracking
    print("\nTraining DistilBERT model with checkpoint tracking on validation loss...")
    best_val_loss = float('inf')
    best_val_f1 = 0.0
    best_model_state = None
    best_epoch = 1
    
    train_start_time = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        total_train_loss = 0
        
        total_batches = len(train_loader)
        for batch_idx, batch in enumerate(train_loader, start=1):
            optimizer.zero_grad()
            
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].to(DEVICE)
            
            # Explicit pre-forward assertion ensuring zero sequences exceed 256
            assert input_ids.shape[-1] <= MAX_LEN, f"Expected input_ids seq_len <= {MAX_LEN}, got {input_ids.shape[-1]}"
            assert attention_mask.shape[-1] <= MAX_LEN, f"Expected attention_mask seq_len <= {MAX_LEN}, got {attention_mask.shape[-1]}"
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            
            total_train_loss += loss.item()
            
            if batch_idx % 25 == 0 or batch_idx == total_batches:
                elapsed = time.time() - train_start_time
                pct = (batch_idx / total_batches) * 100.0
                print(f"[Epoch {epoch}/{epochs}] Batch {batch_idx:3d}/{total_batches:3d} ({pct:5.1f}%) | Batch Loss: {loss.item():.4f} | Running Avg: {total_train_loss/batch_idx:.4f} | Elapsed: {elapsed/60.0:.2f}m", flush=True)
            
        avg_train_loss = total_train_loss / len(train_loader)
        
        # Validation evaluation
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
        
        # Calculate validation F1 at standard 0.50
        val_probs, val_true = get_predictions(model, val_loader)
        val_preds = (val_probs >= 0.50).astype(int)
        val_f1 = f1_score(val_true, val_preds, zero_division=0)
        
        print(f"Epoch {epoch}/{epochs} - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val F1 (0.50): {val_f1:.4f}")
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_val_f1 = val_f1
            best_epoch = epoch
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            
    train_time = time.time() - train_start_time
    print(f"\nTraining completed in {train_time:.2f}s. Best Epoch: {best_epoch} (Val Loss: {best_val_loss:.4f}, Val F1: {best_val_f1:.4f})")
    
    # Restore best checkpoint
    model.load_state_dict({k: v.to(DEVICE) for k, v in best_model_state.items()})
    
    # Save the model checkpoint
    save_path = os.path.join(EXP_DIR, output_model_name)
    torch.save(best_model_state, save_path)
    print(f"Saved best model checkpoint to: {save_path}")
    
    # 5. Predict probabilities strictly on Validation set
    print("\nRunning threshold optimization strictly on Validation Set...")
    y_val_probs, y_val_true = get_predictions(model, val_loader)
    
    # 6. Threshold Selection on Validation Set (Recall >= 0.95 and FPR <= 0.05)
    thresholds = np.linspace(0.0, 1.0, 101)
    valid_thresholds = []
    
    for t in thresholds:
        preds = (y_val_probs >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_val_true, preds).ravel()
        
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        f1 = f1_score(y_val_true, preds, zero_division=0)
        meets_constraints = (recall >= 0.95) and (fpr <= 0.05)
        
        valid_thresholds.append({
            "threshold": round(float(t), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1": round(float(f1), 4),
            "fpr": round(float(fpr), 4),
            "fnr": round(float(fnr), 4),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
            "meets_constraints": meets_constraints
        })
        
    valid_df = pd.DataFrame(valid_thresholds)
    constrained_candidates = valid_df[valid_df["meets_constraints"]]
    
    if not constrained_candidates.empty:
        best_candidate = constrained_candidates.loc[constrained_candidates["f1"].idxmax()]
        chosen_threshold = float(best_candidate["threshold"])
    else:
        best_candidate = valid_df.loc[valid_df["f1"].idxmax()]
        chosen_threshold = float(best_candidate["threshold"])
        
    print(f"Optimal threshold chosen strictly on Validation Set: {chosen_threshold:.2f}")
    print(f"  Validation Performance -> F1: {best_candidate['f1']:.4f} | Recall: {best_candidate['recall']:.4f} | FPR: {best_candidate['fpr']:.4f} | Precision: {best_candidate['precision']:.4f}")
    print(f"  Confusion Matrix: [[TN={int(best_candidate['tn'])}, FP={int(best_candidate['fp'])}], [FN={int(best_candidate['fn'])}, TP={int(best_candidate['tp'])}]]")
    
    # Save threshold metadata next to model checkpoint
    threshold_meta_path = os.path.join(EXP_DIR, output_metadata_name)
    import json
    with open(threshold_meta_path, "w") as f:
        json.dump({
            "chosen_threshold": chosen_threshold,
            "validation_metrics": best_candidate.to_dict(),
            "best_epoch": best_epoch,
            "best_val_loss": best_val_loss,
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
            "max_len": MAX_LEN
        }, f, indent=2)
    print(f"Saved frozen validation threshold metadata to: {threshold_meta_path}")
    
    return {
        "chosen_threshold": chosen_threshold,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "best_candidate": best_candidate.to_dict()
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_path", type=str, default=DEFAULT_TRAIN_PATH)
    parser.add_argument("--val_path", type=str, default=DEFAULT_VAL_PATH)
    parser.add_argument("--lr", type=float, default=DEFAULT_LR)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE)
    parser.add_argument("--output_model", type=str, default="distilbert_model_improved.pt")
    parser.add_argument("--output_metadata", type=str, default="validation_threshold_metadata.json")
    args = parser.parse_args()
    
    train_and_evaluate(
        train_path=args.train_path,
        val_path=args.val_path,
        lr=args.lr,
        epochs=args.epochs,
        batch_size=args.batch_size,
        output_model_name=args.output_model,
        output_metadata_name=args.output_metadata
    )
