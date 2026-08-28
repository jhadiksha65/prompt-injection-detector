"""
PROMPT INJECTION DETECTOR - TRANSFORMER TRAINING

Trains the prompt-injection classifier using the processed
train/validation datasets.
"""

import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from dataset import PromptInjectionDataset
from transformer_classifier import PromptInjectionTransformer


# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_FILE = "ml/processed/train_processed.csv"
VALIDATION_FILE = "ml/processed/validation_processed.csv"

ARTIFACT_FILE = "ml/preprocessing/artifacts/preprocessing_config.json"

MODEL_DIR = Path("ml/model/artifacts")
MODEL_FILE = MODEL_DIR / "prompt_injection_transformer.pt"

BATCH_SIZE = 32
EPOCHS = 5
LEARNING_RATE = 1e-4

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(logits, labels):
    """Calculate accuracy, precision, recall and F1."""

    predictions = (torch.sigmoid(logits) >= 0.5).long()

    labels = labels.long()

    tp = ((predictions == 1) & (labels == 1)).sum().item()
    tn = ((predictions == 0) & (labels == 0)).sum().item()
    fp = ((predictions == 1) & (labels == 0)).sum().item()
    fn = ((predictions == 0) & (labels == 1)).sum().item()

    total = len(labels)

    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    if precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    return accuracy, precision, recall, f1


# ============================================================
# EVALUATION
# ============================================================

def evaluate(model, loader, criterion):
    """Evaluate model on validation data."""

    model.eval()

    total_loss = 0.0
    all_logits = []
    all_labels = []

    with torch.no_grad():

        for batch in loader:

            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].float().to(DEVICE)

            logits = model(
                input_ids,
                attention_mask
            )

            loss = criterion(logits, labels)

            total_loss += loss.item()

            all_logits.append(logits.cpu())
            all_labels.append(labels.cpu())

    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels)

    accuracy, precision, recall, f1 = calculate_metrics(
        logits,
        labels
    )

    average_loss = total_loss / len(loader)

    return average_loss, accuracy, precision, recall, f1


# ============================================================
# MAIN TRAINING
# ============================================================

def main():

    print("=" * 60)
    print("PROMPT INJECTION DETECTOR - TRANSFORMER TRAINING")
    print("=" * 60)

    print(f"\nDevice: {DEVICE}")

    # --------------------------------------------------------
    # Load preprocessing configuration
    # --------------------------------------------------------

    with open(
        ARTIFACT_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        config = json.load(f)

    vocab_size = len(
        json.load(
            open(
                "ml/preprocessing/artifacts/vocabulary.json",
                "r",
                encoding="utf-8"
            )
        )
    )

    max_sequence_length = config["max_sequence_length"]

    print(f"Vocabulary size: {vocab_size}")
    print(f"Sequence length: {max_sequence_length}")

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    train_dataset = PromptInjectionDataset(TRAIN_FILE)
    validation_dataset = PromptInjectionDataset(VALIDATION_FILE)

    print(f"\nTrain samples: {len(train_dataset)}")
    print(f"Validation samples: {len(validation_dataset)}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    # --------------------------------------------------------
    # Create model
    # --------------------------------------------------------

    model = PromptInjectionTransformer(
        vocab_size=vocab_size,
        max_sequence_length=max_sequence_length
    ).to(DEVICE)

    print(
        f"\nModel parameters: "
        f"{sum(p.numel() for p in model.parameters()):,}"
    )

    # --------------------------------------------------------
    # Optimizer and loss
    # --------------------------------------------------------

    criterion = torch.nn.BCEWithLogitsLoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE
    )

    # --------------------------------------------------------
    # Training
    # --------------------------------------------------------

    best_f1 = 0.0

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for epoch in range(1, EPOCHS + 1):

        model.train()

        total_loss = 0.0

        for batch in train_loader:

            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].float().to(DEVICE)

            optimizer.zero_grad()

            logits = model(
                input_ids,
                attention_mask
            )

            loss = criterion(
                logits,
                labels
            )

            loss.backward()

            optimizer.step()

            total_loss += loss.item()

        train_loss = total_loss / len(train_loader)

        (
            validation_loss,
            accuracy,
            precision,
            recall,
            f1
        ) = evaluate(
            model,
            validation_loader,
            criterion
        )

        print("\n" + "-" * 60)
        print(f"Epoch {epoch}/{EPOCHS}")
        print(f"Train loss:      {train_loss:.4f}")
        print(f"Validation loss: {validation_loss:.4f}")
        print(f"Accuracy:        {accuracy:.4f}")
        print(f"Precision:       {precision:.4f}")
        print(f"Recall:          {recall:.4f}")
        print(f"F1:              {f1:.4f}")

        # ----------------------------------------------------
        # Save best model
        # ----------------------------------------------------

        if f1 > best_f1:

            best_f1 = f1

            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "vocab_size": vocab_size,
                    "max_sequence_length": max_sequence_length,
                    "best_validation_f1": best_f1,
                },
                MODEL_FILE
            )

            print(
                f"Saved best model to: {MODEL_FILE}"
            )

    print("\n" + "=" * 60)
    print("TRAINING COMPLETED")
    print("=" * 60)

    print(f"Best validation F1: {best_f1:.4f}")
    print(f"Model: {MODEL_FILE}")


if __name__ == "__main__":
    main()
