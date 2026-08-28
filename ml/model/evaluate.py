"""
PROMPT INJECTION DETECTOR - MODEL EVALUATION

Evaluates the trained Prompt Injection Detector on the
UNTOUCHED test dataset.

Important:
    - Threshold is selected from validation data only.
    - The selected threshold is loaded from decision_threshold.json.
    - Test data is used only for final evaluation.
"""

import json
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


# ============================================================
# IMPORT MODEL
# ============================================================

from transformer_classifier import PromptInjectionTransformer


# ============================================================
# CONFIGURATION
# ============================================================

TEST_FILE = Path(
    "ml/processed/test_processed.csv"
)

VOCAB_FILE = Path(
    "ml/preprocessing/artifacts/vocabulary.json"
)

CONFIG_FILE = Path(
    "ml/preprocessing/artifacts/preprocessing_config.json"
)

THRESHOLD_FILE = Path(
    "ml/model/artifacts/decision_threshold.json"
)

MODEL_FILE = Path(
    "ml/model/artifacts/prompt_injection_transformer.pt"
)

BATCH_SIZE = 32

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):
    """Load a JSON file."""

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# LOAD TEST DATA
# ============================================================

def load_test_dataset():
    """Load the processed test dataset."""

    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"Test dataset not found: {TEST_FILE}"
        )

    df = pd.read_csv(TEST_FILE)

    input_ids = torch.tensor(
        df["input_ids"].apply(json.loads).tolist(),
        dtype=torch.long,
    )

    attention_mask = torch.tensor(
        df["attention_mask"].apply(json.loads).tolist(),
        dtype=torch.long,
    )

    labels = torch.tensor(
        df["label"].astype(int).values,
        dtype=torch.long,
    )

    dataset = TensorDataset(
        input_ids,
        attention_mask,
        labels,
    )

    return df, dataset


# ============================================================
# LOAD MODEL
# ============================================================

def load_model(vocab_size, sequence_length):
    """Create model and load trained weights."""

    model = PromptInjectionTransformer(
        vocab_size=vocab_size,
        max_sequence_length=sequence_length,
    )

    checkpoint = torch.load(
        MODEL_FILE,
        map_location=DEVICE,
        weights_only=False,
    )

    # Support either a raw state_dict or a checkpoint dictionary.
    if isinstance(checkpoint, dict):
        if "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        elif "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
        else:
            state_dict = checkpoint
    else:
        state_dict = checkpoint

    model.load_state_dict(state_dict)

    model.to(DEVICE)
    model.eval()

    return model


# ============================================================
# GET PROBABILITIES
# ============================================================

def get_predictions(model, dataloader):
    """Generate malicious probabilities for the test set."""

    probabilities = []
    labels = []

    with torch.no_grad():

        for input_ids, attention_mask, batch_labels in dataloader:

            input_ids = input_ids.to(DEVICE)
            attention_mask = attention_mask.to(DEVICE)

            logits = model(
                input_ids,
                attention_mask,
            )

            # Model outputs one logit per sample.
            probs = torch.sigmoid(logits)

            probabilities.extend(
                probs.cpu().numpy().tolist()
            )

            labels.extend(
                batch_labels.numpy().tolist()
            )

    return probabilities, labels


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PROMPT INJECTION DETECTOR - MODEL EVALUATION")
    print("=" * 60)

    print()
    print(f"Device: {DEVICE}")

    # --------------------------------------------------------
    # Load preprocessing configuration
    # --------------------------------------------------------

    config = load_json(CONFIG_FILE)
    vocabulary = load_json(VOCAB_FILE)
    threshold_config = load_json(THRESHOLD_FILE)

    vocab_size = len(vocabulary)

    sequence_length = config[
        "max_sequence_length"
    ]

    threshold = threshold_config[
        "threshold"
    ]

    print(
        f"Vocabulary size: {vocab_size}"
    )

    print(
        f"Sequence length: {sequence_length}"
    )

    print(
        f"Decision threshold: {threshold:.3f}"
    )

    # --------------------------------------------------------
    # Load test dataset
    # --------------------------------------------------------

    test_df, test_dataset = load_test_dataset()

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    print(
        f"\nTest samples: {len(test_dataset)}"
    )

    # --------------------------------------------------------
    # Load trained model
    # --------------------------------------------------------

    model = load_model(
        vocab_size,
        sequence_length,
    )

    print(
        f"Loaded model: {MODEL_FILE}"
    )

    # --------------------------------------------------------
    # Get predictions
    # --------------------------------------------------------

    probabilities, labels = get_predictions(
        model,
        test_loader,
    )

    # --------------------------------------------------------
    # Apply validation-selected threshold
    # --------------------------------------------------------

    predictions = [
        1 if probability >= threshold else 0
        for probability in probabilities
    ]

    # --------------------------------------------------------
    # Calculate metrics
    # --------------------------------------------------------

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    precision = precision_score(
        labels,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        labels,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        labels,
        predictions,
        zero_division=0,
    )

    tn, fp, fn, tp = confusion_matrix(
        labels,
        predictions,
        labels=[0, 1],
    ).ravel()

    fpr = fp / (fp + tn)

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("FINAL TEST SET RESULTS")
    print("=" * 60)

    print()
    print(
        f"Threshold:          {threshold:.3f}"
    )

    print(
        f"Accuracy:           {accuracy:.4f} "
        f"({accuracy * 100:.2f}%)"
    )

    print(
        f"Precision:          {precision:.4f} "
        f"({precision * 100:.2f}%)"
    )

    print(
        f"Recall:             {recall:.4f} "
        f"({recall * 100:.2f}%)"
    )

    print(
        f"F1-score:           {f1:.4f} "
        f"({f1 * 100:.2f}%)"
    )

    print(
        f"False Positive Rate:{fpr:.4f} "
        f"({fpr * 100:.2f}%)"
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    print()
    print("Confusion Matrix:")
    print(
        "                 Predicted"
    )
    print(
        "                 Benign  Malicious"
    )
    print(
        f"Actual Benign    {tn:6d}  {fp:9d}"
    )
    print(
        f"Actual Malicious {fn:6d}  {tp:9d}"
    )

    # --------------------------------------------------------
    # Project target checks
    # --------------------------------------------------------

    recall_pass = recall >= 0.95
    fpr_pass = fpr <= 0.05
    precision_pass = precision >= 0.90
    f1_pass = f1 >= 0.92

    print()
    print("=" * 60)
    print("PROJECT TARGET CHECK")
    print("=" * 60)

    print(
        f"Recall >= 95%:       "
        f"{'PASS' if recall_pass else 'FAIL'}"
    )

    print(
        f"FPR <= 5%:           "
        f"{'PASS' if fpr_pass else 'FAIL'}"
    )

    print(
        f"Precision >= 90%:    "
        f"{'PASS' if precision_pass else 'FAIL'}"
    )

    print(
        f"F1 >= 92%:           "
        f"{'PASS' if f1_pass else 'FAIL'}"
    )

    print()
    print("=" * 60)
    print("EVALUATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
