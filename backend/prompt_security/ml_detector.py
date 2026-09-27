"""
ml_detector.py
Inference wrapper for the trained Machine Learning Prompt Injection Classifier.
Loads DistilBERT tokenizer and classification weights and provides prediction probability.
"""

import os
import sys
import json
import torch
from typing import Dict, Any, Optional
from transformers import DistilBertTokenizer, AutoModelForSequenceClassification

from .threat_taxonomy import ThreatCategory

# Add root directory to sys.path if needed
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.prompt_security.preprocessing.token_preprocessing import encode_prompt_head_tail, DEFAULT_MAX_LEN


class MLPromptDetector:
    """
    Loads trained DistilBERT model artifacts and computes the probability of malicious prompt injection.
    """

    def __init__(self, models_dir: Optional[str] = None):
        self.checkpoint = "distilbert-base-uncased"
        
        # Priority resolution for checkpoint: augmented > improved > base
        augmented_path = os.path.abspath(os.path.join(ROOT_DIR, "experiments", "distilbert", "distilbert_model_augmented.pt"))
        improved_path = os.path.abspath(os.path.join(ROOT_DIR, "experiments", "distilbert", "distilbert_model_improved.pt"))
        base_path = os.path.abspath(os.path.join(ROOT_DIR, "experiments", "distilbert", "distilbert_model.pt"))
        
        if os.path.exists(augmented_path):
            self.model_path = augmented_path
        elif os.path.exists(improved_path):
            self.model_path = improved_path
        else:
            self.model_path = base_path

        # Threshold and sequence length configuration (loaded from validation metadata)
        self.max_len = DEFAULT_MAX_LEN  # 256
        self.threshold = 0.38
        meta_path = os.path.abspath(os.path.join(ROOT_DIR, "experiments", "distilbert", "validation_threshold_metadata_augmented.json"))
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    self.threshold = float(meta.get("chosen_threshold", 0.38))
                    self.max_len = int(meta.get("max_len", DEFAULT_MAX_LEN))
            except Exception as e:
                print(f"[MLPromptDetector] Notice: Could not read metadata {meta_path} ({e}), defaulting threshold to {self.threshold}")

        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        
        # Choose Device (MPS, CUDA, or CPU)
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
            
        self._load_model()

    def _load_model(self):
        """Loads tokenizer and PyTorch state dict from disk if available."""
        if os.path.exists(self.model_path):
            try:
                # Load tokenizer from cache or download
                self.tokenizer = DistilBertTokenizer.from_pretrained(self.checkpoint)
                
                # Load model architecture and map state dict
                self.model = AutoModelForSequenceClassification.from_pretrained(self.checkpoint, num_labels=2)
                state_dict = torch.load(self.model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.model.to(self.device)
                self.model.eval()
                self.is_loaded = True
                print(f"[MLPromptDetector] Successfully loaded DistilBERT model weights from: {self.model_path} (threshold={self.threshold:.2f}, max_len={self.max_len}) onto device: {self.device}")
            except Exception as e:
                print(f"[MLPromptDetector] Error loading model: {e}")
                self.is_loaded = False
        else:
            print(f"[MLPromptDetector] Model file not found at: {self.model_path}")
            self.is_loaded = False

    def predict_probability(self, prompt: str) -> Dict[str, Any]:
        """
        Computes the malicious probability for a prompt using DistilBERT.
        """
        if not prompt or not isinstance(prompt, str):
            return {
                "ml_available": self.is_loaded,
                "malicious_probability": 0.0,
                "ml_score": 0.0,
                "is_malicious": False,
                "confidence": 1.0
            }

        if not self.is_loaded:
            return {
                "ml_available": False,
                "malicious_probability": 0.0,
                "ml_score": 0.0,
                "is_malicious": False,
                "confidence": 0.0
            }

        cleaned_text = str(prompt).strip()
        
        # Tokenize inputs using verified head+tail preservation
        encoding = encode_prompt_head_tail(
            text=cleaned_text,
            tokenizer=self.tokenizer,
            max_len=self.max_len,
            return_tensors="pt"
        )
        
        input_ids = encoding["input_ids"].unsqueeze(0).to(self.device)
        attention_mask = encoding["attention_mask"].unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=1)
            malicious_prob = float(probs[0, 1].item())
            
        ml_score = round(malicious_prob * 100.0, 2)
        # Apply the validated threshold (0.38 loaded from metadata)
        is_malicious = malicious_prob >= self.threshold
        confidence = float(probs[0, 1].item()) if is_malicious else float(probs[0, 0].item())

        return {
            "ml_available": True,
            "malicious_probability": round(malicious_prob, 4),
            "ml_score": ml_score,
            "is_malicious": is_malicious,
            "confidence": round(confidence, 4)
        }
