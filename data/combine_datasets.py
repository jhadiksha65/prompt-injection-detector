import pandas as pd
import os

files = [
    "data/processed/kaggle_clean.csv",
    "data/processed/neuralchemy_clean.csv",
    "data/processed/wambosec_clean.csv"
]

dfs = [pd.read_csv(f) for f in files]
df = pd.concat(dfs, ignore_index=True)

print("Before deduplication:", len(df))

# Normalize whitespace
df["prompt"] = df["prompt"].str.replace(r"\s+", " ", regex=True).str.strip()

# Remove exact duplicates
df = df.drop_duplicates(subset=["prompt"], keep="first")

print("After deduplication:", len(df))
print("\nLabels:")
print(df["label"].value_counts())

print("\nSources:")
print(df["source"].value_counts())

os.makedirs("data/combined", exist_ok=True)
df.to_csv("data/combined/all_clean_deduplicated.csv", index=False)

print("\nSaved successfully.")