from datasets import load_dataset
import pandas as pd
import os

output_file = "data/processed/wambosec_clean.csv"

ds = load_dataset("wambosec/prompt-injections")

rows = []

for split in ["train", "test"]:
    for r in ds[split]:
        prompt = str(r.get("prompt", "")).strip()

        if not prompt:
            continue

        rows.append({
            "prompt": prompt,
            "label": int(r["label"]),
            "attack_type": str(r.get("category") or "unknown"),
            "source": "WamboSec"
        })

df = pd.DataFrame(rows)

df = df.drop_duplicates(subset=["prompt"])

os.makedirs("data/processed", exist_ok=True)

df.to_csv(output_file, index=False, encoding="utf-8")

print("WamboSec dataset cleaned successfully.")
print("Total samples:", len(df))
print("\nLabels:")
print(df["label"].value_counts())
print("\nTop attack types:")
print(df["attack_type"].value_counts().head(20))
print("\nSaved to:", output_file)