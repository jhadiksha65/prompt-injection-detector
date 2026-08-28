"""
PyTorch Dataset Loader

Loads the processed datasets created by the preprocessing pipeline
preprocessing pipeline.

Expected columns:
    input_ids
    attention_mask
    label
"""

import json
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import Dataset


class PromptInjectionDataset(Dataset):
    """PyTorch Dataset for processed prompt-injection data."""

    def __init__(self, csv_file):
        self.csv_file = Path(csv_file)

        if not self.csv_file.exists():
            raise FileNotFoundError(
                f"Processed dataset not found: {self.csv_file}"
            )

        self.data = pd.read_csv(self.csv_file)

        required_columns = {
            "input_ids",
            "attention_mask",
            "label",
        }

        missing = required_columns - set(self.data.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        if self.data.empty:
            raise ValueError(
                f"Dataset is empty: {self.csv_file}"
            )

        # Validate labels.
        if not self.data["label"].isin([0, 1]).all():
            raise ValueError(
                f"Invalid labels found in {self.csv_file}"
            )

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        row = self.data.iloc[index]

        input_ids = torch.tensor(
            json.loads(row["input_ids"]),
            dtype=torch.long,
        )

        attention_mask = torch.tensor(
            json.loads(row["attention_mask"]),
            dtype=torch.long,
        )

        label = torch.tensor(
            int(row["label"]),
            dtype=torch.long,
        )

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "label": label,
        }


def load_datasets(data_dir="ml/processed"):
    """
    Load the train, validation and test datasets.

    Returns:
        train_dataset
        validation_dataset
        test_dataset
    """

    data_dir = Path(data_dir)

    train_dataset = PromptInjectionDataset(
        data_dir / "train_processed.csv"
    )

    validation_dataset = PromptInjectionDataset(
        data_dir / "validation_processed.csv"
    )

    test_dataset = PromptInjectionDataset(
        data_dir / "test_processed.csv"
    )

    return (
        train_dataset,
        validation_dataset,
        test_dataset,
    )


if __name__ == "__main__":
    print("=" * 60)
    print("PROMPT INJECTION DETECTOR - DATASET LOADER TEST")
    print("=" * 60)

    train, validation, test = load_datasets()

    print(f"Train samples:      {len(train)}")
    print(f"Validation samples: {len(validation)}")
    print(f"Test samples:       {len(test)}")

    sample = train[0]

    print("\nSample:")
    print("input_ids shape:", sample["input_ids"].shape)
    print(
        "attention_mask shape:",
        sample["attention_mask"].shape,
    )
    print("label:", sample["label"].item())

    print("\nDataset loader test completed successfully.")
