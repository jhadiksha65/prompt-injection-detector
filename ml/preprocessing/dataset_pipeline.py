"""
Dataset Preprocessing Pipeline

Input:
    data/final/train.csv
    data/final/validation.csv
    data/final/test.csv

Output:
    ml/processed/train_processed.csv
    ml/processed/validation_processed.csv
    ml/processed/test_processed.csv

    ml/preprocessing/artifacts/vocabulary.json
    ml/preprocessing/artifacts/preprocessing_config.json

Responsibilities:
    - Dataset validation
    - Dataset statistics
    - Train/validation/test leakage checks
    - Text normalization
    - Vocabulary creation using TRAINING DATA ONLY
    - Tokenization
    - Sequence conversion
    - Padding/truncation
    - Reusable inference preprocessing
"""

import json
import re
from pathlib import Path
from collections import Counter

import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

TRAIN_FILE = Path("data/final/train.csv")
VALIDATION_FILE = Path("data/final/validation.csv")
TEST_FILE = Path("data/final/test.csv")

OUTPUT_DIR = Path("ml/processed")
ARTIFACT_DIR = Path("ml/preprocessing/artifacts")

TRAIN_OUTPUT = OUTPUT_DIR / "train_processed.csv"
VALIDATION_OUTPUT = OUTPUT_DIR / "validation_processed.csv"
TEST_OUTPUT = OUTPUT_DIR / "test_processed.csv"

VOCAB_FILE = ARTIFACT_DIR / "vocabulary.json"
CONFIG_FILE = ARTIFACT_DIR / "preprocessing_config.json"


# ============================================================
# PREPROCESSING CONFIGURATION
# ============================================================

# Special tokens
PAD_TOKEN = "<PAD>"
UNK_TOKEN = "<UNK>"

PAD_ID = 0
UNK_ID = 1

# Minimum frequency required for a word/token to enter vocabulary.
MIN_FREQUENCY = 1

# This will be selected automatically from the training data.
MAX_SEQUENCE_LENGTH = None

