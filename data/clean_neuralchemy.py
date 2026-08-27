from datasets import load_from_disk
import pandas as pd
import os

input_dir = "data/raw/neuralchemy_full"
output_file = "data/processed/neuralchemy_clean.csv"

ds = load_from_disk(input_dir)

rows = []

for split in ["train", "validation", "test"]:
    for r in ds[split]:
        prompt = str(r.get("text", "")).strip()

        if not prompt:
            continue

        rows.append({
            "prompt": prompt,
            "label": int(r["label"]),
            "attack_type": str(r.get("category", "unknown")),
            "source": "Neuralchemy"
        })

df = pd.DataFrame(rows)

# Remove exact duplicate prompts
df = df.drop_duplicates(subset=["prompt"])

os.makedirs("data/processed", exist_ok=True)

df.to_csv(output_file, index=False, encoding="utf-8")

print("Neuralchemy dataset cleaned successfully.")
print("Total samples:", len(df))
print("\nLabels:")
print(df["label"].value_counts())
print("\nTop attack types:")
print(df["attack_type"].value_counts().head(20))
print("\nSaved to:", output_file)