import pandas as pd
from sklearn.model_selection import train_test_split
import os

INPUT = "data/combined/final_balanced.csv"
OUT = "data/final"

df = pd.read_csv(INPUT)

# 70% train, 30% temporary
train, temp = train_test_split(
    df,
    test_size=0.30,
    stratify=df["label"],
    random_state=42
)

# Split remaining 30% equally → 15% validation, 15% test
validation, test = train_test_split(
    temp,
    test_size=0.50,
    stratify=temp["label"],
    random_state=42
)

os.makedirs(OUT, exist_ok=True)

train.to_csv(f"{OUT}/train.csv", index=False)
validation.to_csv(f"{OUT}/validation.csv", index=False)
test.to_csv(f"{OUT}/test.csv", index=False)

print("Dataset split successfully.")
print("Train:", len(train))
print("Validation:", len(validation))
print("Test:", len(test))

print("\nTrain labels:")
print(train["label"].value_counts())

print("\nValidation labels:")
print(validation["label"].value_counts())

print("\nTest labels:")
print(test["label"].value_counts())