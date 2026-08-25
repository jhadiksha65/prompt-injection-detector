"""
app.py
Flask Central Security API for Prompt Injection Detection.
Provides /health check and /detect endpoints for the browser extension and downstream consumers.
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add root directory to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.prompt_security.decision_engine import PromptSecurityEngine

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome Extension & external clients

# Initialize Security Detection Engine
engine = PromptSecurityEngine()


# -------------------------------------------------------------
# 1. Health Check Endpoint
# -------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint verifying that the security API is active
    and reporting detection engine readiness.
    """
    return jsonify({
        "status": "ok",
        "service": "prompt-security-api",
        "ml_model_loaded": engine.ml_detector.is_loaded,
        "rule_engine_loaded": True
    }), 200


# -------------------------------------------------------------
# 2. Prompt Detection Endpoint
# -------------------------------------------------------------
@app.route("/detect", methods=["POST"])
def detect():
    """
    Analyzes a prompt using hybrid rule-based and ML detection.
    Accepts JSON: {"prompt": "..."}
    Returns structured security decision, risk score, and attack classification.
    """
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({
            "error": "Invalid request payload. Expected JSON with 'prompt' key.",
            "is_injection": False,
            "decision": "ALLOW",
            "risk_score": 0.0,
            "risk_level": "LOW"
        }), 400

    prompt_text = data.get("prompt", "")
    if not isinstance(prompt_text, str):
        prompt_text = str(prompt_text)

    # Execute prompt analysis
    result = engine.analyze_prompt(prompt_text)
    return jsonify(result), 200


# -------------------------------------------------------------
# Main Execution Entry Point
# -------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting Prompt Injection Security API on port {port}...")
    print(f"[*] ML Detector Status: {'READY' if engine.ml_detector.is_loaded else 'NOT LOADED'}")
    app.run(host="0.0.0.0", port=port, debug=False)