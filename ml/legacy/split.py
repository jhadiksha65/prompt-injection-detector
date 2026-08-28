"""
split.py
Splits the prompt injection dataset into stratified Train (70%), Validation (15%),
and Test (15%) partitions using a fixed random seed to ensure reproducibility.
"""

import json
import os
import random
from typing import Dict, List

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

def stratified_split(dataset: List[Dict], train_ratio: float = 0.70, val_ratio: float = 0.15, test_ratio: float = 0.15):
    """
    Performs stratified partitioning by grouping by (label, attack_type)
    to ensure identical class and category proportions across all splits.
    """
    assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Ratios must sum to 1.0"

    # Group samples by category
    groups: Dict[str, List[Dict]] = {}
    for item in dataset:
        key = f"{item['label']}::{item['attack_type']}::{item.get('source', '')}"
        groups.setdefault(key, []).append(item)

    train_set, val_set, test_set = [], [], []

    for key, items in groups.items():
        random.shuffle(items)
        n = len(items)
        n_train = int(round(n * train_ratio))
        n_val = int(round(n * val_ratio))
        
        # Adjust for small groups
        if n > 1 and n_train == 0:
            n_train = 1
        
        train_part = items[:n_train]
        val_part = items[n_train:n_train + n_val]
        test_part = items[n_train + n_val:]

        train_set.extend(train_part)
        val_set.extend(val_part)
        test_set.extend(test_part)

    random.shuffle(train_set)
    random.shuffle(val_set)
    random.shuffle(test_set)

    return train_set, val_set, test_set

def compute_split_stats(name: str, data: List[Dict]) -> Dict:
    total = len(data)
    malicious = sum(1 for d in data if d["label"] == "MALICIOUS")
    benign = sum(1 for d in data if d["label"] == "BENIGN")
    hard_neg = sum(1 for d in data if d["source"] == "hard_negative")
    attack_counts = {}
    for d in data:
        at = d["attack_type"]
        attack_counts[at] = attack_counts.get(at, 0) + 1

    return {
        "split_name": name,
        "total_samples": total,
        "malicious_samples": malicious,
        "benign_samples": benign,
        "hard_negatives": hard_neg,
        "malicious_pct": round((malicious / total) * 100, 2) if total > 0 else 0,
        "benign_pct": round((benign / total) * 100, 2) if total > 0 else 0,
        "attack_type_distribution": attack_counts
    }

def main():
    dataset_dir = os.path.join(os.path.dirname(__file__), "..", "..", "dataset")
    input_file = os.path.join(dataset_dir, "dataset.json")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Dataset file not found at {input_file}. Run build_dataset.py first.")

    with open(input_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    train_set, val_set, test_set = stratified_split(dataset, 0.70, 0.15, 0.15)

    train_path = os.path.join(dataset_dir, "train.json")
    val_path = os.path.join(dataset_dir, "val.json")
    test_path = os.path.join(dataset_dir, "test.json")
    stats_path = os.path.join(dataset_dir, "split_stats.json")

    for path, data in [(train_path, train_set), (val_path, val_set), (test_path, test_set)]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    stats = {
        "random_seed": RANDOM_SEED,
        "ratios": {"train": 0.70, "val": 0.15, "test": 0.15},
        "train": compute_split_stats("train", train_set),
        "validation": compute_split_stats("validation", val_set),
        "test": compute_split_stats("test", test_set)
    }

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print("Stratified Split Completed:")
    print(f"  - Train: {len(train_set)} samples ({stats['train']['malicious_pct']}% Malicious / {stats['train']['benign_pct']}% Benign)")
    print(f"  - Validation: {len(val_set)} samples ({stats['validation']['malicious_pct']}% Malicious / {stats['validation']['benign_pct']}% Benign)")
    print(f"  - Test: {len(test_set)} samples ({stats['test']['malicious_pct']}% Malicious / {stats['test']['benign_pct']}% Benign)")

if __name__ == "__main__":
    main()