# Vocabulary size limit.
# None means keep all tokens meeting MIN_FREQUENCY.
MAX_VOCAB_SIZE = None


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize prompt text without aggressively destroying
    security-relevant characters.

    We:
        - convert to string
        - remove leading/trailing whitespace
        - normalize repeated whitespace

    We intentionally DO NOT remove punctuation or special
    characters because they can be relevant to prompt attacks.
    """

    if pd.isna(text):
        return ""

    text = str(text)

    # Normalize different types of whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text: str):
    """
    Lightweight tokenizer.

    Words and individual non-whitespace characters are retained.
    This preserves punctuation and special characters.

    Example:

        "Ignore previous instructions!"

    becomes approximately:

        ["Ignore", "previous", "instructions", "!"]
    """

    text = normalize_text(text)

    if not text:
        return []

    return re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)


# ============================================================
# DATASET LOADING
# ============================================================

def load_dataset(path: Path) -> pd.DataFrame:
    """Load and validate one dataset split."""

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    df = pd.read_csv(path)

    required_columns = {
        "prompt",
        "label",
        "attack_type",
        "source",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{path} is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    return df


# ============================================================
# DATASET VALIDATION
# ============================================================

def validate_dataset(df: pd.DataFrame, name: str):
    """Validate one dataset split."""

    print(f"\n{'=' * 60}")
    print(f"VALIDATION: {name}")
    print(f"{'=' * 60}")

    print(f"Samples: {len(df)}")

    # Missing prompts
    missing_prompts = df["prompt"].isna().sum()

    # Empty prompts
    empty_prompts = (
        df["prompt"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

    # Missing labels
    missing_labels = df["label"].isna().sum()

    # Invalid labels
    invalid_labels = (
        ~df["label"].isin([0, 1])
    ).sum()

    print(f"Missing prompts: {missing_prompts}")
    print(f"Empty prompts: {empty_prompts}")
    print(f"Missing labels: {missing_labels}")
    print(f"Invalid labels: {invalid_labels}")

    print("\nClass distribution:")

    counts = df["label"].value_counts().sort_index()

    for label, count in counts.items():
        percentage = (count / len(df)) * 100
        label_name = "Benign" if label == 0 else "Malicious"

        print(
            f"  {label} ({label_name}): "
            f"{count} ({percentage:.2f}%)"
        )

    # Duplicate prompts inside the split
    normalized = (
        df["prompt"]
        .fillna("")
        .map(normalize_text)
    )

    duplicates = normalized.duplicated().sum()

    print(f"\nDuplicate normalized prompts: {duplicates}")


# ============================================================
# DATASET STATISTICS
# ============================================================

def calculate_statistics(df: pd.DataFrame, name: str):
    """Calculate prompt length statistics."""

    token_lengths = (
        df["prompt"]
        .fillna("")
        .map(tokenize)
        .map(len)
    )

    if len(token_lengths) == 0:
        return {}

    statistics = {
        "samples": int(len(df)),
        "minimum_tokens": int(token_lengths.min()),
        "maximum_tokens": int(token_lengths.max()),
        "mean_tokens": float(token_lengths.mean()),
        "median_tokens": float(token_lengths.median()),
        "p90_tokens": float(token_lengths.quantile(0.90)),
        "p95_tokens": float(token_lengths.quantile(0.95)),
        "p99_tokens": float(token_lengths.quantile(0.99)),
    }

    print(f"\n{'=' * 60}")
    print(f"TOKEN STATISTICS: {name}")
    print(f"{'=' * 60}")

    for key, value in statistics.items():
        print(f"{key}: {value}")

    return statistics


# ============================================================
# LEAKAGE CHECK
# ============================================================

def check_split_overlap(train, validation, test):
    """
    Check for exact normalized prompt overlap between
    train/validation/test.

    Ideally every intersection should be zero.
    """

    print(f"\n{'=' * 60}")
    print("TRAIN / VALIDATION / TEST LEAKAGE CHECK")
    print(f"{'=' * 60}")

    train_prompts = set(
        train["prompt"]
        .fillna("")
        .map(normalize_text)
    )

    validation_prompts = set(
        validation["prompt"]
        .fillna("")
        .map(normalize_text)
    )

    test_prompts = set(
        test["prompt"]
        .fillna("")
        .map(normalize_text)
    )

    train_validation = train_prompts & validation_prompts
    train_test = train_prompts & test_prompts
    validation_test = validation_prompts & test_prompts

    print(
        f"Train ∩ Validation: "
        f"{len(train_validation)}"
    )

    print(
        f"Train ∩ Test: "
        f"{len(train_test)}"
    )

    print(
        f"Validation ∩ Test: "
        f"{len(validation_test)}"
    )

    if (
        len(train_validation) == 0
        and len(train_test) == 0
        and len(validation_test) == 0
    ):
        print("\nRESULT: No exact normalized prompt overlap detected.")
    else:
        print(
            "\nWARNING: Overlapping prompts detected. "
            "Investigate before model training."
        )

    return {
        "train_validation_overlap": len(train_validation),
        "train_test_overlap": len(train_test),
        "validation_test_overlap": len(validation_test),
    }


# ============================================================
# VOCABULARY BUILDING
# ============================================================

def build_vocabulary(train_df: pd.DataFrame):
    """
    Build vocabulary ONLY from training data.

    This prevents validation/test information from leaking
    into the vocabulary.
    """

    print(f"\n{'=' * 60}")
    print("BUILDING VOCABULARY")
    print(f"{'=' * 60}")

    counter = Counter()

    for prompt in train_df["prompt"]:
        tokens = tokenize(prompt)
        counter.update(tokens)

    # Keep tokens meeting minimum frequency.
    tokens = [
        token
        for token, frequency in counter.items()
        if frequency >= MIN_FREQUENCY
    ]

    # Sort by frequency, then alphabetically for reproducibility.
    tokens.sort(
        key=lambda token: (-counter[token], token)
    )

    if MAX_VOCAB_SIZE is not None:
        # Reserve space for special tokens.
        tokens = tokens[: MAX_VOCAB_SIZE - 2]

    vocabulary = {
        PAD_TOKEN: PAD_ID,
        UNK_TOKEN: UNK_ID,
    }

    next_id = 2

    for token in tokens:
        vocabulary[token] = next_id
        next_id += 1

    print(f"Unique tokens found: {len(counter)}")
    print(f"Vocabulary size: {len(vocabulary)}")

    return vocabulary


# ============================================================
# DETERMINE MAX SEQUENCE LENGTH
# ============================================================

def determine_max_sequence_length(train_df: pd.DataFrame):
    """
    Select maximum sequence length from the training data.

    We use the 95th percentile rather than the absolute maximum
    so that extremely long outliers do not dominate the model input.

    Minimum is 16.
    Maximum is capped at 512.
    """

    lengths = (
        train_df["prompt"]
        .fillna("")
        .map(tokenize)
        .map(len)
    )

    if len(lengths) == 0:
        return 16

    p95 = int(round(lengths.quantile(0.95)))

    max_length = max(16, p95)

    max_length = min(max_length, 512)

    # Round upward to a convenient value.
    common_lengths = [
        16,
        32,
        64,
        128,
        256,
        384,
        512,
    ]

    selected = 512

    for value in common_lengths:
        if value >= max_length:
            selected = value
            break

    print(f"\n95th percentile token length: {p95}")
    print(f"Selected maximum sequence length: {selected}")

    return selected


# ============================================================
# SEQUENCE CONVERSION
# ============================================================

def text_to_sequence(text: str, vocabulary: dict):
    """Convert tokenized text into integer IDs."""

    tokens = tokenize(text)

    return [
        vocabulary.get(token, UNK_ID)
        for token in tokens
    ]


# ============================================================
# PADDING / TRUNCATION
# ============================================================

def pad_sequence(sequence, max_length):
    """
    Truncate long sequences and pad shorter sequences.

    Padding is performed at the end of the sequence.
    """

    sequence = sequence[:max_length]

    attention_mask = [1] * len(sequence)

    padding_needed = max_length - len(sequence)

    if padding_needed > 0:
        sequence = sequence + [PAD_ID] * padding_needed
        attention_mask = attention_mask + [0] * padding_needed

    return sequence, attention_mask


# ============================================================
# PROCESS DATASET
# ============================================================

def process_dataset(
    df: pd.DataFrame,
    vocabulary: dict,
    max_sequence_length: int,
    name: str,
):
    """Convert a dataset into model-ready numerical representation."""

    processed = df.copy()

    # Normalize prompt.
    processed["normalized_prompt"] = (
        processed["prompt"]
        .fillna("")
        .map(normalize_text)
    )

    sequences = []
    attention_masks = []
    token_lengths = []

    for prompt in processed["normalized_prompt"]:
        sequence = text_to_sequence(
            prompt,
            vocabulary
        )

        token_lengths.append(len(sequence))

        padded, mask = pad_sequence(
            sequence,
            max_sequence_length
        )

        sequences.append(
            json.dumps(padded)
        )

        attention_masks.append(
            json.dumps(mask)
        )

    processed["token_length"] = token_lengths
    processed["input_ids"] = sequences
    processed["attention_mask"] = attention_masks

    print(
        f"Processed {name}: "
        f"{len(processed)} samples"
    )

    return processed


# ============================================================
# SAVE ARTIFACTS
# ============================================================

def save_artifacts(
    vocabulary,
    max_sequence_length,
    statistics,
    leakage_results,
):
    """Save vocabulary and preprocessing configuration."""

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        VOCAB_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            vocabulary,
            f,
            ensure_ascii=False,
            indent=2
        )

    config = {
        "pad_token": PAD_TOKEN,
        "unk_token": UNK_TOKEN,
        "pad_id": PAD_ID,
        "unk_id": UNK_ID,
        "min_frequency": MIN_FREQUENCY,
        "max_vocab_size": MAX_VOCAB_SIZE,
        "max_sequence_length": max_sequence_length,
        "statistics": statistics,
        "leakage_check": leakage_results,
    }

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            config,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\nSaved artifacts:")
    print(f"  {VOCAB_FILE}")
    print(f"  {CONFIG_FILE}")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("PROMPT INJECTION DETECTOR - DATA PREPROCESSING PIPELINE")
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print("\nLoading datasets...")

    train_df = load_dataset(TRAIN_FILE)
    validation_df = load_dataset(VALIDATION_FILE)
    test_df = load_dataset(TEST_FILE)

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_dataset(train_df, "TRAIN")
    validate_dataset(validation_df, "VALIDATION")
    validate_dataset(test_df, "TEST")

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    statistics = {
        "train": calculate_statistics(
            train_df,
            "TRAIN"
        ),
        "validation": calculate_statistics(
            validation_df,
            "VALIDATION"
        ),
        "test": calculate_statistics(
            test_df,
            "TEST"
        ),
    }

    # --------------------------------------------------------
    # Leakage check
    # --------------------------------------------------------

    leakage_results = check_split_overlap(
        train_df,
        validation_df,
        test_df
    )

    # --------------------------------------------------------
    # Build vocabulary
    # --------------------------------------------------------

    vocabulary = build_vocabulary(train_df)

    # --------------------------------------------------------
    # Determine sequence length
    # --------------------------------------------------------

    max_sequence_length = determine_max_sequence_length(
        train_df
    )

    # --------------------------------------------------------
    # Process datasets
    # --------------------------------------------------------

    processed_train = process_dataset(
        train_df,
        vocabulary,
        max_sequence_length,
        "TRAIN"
    )

    processed_validation = process_dataset(
        validation_df,
        vocabulary,
        max_sequence_length,
        "VALIDATION"
    )

    processed_test = process_dataset(
        test_df,
        vocabulary,
        max_sequence_length,
        "TEST"
    )

    # --------------------------------------------------------
    # Save processed datasets
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    processed_train.to_csv(
        TRAIN_OUTPUT,
        index=False,
        encoding="utf-8"
    )

    processed_validation.to_csv(
        VALIDATION_OUTPUT,
        index=False,
        encoding="utf-8"
    )

    processed_test.to_csv(
        TEST_OUTPUT,
        index=False,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Save artifacts
    # --------------------------------------------------------

    save_artifacts(
        vocabulary,
        max_sequence_length,
        statistics,
        leakage_results,
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PROMPT INJECTION DETECTOR - PREPROCESSING COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print("\nInput datasets:")
    print(f"  {TRAIN_FILE}")
    print(f"  {VALIDATION_FILE}")
    print(f"  {TEST_FILE}")

    print("\nOutput datasets:")
    print(f"  {TRAIN_OUTPUT}")
    print(f"  {VALIDATION_OUTPUT}")
    print(f"  {TEST_OUTPUT}")

    print("\nVocabulary size:")
    print(f"  {len(vocabulary)}")

    print("\nMaximum sequence length:")
    print(f"  {max_sequence_length}")

    print("\nPipeline is ready for model integration.")


if __name__ == "__main__":
    main()
