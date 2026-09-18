"""
app.py
Central Security API & Dual-Layer Middleware for Web-Based and API-Based LLM Applications.

Provides:
- GET  /health           : Health & module readiness check
- POST /detect           : Layer 1 prompt injection threat analysis
- POST /secure-prompt    : Full end-to-end Dual-Layer Security Middleware
- GET  /api/incidents    : Incident logs for Security Dashboard
- GET  /api/stats        : Aggregated security metrics & KPIs
- GET  /api/user-status  : Session security lock state
- POST /api/unlock       : Re-authentication challenge handler
- Frontend routes        : Web UI for Assistant, Dashboard, and Sensitive Resource
"""

import os
import sys
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS

# Add root directory to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Automatically load .env file if present
def load_env():
    env_path = os.path.join(ROOT_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    os.environ[key.strip()] = val

load_env()

# Import Security Modules
from backend.prompt_security.decision_engine import PromptSecurityEngine
from backend.response_security.decision_engine import ResponseSecurityEngine
from backend.llm.client import LLMClient
from backend.database.db import init_db, log_incident, get_all_incidents, get_security_stats
from backend.alerts.email_alert import send_security_email
from backend.alerts.sms_alert import send_security_sms

# Initialize Flask
app = Flask(__name__, static_folder="../frontend/static")
CORS(app)

# Initialize Security & Database Engines
init_db()
prompt_engine = PromptSecurityEngine()
response_engine = ResponseSecurityEngine()
llm_client = LLMClient()

# Global session security state (for demo lockout)
SESSION_STATE = {
    "is_locked": False,
    "lock_reason": None,
    "last_critical_id": None
}


# -------------------------------------------------------------
# 1. Health Check Endpoint
# -------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "prompt-security-api",
        "ml_model_loaded": prompt_engine.ml_detector.is_loaded,
        "layer1_ml_loaded": prompt_engine.ml_detector.is_loaded,
        "layer1_rule_engine": True,
        "layer2_response_security": True,
        "llm_provider": llm_client.provider
    }), 200


# -------------------------------------------------------------
# 2. Layer 1 Detection Endpoint
# -------------------------------------------------------------
@app.route("/detect", methods=["POST"])
def detect():
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({"error": "Missing 'prompt' parameter in JSON payload."}), 400

    prompt_text = str(data.get("prompt", "")).strip()
    result = prompt_engine.analyze_prompt(prompt_text)
    client_ip = request.remote_addr or "127.0.0.1"

    email_status = "SKIPPED"
    sms_status = "SKIPPED"
    recipient_email = os.getenv("ALERT_EMAIL_RECIPIENT", "account-holder@example.com")
    recipient_phone = os.getenv("ALERT_PHONE_NUMBER", "+91-XXXXXXXXXX")
    req_id = "SCAN"

    risk_level = result.get("risk_level", "LOW")
    is_critical = (risk_level == "CRITICAL")
    is_blocked = (result.get("decision") == "BLOCK" or risk_level in ["CRITICAL", "HIGH"])

    if is_blocked:
        import uuid
        req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        # Lock sensitive resource only on CRITICAL attack
        if is_critical:
            SESSION_STATE["is_locked"] = True
            SESSION_STATE["lock_reason"] = f"{result.get('attack_type')} detected via browser extension."
            SESSION_STATE["last_critical_id"] = req_id

        # Dispatch automated Email & SMS alerts
        email_status = send_security_email(
            request_id=req_id,
            risk_score=result.get("risk_score", 0),
            risk_level=risk_level,
            attack_type=result.get("attack_type", "Prompt Injection"),
            action_taken="PROMPT_BLOCKED_ON_CHATGPT",
            reason=result.get("reason", "Heuristic override detected"),
            prompt_snippet=prompt_text,
            layer1_status="BLOCKED",
            llm_called="NO",
            layer2_status="NOT_EXECUTED",
            leakage_detected="FALSE",
            leakage_score="N/A",
            final_decision="BLOCKED"
        )
        sms_status = send_security_sms(
            request_id=req_id,
            risk_level=risk_level,
            attack_type=result.get("attack_type", "Prompt Injection")
        )

        # Log incident in SQLite database
        log_incident(
            prompt=prompt_text,
            risk_score=result.get("risk_score", 0),
            risk_level=risk_level,
            attack_type=result.get("attack_type", "Prompt Injection"),
            layer1_decision="BLOCK",
            layer2_decision="N/A",
            final_decision="BLOCK",
            reason=result.get("reason", ""),
            alert_status=email_status,
            client_ip=client_ip,
            email_status=email_status,
            sms_status=sms_status,
            request_id=req_id
        )

    result["request_id"] = req_id
    result["alert_status"] = email_status
    result["email_status"] = email_status
    result["sms_status"] = sms_status
    result["alert_recipient_email"] = recipient_email
    result["alert_recipient_phone"] = recipient_phone
    return jsonify(result), 200


