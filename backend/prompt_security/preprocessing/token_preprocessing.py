"""
token_preprocessing.py
Shared Tokenization and Head+Tail Preprocessing Module for Prompt Injection Detection.
Used across training, offline evaluation, and inference pipelines to guarantee byte-for-byte
and token-for-token consistency.
"""

import torch
from typing import Dict, Any, List
from transformers import DistilBertTokenizer

DEFAULT_MAX_LEN = 256
CHECKPOINT = "distilbert-base-uncased"

def encode_prompt_head_tail(
    text: str,
    tokenizer: DistilBertTokenizer,
    max_len: int = DEFAULT_MAX_LEN,
    return_tensors: str = "pt"
) -> Dict[str, Any]:
    """
    Tokenizes text with head+tail retention for prompts exceeding max_len.
    
    Structure for prompt tokens when len(content_tokens) > max_len - 2:
      [CLS] + head_tokens[:head_len] + tail_tokens[-tail_len:] + [SEP]
    where:
      budget = max_len - 2  (reserving 2 slots for CLS and SEP)
      head_len = budget // 2 = 127
      tail_len = budget - head_len = 127
      total tokens = 1 + 127 + 127 + 1 = 256.
      
    For prompts with content tokens <= budget:
      [CLS] + content_tokens + [SEP] + [PAD]...
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
        
    cls_token_id = tokenizer.cls_token_id
    sep_token_id = tokenizer.sep_token_id
    pad_token_id = tokenizer.pad_token_id
    # Tokenize without special tokens to inspect full raw token sequence.
    # Note: HuggingFace tokenizers check against self.model_max_length (512) and emit a warning
    # if raw input > 512, even though our function immediately reduces it to max_len (256).
    orig_max_len = tokenizer.model_max_length
    try:
        tokenizer.model_max_length = int(1e9)
        token_ids = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    finally:
        tokenizer.model_max_length = orig_max_len
        
    budget = max_len - 2  # account for [CLS] and [SEP]
    
    if len(token_ids) <= budget:
        # Fits comfortably within budget: standard CLS + tokens + SEP + padding
        input_ids = [cls_token_id] + token_ids + [sep_token_id]
        attention_mask = [1] * len(input_ids)
        pad_len = max_len - len(input_ids)
        if pad_len > 0:
            input_ids += [pad_token_id] * pad_len
            attention_mask += [0] * pad_len
    else:
        # Exceeds budget: split into head and tail preservation
        head_len = budget // 2
        tail_len = budget - head_len
        head_tokens = token_ids[:head_len]
        tail_tokens = token_ids[-tail_len:]
        input_ids = [cls_token_id] + head_tokens + tail_tokens + [sep_token_id]
        attention_mask = [1] * max_len
        
    if return_tensors == "pt":
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long)
        }
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask
    }
