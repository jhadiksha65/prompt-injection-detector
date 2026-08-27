"""
preprocessing.py
Modular NLP text preprocessing, tokenization, vocabulary management,
and sequence conversion pipeline for prompt injection detection.
"""

import re
import string
import json
import os
from typing import List, Dict, Tuple, Optional


class TextPreprocessor:
    """
    Handles text normalization, cleaning, tokenization, vocabulary indexing,
    and sequence padding/truncation.
    """

    PAD_TOKEN = "<PAD>"
    UNK_TOKEN = "<UNK>"

    def __init__(self, max_seq_len: int = 100, min_word_freq: int = 2, max_vocab_size: int = 10000):
        self.max_seq_len = max_seq_len
        self.min_word_freq = min_word_freq
        self.max_vocab_size = max_vocab_size
        self.word2idx: Dict[str, int] = {self.PAD_TOKEN: 0, self.UNK_TOKEN: 1}
        self.idx2word: Dict[int, str] = {0: self.PAD_TOKEN, 1: self.UNK_TOKEN}
        self.word_counts: Dict[str, int] = {}
        self.is_fitted: bool = False

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Normalizes raw text:
        - Converts to lowercase
        - Strips control characters
        - Normalizes multiple whitespaces
        - Preserves semantic punctuation boundaries
        """
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        
        # Lowercase
        text = text.lower()

        # Replace tabs and newlines with spaces
        text = re.sub(r'[\r\n\t]+', ' ', text)

        # Normalize multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenizes normalized text into word tokens while preserving alphanumeric words
        and punctuation tokens.
        """
        cleaned = TextPreprocessor.clean_text(text)
        # Separate punctuation into individual tokens to preserve structural cues
        tokens = re.findall(r'\b\w+\b|[^\w\s]', cleaned)
        return tokens

    def fit_vocabulary(self, texts: List[str]):
        """
        Builds word2idx and idx2word vocabulary from a corpus of texts.
        """
        self.word_counts = {}
        for text in texts:
            tokens = self.tokenize(text)
            for token in tokens:
                self.word_counts[token] = self.word_counts.get(token, 0) + 1

        # Filter by min frequency and sort by frequency
        sorted_words = sorted(
            [w for w, c in self.word_counts.items() if c >= self.min_word_freq],
            key=lambda w: self.word_counts[w],
            reverse=True
        )

        # Cap at max_vocab_size
        sorted_words = sorted_words[:self.max_vocab_size - 2]

        self.word2idx = {self.PAD_TOKEN: 0, self.UNK_TOKEN: 1}
        for idx, word in enumerate(sorted_words, start=2):
            self.word2idx[word] = idx

        self.idx2word = {idx: word for word, idx in self.word2idx.items()}
        self.is_fitted = True

    def text_to_sequence(self, text: str) -> List[int]:
        """
        Converts text to fixed-length integer index sequence with padding/truncation.
        """
        tokens = self.tokenize(text)
        unk_idx = self.word2idx.get(self.UNK_TOKEN, 1)

        # Convert to indices
        seq = [self.word2idx.get(tok, unk_idx) for tok in tokens]

        # Truncate or pad to max_seq_len
        if len(seq) > self.max_seq_len:
            seq = seq[:self.max_seq_len]
        else:
            seq = seq + [0] * (self.max_seq_len - len(seq))

        return seq

    def batch_to_sequences(self, texts: List[str]) -> List[List[int]]:
        """
        Processes a batch of texts into sequences.
        """
        return [self.text_to_sequence(t) for t in texts]

    def save_vocabulary(self, filepath: str):
        """
        Saves vocabulary and configuration to a JSON file.
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {
            "max_seq_len": self.max_seq_len,
            "min_word_freq": self.min_word_freq,
            "max_vocab_size": self.max_vocab_size,
            "vocab_size": len(self.word2idx),
            "word2idx": self.word2idx
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_vocabulary(cls, filepath: str) -> "TextPreprocessor":
        """
        Loads preprocessor and vocabulary from a saved JSON file.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        preprocessor = cls(
            max_seq_len=data["max_seq_len"],
            min_word_freq=data["min_word_freq"],
            max_vocab_size=data["max_vocab_size"]
        )
        preprocessor.word2idx = data["word2idx"]
        preprocessor.idx2word = {int(v): k for k, v in data["word2idx"].items()}
        preprocessor.is_fitted = True
        return preprocessor