# -------------------------------------------------------------
# 3. Main Dual-Layer Security Middleware Endpoint
# -------------------------------------------------------------
@app.route("/secure-prompt", methods=["POST"])
def secure_prompt():
    """
    Main End-to-End Dual-Layer Security Middleware:
    1. Layer 1: Prompt Security Analysis
    2. Decision Gateway: If BLOCK -> Terminate, do NOT call LLM, log & alert.
    3. LLM Execution: Generate response if safe.
    4. Layer 2: Response Security Validation & Leakage Detection.
    5. Output Gateway: Return sanitized safe output.
    """
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({"error": "Missing 'prompt' parameter in JSON payload."}), 400

    prompt_text = str(data.get("prompt", "")).strip()
    client_ip = request.remote_addr or "127.0.0.1"

    # =========================================================
    # STEP 1: LAYER 1 — PROMPT SECURITY
    # =========================================================
    l1_result = prompt_engine.analyze_prompt(prompt_text)
    l1_decision = l1_result["decision"]
    risk_score = l1_result["risk_score"]
    risk_level = l1_result["risk_level"]
    attack_type = l1_result["attack_type"]
    l1_reason = l1_result["reason"]

    # =========================================================
    # STEP 2: GATEWAY DECISION (BLOCK PATH)
    # =========================================================
    if l1_decision == "BLOCK" or risk_level in ["CRITICAL", "HIGH"]:
        import uuid
        req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        is_critical = (risk_level == "CRITICAL")

        # Lock sensitive resource ONLY on critical attack
        if is_critical:
            SESSION_STATE["is_locked"] = True
            SESSION_STATE["lock_reason"] = f"{attack_type} detected with {risk_score}% critical threat risk."
            SESSION_STATE["last_critical_id"] = req_id

        # Trigger Alerts
        email_status = send_security_email(
            request_id=req_id,
            risk_score=risk_score,
            risk_level=risk_level,
            attack_type=attack_type,
            action_taken="PROMPT_BLOCKED_LLM_NOT_CALLED",
            reason=l1_reason,
            prompt_snippet=prompt_text,
            layer1_status="BLOCKED",
            llm_called="NO",
            layer2_status="NOT_EXECUTED",
            leakage_detected="FALSE",
            leakage_score="N/A",
            final_decision="BLOCKED"
        )
        sms_status = send_security_sms(request_id=req_id, risk_level=risk_level, attack_type=attack_type)

        # Log Incident
        log_incident(
            prompt=prompt_text,
            risk_score=risk_score,
            risk_level=risk_level,
            attack_type=attack_type,
            layer1_decision="BLOCK",
            layer2_decision="BYPASSED_DUE_TO_BLOCK",
            final_decision="BLOCK",
            reason=l1_reason,
            alert_status=email_status,
            client_ip=client_ip,
            email_status=email_status,
            sms_status=sms_status,
            request_id=req_id
        )

        return jsonify({
            "request_id": req_id,
            "llm_called": False,
            "final_decision": "BLOCK",
            "response": f"[SECURITY BLOCKED: {attack_type} detected ({risk_level} risk: {risk_score}%). The prompt was not sent to the LLM.]",
            "layer1": l1_result,
            "layer2": {
                "status": "BYPASSED_DUE_TO_BLOCK",
                "decision": "NOT_EXECUTED",
                "is_safe": False,
                "reason": "Layer 1 blocked the request before LLM generation.",
                "risk_level": "N/A",
                "risk_score": 0.0,
                "leakage_details": {
                    "findings": [],
                    "leakage_detected": False,
                    "leakage_score": 0.0,
                    "reason": "Layer 1 blocked the request before LLM generation."
                }
            },
            "alert_status": email_status,
            "email_status": email_status,
            "sms_status": sms_status,
            "sensitive_resource_locked": is_critical,
            "requires_reauth": is_critical,
            "threat_details": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "attack_type": attack_type,
                "reason": l1_reason,
                "alert_dispatched": email_status == "SENT",
                "lock_status": "LOCKED" if is_critical else "ACTIVE"
            }
        }), 200

    # =========================================================
    # STEP 3: LLM GENERATION (SAFE / ALLOWED PATH)
    # =========================================================
    llm_output = llm_client.generate_response(prompt_text)
    raw_response = llm_output.get("raw_response", "")

    # =========================================================
    # STEP 4: LAYER 2 — RESPONSE SECURITY & LEAKAGE VALIDATION
    # =========================================================
    l2_result = response_engine.process_response(raw_response)
    l2_decision = l2_result["decision"]
    final_response = l2_result["sanitized_response"]

    # If Layer 2 detected critical leakage, dispatch alert
    email_status = "SKIPPED"
    sms_status = "SKIPPED"
    import uuid
    req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

    if l2_decision in ["BLOCK", "MASK"]:
        email_status = send_security_email(
            request_id=req_id,
            risk_score=l2_result["risk_score"],
            risk_level=l2_result["risk_level"],
            attack_type="System Leakage / Confidential Disclosure",
            action_taken=f"RESPONSE_{l2_decision}",
            reason=l2_result["reason"],
            prompt_snippet=prompt_text,
            layer1_status="ALLOWED",
            llm_called="YES",
            layer2_status=l2_decision,
            leakage_detected="TRUE",
            leakage_score=str(l2_result["risk_score"]),
            final_decision="BLOCKED" if l2_decision == "BLOCK" else "SANITIZED"
        )
        sms_status = send_security_sms(
            request_id=req_id,
            risk_level=l2_result["risk_level"],
            attack_type="System Leakage / Confidential Disclosure"
        )

    # Log Incident
    log_incident(
        prompt=prompt_text,
        risk_score=risk_score,
        risk_level=risk_level,
        attack_type=attack_type,
        layer1_decision=l1_decision,
        layer2_decision=l2_decision,
        final_decision=l2_decision if l2_decision != "SAFE" else ("WARNING" if (l1_decision == "WARNING" or risk_level == "MEDIUM") else "ALLOW"),
        reason=l2_result["reason"] if l2_decision != "SAFE" else l1_result["reason"],
        alert_status=email_status,
        client_ip=client_ip,
        email_status=email_status,
        sms_status=sms_status,
        request_id=req_id
    )

    overall_final_decision = l2_decision if l2_decision != "SAFE" else ("WARNING" if (l1_decision == "WARNING" or risk_level == "MEDIUM") else "ALLOW")

    return jsonify({
        "request_id": req_id,
        "llm_called": True,
        "final_decision": overall_final_decision,
        "response": final_response,
        "layer1": l1_result,
        "layer2": l2_result,
        "llm_metadata": {
            "provider": llm_output.get("provider"),
            "model": llm_output.get("model"),
            "latency_ms": llm_output.get("latency_ms")
        },
        "alert_status": email_status,
        "email_status": email_status,
        "sms_status": sms_status,
        "sensitive_resource_locked": False
    }), 200


