import pandas as pd
import os

INPUT = "data/combined/all_clean_deduplicated.csv"
OUTPUT = "data/combined/final_balanced.csv"

df = pd.read_csv(INPUT)

benign = df[df["label"] == 0].copy()
malicious = df[df["label"] == 1].copy()

target = len(benign)

# Proportional sampling while preserving all columns
malicious_balanced = (
    malicious
    .groupby("attack_type", group_keys=False)
    .sample(frac=target / len(malicious), random_state=42)
)

# Correct rounding difference
if len(malicious_balanced) > target:
    malicious_balanced = malicious_balanced.sample(
        n=target, random_state=42
    )
elif len(malicious_balanced) < target:
    remaining = malicious.drop(malicious_balanced.index)
    extra = remaining.sample(
        n=target - len(malicious_balanced),
        random_state=42
    )
    malicious_balanced = pd.concat(
        [malicious_balanced, extra]
    )

final_df = pd.concat(
    [benign, malicious_balanced],
    ignore_index=True
)

final_df = final_df.sample(
    frac=1, random_state=42
).reset_index(drop=True)

os.makedirs("data/combined", exist_ok=True)
final_df.to_csv(OUTPUT, index=False)

print("Final balanced dataset created.")
print("Total:", len(final_df))
print("\nLabels:")
print(final_df["label"].value_counts())

print("\nSources:")
print(final_df["source"].value_counts())

print("\nMalicious attack types:")
print(
    final_df[final_df["label"] == 1]["attack_type"]
    .value_counts()
)

print("\nColumns:")
print(final_df.columns.tolist())

print("\nSaved to:", OUTPUT)