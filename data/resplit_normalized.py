import pandas as pd
import re
from sklearn.model_selection import train_test_split

INPUT = r"data\combined\final_balanced.csv"
OUT = r"data\final"

def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

df = pd.read_csv(INPUT)

# Normalize prompts
df["normalized_prompt"] = df["prompt"].map(normalize_text)

print("Before normalized deduplication:", len(df))

# Remove duplicates after normalization
df = df.drop_duplicates(
    subset="normalized_prompt",
    keep="first"
).reset_index(drop=True)

print("After normalized deduplication:", len(df))

# Remove helper column
df = df.drop(columns=["normalized_prompt"])

print("\nLabels:")
print(df["label"].value_counts())

# 70% train, 30% temporary
train, temp = train_test_split(
    df,
    test_size=0.30,
    stratify=df["label"],
    random_state=42
)

# 15% validation, 15% test
validation, test = train_test_split(
    temp,
    test_size=0.50,
    stratify=temp["label"],
    random_state=42
)

# Leakage check using the SAME normalization
train_prompts = set(train["prompt"].map(normalize_text))
validation_prompts = set(validation["prompt"].map(normalize_text))
test_prompts = set(test["prompt"].map(normalize_text))

print("\nNormalized leakage:")
print("Train ∩ Validation:", len(train_prompts & validation_prompts))
print("Train ∩ Test:", len(train_prompts & test_prompts))
print("Validation ∩ Test:", len(validation_prompts & test_prompts))

# Save
train.to_csv(f"{OUT}/train.csv", index=False)
validation.to_csv(f"{OUT}/validation.csv", index=False)
test.to_csv(f"{OUT}/test.csv", index=False)

print("\nSplits saved.")
print("Train:", len(train))
print("Validation:", len(validation))
print("Test:", len(test))

print("\nTrain labels:")
print(train["label"].value_counts())

print("\nValidation labels:")
print(validation["label"].value_counts())

print("\nTest labels:")
print(test["label"].value_counts())