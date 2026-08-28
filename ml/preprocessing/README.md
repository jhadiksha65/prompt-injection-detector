# Dataset Preprocessing Pipeline

## 1. Purpose

This directory contains the preprocessing pipeline developed for the
Prompt Injection Detector project.

The pipeline takes the cleaned, balanced, and stratified datasets prepared
by the dataset engineering work and converts the prompt text into a
model-ready numerical representation.

---

## 2. Input Dataset

The preprocessing pipeline uses the following datasets:

```text
data/final/train.csv
data/final/validation.csv
data/final/test.csv
