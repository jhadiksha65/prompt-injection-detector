"""
ml_detector.py
Inference wrapper for the trained Machine Learning Prompt Injection Classifier.
Loads DistilBERT tokenizer and classification weights and provides prediction probability.

The production model is FROZEN (see model_integrity.EXPECTED_MODEL_SHA256). This
wrapper verifies the on-disk weights against that pinned digest before loading,
and reports a precise ModelLoadStatus so a degraded pipeline is never mistaken
for a healthy one.
"""

import os
import sys
import json
from typing import Dict, Any, Optional

from .threat_taxonomy import ThreatCategory
from .model_integrity import (
    EXPECTED_MODEL_SHA256,
    FROZEN_DECISION_THRESHOLD,
    ModelLoadStatus,
    PipelineMode,
    inspect_weights_file,
)

# Add root directory to sys.path if needed
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# torch / transformers are optional at import time so that the API can still
# boot and truthfully report TORCH_UNAVAILABLE instead of failing to start.
try:
    import torch
    _TORCH_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - environment dependent
    torch = None
    _TORCH_IMPORT_ERROR = exc

try:
    from transformers import DistilBertTokenizer, AutoModelForSequenceClassification
    _TRANSFORMERS_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - environment dependent
    DistilBertTokenizer = None
    AutoModelForSequenceClassification = None
    _TRANSFORMERS_IMPORT_ERROR = exc

from backend.prompt_security.preprocessing.token_preprocessing import (
    encode_prompt_head_tail,
    DEFAULT_MAX_LEN,
)


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
        self.threshold = FROZEN_DECISION_THRESHOLD  # 0.38
        self.threshold_source = "pinned_default"
        meta_path = os.path.abspath(os.path.join(ROOT_DIR, "experiments", "distilbert", "validation_threshold_metadata_augmented.json"))
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    self.threshold = float(meta.get("chosen_threshold", FROZEN_DECISION_THRESHOLD))
                    self.max_len = int(meta.get("max_len", DEFAULT_MAX_LEN))
                    self.threshold_source = os.path.basename(meta_path)
            except Exception as e:
                print(f"[MLPromptDetector] Notice: Could not read metadata {meta_path} ({e}), defaulting threshold to {self.threshold}")

        # The decision threshold is part of the frozen model contract. Surface any
        # drift loudly rather than silently scoring against an unexpected value.
        self.threshold_matches_frozen = abs(self.threshold - FROZEN_DECISION_THRESHOLD) < 1e-9
        if not self.threshold_matches_frozen:
            print(
                f"[MLPromptDetector] WARNING: decision threshold {self.threshold} from "
                f"{self.threshold_source} differs from the frozen production threshold "
                f"{FROZEN_DECISION_THRESHOLD}."
            )

        self.tokenizer = None
        self.model = None
        self.load_status = ModelLoadStatus.LOAD_ERROR
        self.load_detail = "Model load has not been attempted."
        self.model_sha256 = None
        self.expected_model_sha256 = EXPECTED_MODEL_SHA256
        self.device = None

        self._load_model()

    # -- Derived state -----------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        """True only when verified production weights are loaded and usable."""
        return self.load_status == ModelLoadStatus.LOADED_VERIFIED

    @property
    def pipeline_mode(self) -> str:
        """FULL when the verified ML classifier participates, else RULE_ONLY."""
        return PipelineMode.FULL.value if self.is_loaded else PipelineMode.RULE_ONLY.value

    def status_report(self) -> Dict[str, Any]:
        """Operator-facing summary of model load state and frozen-model identity."""
        return {
            "load_status": self.load_status.value,
            "load_detail": self.load_detail,
            "is_loaded": self.is_loaded,
            "pipeline_mode": self.pipeline_mode,
            "degraded": not self.is_loaded,
            "model_path": self.model_path,
            "model_sha256": self.model_sha256,
            "expected_model_sha256": self.expected_model_sha256,
            "decision_threshold": self.threshold,
            "decision_threshold_source": self.threshold_source,
            "decision_threshold_matches_frozen": self.threshold_matches_frozen,
            "max_len": self.max_len,
            "device": str(self.device) if self.device is not None else None,
        }

    # -- Loading -----------------------------------------------------------

    def _select_device(self):
        """Chooses MPS, CUDA or CPU. Requires torch."""
        try:
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return torch.device("mps")
        except Exception:
            pass
        try:
            if torch.cuda.is_available():
                return torch.device("cuda")
        except Exception:
            pass
        return torch.device("cpu")

    def _load_model(self):
        """
        Loads the tokenizer and verified weights, recording a precise status.

        Order matters: the local weights file is validated FIRST, because it is
        cheap and offline. A blocked tokenizer download must never mask a
        missing, unfetched or tampered checkpoint.
        """
        # 1. Validate the weights file itself (no torch, no network).
        blocking_status, detail, sha = inspect_weights_file(self.model_path, self.expected_model_sha256)
        self.model_sha256 = sha
        if blocking_status is not None:
            self.load_status = blocking_status
            self.load_detail = detail
            print(f"[MLPromptDetector] {self.load_status.value}: {detail}")
            return

        # 2. Require torch / transformers.
        if torch is None:
            self.load_status = ModelLoadStatus.TORCH_UNAVAILABLE
            self.load_detail = f"PyTorch is not importable: {_TORCH_IMPORT_ERROR}"
            print(f"[MLPromptDetector] {self.load_status.value}: {self.load_detail}")
            return
        if DistilBertTokenizer is None or AutoModelForSequenceClassification is None:
            self.load_status = ModelLoadStatus.TORCH_UNAVAILABLE
            self.load_detail = f"transformers is not importable: {_TRANSFORMERS_IMPORT_ERROR}"
            print(f"[MLPromptDetector] {self.load_status.value}: {self.load_detail}")
            return

        self.device = self._select_device()

        # 3. Tokenizer (may require network access to the model hub).
        try:
            self.tokenizer = DistilBertTokenizer.from_pretrained(self.checkpoint)
        except Exception as e:
            self.tokenizer = None
            self.load_status = ModelLoadStatus.TOKENIZER_UNAVAILABLE
            self.load_detail = (
                f"Could not obtain the '{self.checkpoint}' tokenizer ({e}). The weights on disk are "
                "verified, but tokenization is unavailable - check model-hub network access or "
                "pre-populate the local transformers cache."
            )
            print(f"[MLPromptDetector] {self.load_status.value}: {self.load_detail}")
            return

        # 4. Architecture + verified state dict.
        try:
            self.model = AutoModelForSequenceClassification.from_pretrained(self.checkpoint, num_labels=2)
            state_dict = torch.load(self.model_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            self.model = None
            self.load_status = ModelLoadStatus.LOAD_ERROR
            self.load_detail = f"Failed to initialise the classifier from verified weights: {e}"
            print(f"[MLPromptDetector] {self.load_status.value}: {self.load_detail}")
            return

        self.load_status = ModelLoadStatus.LOADED_VERIFIED
        self.load_detail = (
            f"Verified production weights loaded from {self.model_path} "
            f"(sha256={self.model_sha256}, threshold={self.threshold:.2f}, max_len={self.max_len}) "
            f"on device {self.device}."
        )
        print(f"[MLPromptDetector] {self.load_status.value}: {self.load_detail}")

    # -- Inference ---------------------------------------------------------

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
