"""
ml_detector.py
Inference wrapper for the trained Machine Learning Prompt Injection Classifier.
Loads serialized vectorizer and classifier artifacts and provides calibrated probability estimation.
"""

import os
import joblib
from typing import Dict, Any, Optional
import sys

from .threat_taxonomy import ThreatCategory

# Add root directory to sys.path if needed for text preprocessing
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ml.preprocessing.preprocessing import TextPreprocessor


class MLPromptDetector:
    """
    Loads trained ML model artifacts and computes the probability of malicious prompt injection.
    """

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        
        self.models_dir = os.path.abspath(models_dir)
        self.vectorizer_path = os.path.join(self.models_dir, "vectorizer.joblib")
        self.classifier_path = os.path.join(self.models_dir, "classifier.joblib")
        self.vectorizer = None
        self.classifier = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        """Loads vectorizer and classifier from disk if available."""
        if os.path.exists(self.vectorizer_path) and os.path.exists(self.classifier_path):
            try:
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.classifier = joblib.load(self.classifier_path)
                self.is_loaded = True
            except Exception as e:
                print(f"[MLPromptDetector] Error loading model: {e}")
                self.is_loaded = False
        else:
            self.is_loaded = False

    def predict_probability(self, prompt: str) -> Dict[str, Any]:
        """
        Computes the calibrated malicious probability for a prompt.
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
            # Fallback if model is not yet trained/loaded
            return {
                "ml_available": False,
                "malicious_probability": 0.0,
                "ml_score": 0.0,
                "is_malicious": False,
                "confidence": 0.0
            }

        cleaned_text = TextPreprocessor.clean_text(prompt)
        features = self.vectorizer.transform([cleaned_text])
        probabilities = self.classifier.predict_proba(features)[0]
        malicious_prob = float(probabilities[1])
        ml_score = round(malicious_prob * 100.0, 2)

        return {
            "ml_available": True,
            "malicious_probability": round(malicious_prob, 4),
            "ml_score": ml_score,
            "is_malicious": malicious_prob >= 0.50,
            "confidence": round(float(max(probabilities)), 4)
        }