# -------------------------------------------------------------
# 4. Incident Analytics & User Status API
# -------------------------------------------------------------
@app.route("/api/incidents", methods=["GET"])
def api_incidents():
    incidents = get_all_incidents(limit=50)
    return jsonify(incidents), 200


@app.route("/api/stats", methods=["GET"])
def api_stats():
    stats = get_security_stats()
    return jsonify(stats), 200


@app.route("/api/user-status", methods=["GET"])
def api_user_status():
    return jsonify({
        "is_locked": SESSION_STATE["is_locked"],
        "lock_reason": SESSION_STATE["lock_reason"],
        "last_critical_id": SESSION_STATE["last_critical_id"]
    }), 200


@app.route("/api/unlock", methods=["POST"])
@app.route("/api/reauth", methods=["POST"])
def api_unlock():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "admin").strip()
    password = data.get("password", "").strip()

    # Check password (default: admin123)
    salt = "prompt_sentinel_salt"
    entered_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    expected_hash = hashlib.sha256((salt + "admin123").encode("utf-8")).hexdigest()

    if entered_hash == expected_hash:
        SESSION_STATE["is_locked"] = False
        SESSION_STATE["lock_reason"] = None
        return jsonify({
            "success": True,
            "message": f"Identity verified for user '{username}'. Session unlocked.",
            "is_locked": False
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "Authentication failed: Invalid credentials provided.",
            "is_locked": True
        }), 401


# -------------------------------------------------------------
# 5. Web UI Routes (Assistant, Dashboard, Sensitive Resource)
# -------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    with open(os.path.join(ROOT_DIR, "frontend", "index.html"), "r", encoding="utf-8") as f:
        return render_template_string(f.read())


@app.route("/dashboard", methods=["GET"])
def dashboard():
    with open(os.path.join(ROOT_DIR, "frontend", "dashboard.html"), "r", encoding="utf-8") as f:
        return render_template_string(f.read())


@app.route("/sensitive-resource", methods=["GET"])
def sensitive_resource():
    with open(os.path.join(ROOT_DIR, "frontend", "sensitive_resource.html"), "r", encoding="utf-8") as f:
        return render_template_string(f.read())


# -------------------------------------------------------------
# Main Execution
# -------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting Dual-Layer Prompt Security API on port {port}...")
    print(f"[*] Layer 1 ML Status: {'READY' if prompt_engine.ml_detector.is_loaded else 'NOT LOADED'}")
    print(f"[*] Layer 2 Response Security: ACTIVE")
    print(f"[*] Web Interface Available at: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)