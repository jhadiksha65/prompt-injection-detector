import json
import pandas as pd

input_file = "data/raw/Prompt_INJECTION_And_Benign_DATASET.jsonl"
output_file = "data/processed/kaggle_clean.csv"

rows = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)

        prompt = str(r.get("prompt", "")).strip()
        label = 1 if str(r.get("label", "")).lower() == "malicious" else 0
        attack_type = str(r.get("attack_type", "none")).strip()

        if prompt:
            rows.append({
                "prompt": prompt,
                "label": label,
                "attack_type": attack_type,
                "source": "Kaggle"
            })

df = pd.DataFrame(rows)

# Remove exact duplicate prompts
df = df.drop_duplicates(subset=["prompt"])

df.to_csv(output_file, index=False, encoding="utf-8")

print("Kaggle dataset cleaned successfully.")
print("Total samples:", len(df))
print("\nLabels:")
print(df["label"].value_counts())
print("\nAttack types:")
print(df["attack_type"].value_counts())
print("\nSaved to:", output_file)