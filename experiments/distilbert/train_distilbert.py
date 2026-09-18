import os
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

# Configuration Defaults
DEFAULT_TRAIN_PATH = "data/final/train_augmented.csv"
VAL_PATH = "data/final/validation.csv"
TEST_PATH = "data/final/test.csv"
HARD_NEG_PATH = "data/final/hard_negatives.csv"
EXP_DIR = "experiments/distilbert"
MODEL_CHECKPOINT = "distilbert-base-uncased"
MAX_LEN = 128
BATCH_SIZE = 32
DEFAULT_LR = 3e-5
WEIGHT_DECAY = 0.01
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


def train_and_evaluate(train_path=DEFAULT_TRAIN_PATH, lr=DEFAULT_LR, epochs=EPOCHS, batch_size=BATCH_SIZE, output_model_name="distilbert_model_improved.pt"):
    print("=" * 70)
    print("PROMPT INJECTION DETECTOR - DISTILBERT SPECIALIZATION TRAINING")
    print("=" * 70)
    print(f"Device:            {DEVICE}")
    print(f"Training Dataset:  {train_path}")
    print(f"Base Model:        {MODEL_CHECKPOINT}")
    print(f"Learning Rate:     {lr}")
    print(f"Batch Size:        {batch_size}")
    print(f"Weight Decay:      {WEIGHT_DECAY}")
    print(f"Max Seq Length:    {MAX_LEN}")
    print(f"Max Epochs:        {epochs}")
    print("=" * 70)
    
    # 1. Load data
    print("\nLoading datasets...")
    X_train, y_train = load_data(train_path)
    X_val, y_val = load_data(VAL_PATH)
    X_test, y_test = load_data(TEST_PATH)
    X_hn, y_hn = load_data(HARD_NEG_PATH)
    
    print(f"Train samples:          {len(X_train)}")
    print(f"Validation samples:     {len(X_val)}")
    print(f"Test samples:           {len(X_test)}")
    print(f"Hard-Negative samples:  {len(X_hn)}")
    
    # 2. Tokenizer and DataLoader
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_CHECKPOINT)
    
    train_dataset = PromptDataset(X_train, y_train, tokenizer, MAX_LEN)
    val_dataset = PromptDataset(X_val, y_val, tokenizer, MAX_LEN)
    test_dataset = PromptDataset(X_test, y_test, tokenizer, MAX_LEN)
    hn_dataset = PromptDataset(X_hn, y_hn, tokenizer, MAX_LEN)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    train_eval_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    hn_loader = DataLoader(hn_dataset, batch_size=batch_size, shuffle=False)
    
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
    
    # 4. Training loop with early stopping / best validation checkpoint tracking
    print("\nTraining DistilBERT model with early stopping on validation loss...")
    best_val_loss = float('inf')
    best_val_f1 = 0.0
    best_model_state = None
    best_epoch = 1
    
    train_start_time = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        total_train_loss = 0
        
        for batch in train_loader:
            optimizer.zero_grad()
            
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].to(DEVICE)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            
            total_train_loss += loss.item()
            
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
        
        # Calculate validation F1
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
    
    # Save the model
    save_path = os.path.join(EXP_DIR, output_model_name)
    torch.save(best_model_state, save_path)
    print(f"Saved best model checkpoint to: {save_path}")
    
    # 5. Predict probabilities
    print("\nEvaluating model on validation, test, and hard-negative benchmarks...")
    y_val_probs, y_val_true = get_predictions(model, val_loader)
    y_test_probs, y_test_true = get_predictions(model, test_loader)
    y_hn_probs, y_hn_true = get_predictions(model, hn_loader)
    
    # 6. Threshold Selection on Validation Set
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
    
    if not constrained_candidates.empty:
        best_candidate = constrained_candidates.loc[constrained_candidates["f1"].idxmax()]
        chosen_threshold = float(best_candidate["threshold"])
    else:
        best_candidate = valid_df.loc[valid_df["f1"].idxmax()]
        chosen_threshold = float(best_candidate["threshold"])
        
    print(f"Optimal threshold chosen on Validation Set: {chosen_threshold:.2f} (F1: {best_candidate['f1']:.4f}, Recall: {best_candidate['recall']:.4f}, FPR: {best_candidate['fpr']:.4f})")
    
    def evaluate_dataset(y_true, y_probs, threshold, name):
        preds = (y_probs >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, preds).ravel()
        
        acc = accuracy_score(y_true, preds)
        prec = precision_score(y_true, preds, zero_division=0)
        rec = recall_score(y_true, preds, zero_division=0)
        f1 = f1_score(y_true, preds, zero_division=0)
        roc_auc = roc_auc_score(y_true, y_probs)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        print("\n" + "-" * 50)
        print(f"EVALUATION: {name}")
        print("-" * 50)
        print(f"Samples:             {len(y_true)}")
        print(f"Decision Threshold:  {threshold:.2f}")
        print(f"Accuracy:            {acc:.4f} ({acc*100:.2f}%)")
        print(f"Precision:           {prec:.4f}")
        print(f"Recall:              {rec:.4f}")
        print(f"F1-score:            {f1:.4f}")
        print(f"ROC-AUC:             {roc_auc:.4f}")
        print(f"False Positive Rate: {fpr:.4f} (FP={fp})")
        print(f"False Negative Rate: {fnr:.4f} (FN={fn})")
        print(f"Confusion Matrix:    [[TN={tn}, FP={fp}], [FN={fn}, TP={tp}]]")
        
        return {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": roc_auc,
            "fpr": fpr,
            "fnr": fnr,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "tp": tp
        }
        
    val_results = evaluate_dataset(y_val_true, y_val_probs, chosen_threshold, "Validation Set")
    test_results = evaluate_dataset(y_test_true, y_test_probs, chosen_threshold, "Untouched Test Benchmark")
    hn_results = evaluate_dataset(y_hn_true, y_hn_probs, chosen_threshold, "Hard-Negative Benchmark")
    
    return {
        "chosen_threshold": chosen_threshold,
        "val_results": val_results,
        "test_results": test_results,
        "hn_results": hn_results
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_path", type=str, default=DEFAULT_TRAIN_PATH)
    parser.add_argument("--lr", type=float, default=DEFAULT_LR)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE)
    parser.add_argument("--output_model", type=str, default="distilbert_model_improved.pt")
    args = parser.parse_args()
    
    train_and_evaluate(
        train_path=args.train_path,
        lr=args.lr,
        epochs=args.epochs,
        batch_size=args.batch_size,
        output_model_name=args.output_model
    )

