"""
PROMPT INJECTION DETECTOR - Validation Threshold Selection

Selects the classification threshold using the VALIDATION set only.

The test set must not be used during threshold selection.
"""

import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from dataset import PromptInjectionDataset
from transformer_classifier import PromptInjectionTransformer


VALIDATION_FILE = "ml/processed/validation_processed.csv"

VOCAB_FILE = "ml/preprocessing/artifacts/vocabulary.json"
CONFIG_FILE = "ml/preprocessing/artifacts/preprocessing_config.json"

MODEL_FILE = "ml/model/artifacts/prompt_injection_transformer.pt"

THRESHOLD_FILE = (
    "ml/model/artifacts/decision_threshold.json"
)

BATCH_SIZE = 32

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def calculate_metrics(predictions, labels):
    predictions = predictions.long()
    labels = labels.long()

    tp = ((predictions == 1) & (labels == 1)).sum().item()
    tn = ((predictions == 0) & (labels == 0)).sum().item()
    fp = ((predictions == 1) & (labels == 0)).sum().item()
    fn = ((predictions == 0) & (labels == 1)).sum().item()

    precision = (
        tp / (tp + fp)
        if tp + fp
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn
        else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    fpr = (
        fp / (fp + tn)
        if fp + tn
        else 0.0
    )

    accuracy = (
        (tp + tn) / len(labels)
        if len(labels)
        else 0.0
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def main():

    print("=" * 60)
    print("PROMPT INJECTION DETECTOR - VALIDATION THRESHOLD SELECTION")
    print("=" * 60)

    print(f"\nDevice: {DEVICE}")

    with open(VOCAB_FILE, "r", encoding="utf-8") as f:
        vocabulary = json.load(f)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    vocab_size = len(vocabulary)
    max_sequence_length = config["max_sequence_length"]

    validation_dataset = PromptInjectionDataset(
        VALIDATION_FILE
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    print(
        f"Validation samples: "
        f"{len(validation_dataset)}"
    )

    model = PromptInjectionTransformer(
        vocab_size=vocab_size,
        max_sequence_length=max_sequence_length
    ).to(DEVICE)

    checkpoint = torch.load(
        MODEL_FILE,
        map_location=DEVICE
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.eval()

    all_probabilities = []
    all_labels = []

    with torch.no_grad():

        for batch in validation_loader:

            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].long().to(DEVICE)

            logits = model(
                input_ids,
                attention_mask
            )

            probabilities = torch.sigmoid(logits)

            all_probabilities.append(
                probabilities.cpu()
            )

            all_labels.append(
                labels.cpu()
            )

    probabilities = torch.cat(all_probabilities)
    labels = torch.cat(all_labels)

    # --------------------------------------------------------
    # Search thresholds
    # --------------------------------------------------------

    results = []

    for i in range(1, 1000):

        threshold = i / 1000

        predictions = (
            probabilities >= threshold
        ).long()

        metrics = calculate_metrics(
            predictions,
            labels
        )

        results.append({
            "threshold": threshold,
            **metrics
        })

    # --------------------------------------------------------
    # Find thresholds satisfying project requirements
    # --------------------------------------------------------

    valid = [
        r for r in results
        if r["recall"] >= 0.95
        and r["fpr"] <= 0.05
    ]

    print("\n" + "=" * 60)
    print("THRESHOLD SEARCH")
    print("=" * 60)

    print(
        f"\nThresholds satisfying "
        f"Recall >= 95% and FPR <= 5%: "
        f"{len(valid)}"
    )

    if not valid:

        print(
            "\nWARNING: No threshold satisfies "
            "both project targets on validation."
        )

        # Select the threshold with the lowest FPR
        # while maintaining the recall requirement.
        recall_valid = [
            r for r in results
            if r["recall"] >= 0.95
        ]

        if not recall_valid:
            raise RuntimeError(
                "No validation threshold achieves "
                "Recall >= 95%."
            )

        selected = min(
            recall_valid,
            key=lambda r: (r["fpr"], -r["recall"])
        )

    else:

        # Among valid thresholds, maximize recall first,
        # then minimize FPR.
        selected = sorted(
            valid,
            key=lambda r: (
                -r["recall"],
                r["fpr"],
                r["threshold"]
            )
        )[0]

    # --------------------------------------------------------
    # Display selected threshold
    # --------------------------------------------------------

    print("\nSELECTED THRESHOLD")
    print("-" * 60)

    print(
        f"Threshold:  {selected['threshold']:.3f}"
    )

    print(
        f"Accuracy:   {selected['accuracy']:.4f}"
    )

    print(
        f"Precision:  {selected['precision']:.4f}"
    )

    print(
        f"Recall:     {selected['recall']:.4f}"
    )

    print(
        f"F1:         {selected['f1']:.4f}"
    )

    print(
        f"FPR:        {selected['fpr']:.4f}"
    )

    print(
        f"\nConfusion matrix:"
    )

    print(
        f"TN={selected['tn']} "
        f"FP={selected['fp']} "
        f"FN={selected['fn']} "
        f"TP={selected['tp']}"
    )

    # --------------------------------------------------------
    # Save threshold
    # --------------------------------------------------------

    Path(THRESHOLD_FILE).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    threshold_config = {
        "threshold": selected["threshold"],
        "selection_dataset": "validation",
        "recall": selected["recall"],
        "fpr": selected["fpr"],
        "precision": selected["precision"],
        "f1": selected["f1"],
        "accuracy": selected["accuracy"],
    }

    with open(
        THRESHOLD_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            threshold_config,
            f,
            indent=2
        )

    print(
        f"\nSaved threshold configuration to:"
        f"\n{THRESHOLD_FILE}"
    )

    print("\n" + "=" * 60)
    print("THRESHOLD SELECTION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
