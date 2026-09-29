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
import re
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
from backend.attachments.handler import extract_attachment_text, AttachmentError
from backend.database.db import init_db, log_incident, get_all_incidents, get_security_stats
from backend.alerts.email_alert import send_security_email
from backend.alerts.sms_alert import send_security_sms
from backend.auth import init_admin_auth, verify_admin_credentials, require_admin_auth, ADMIN_USERNAME

# Initialize Flask
app = Flask(__name__, static_folder="../frontend/static")
CORS(app)

# Hard request-size ceiling (defense in depth ahead of attachment-specific
# validation): a little above the attachment size limit to allow for the
# rest of the multipart/form payload.
app.config["MAX_CONTENT_LENGTH"] = int(
    os.getenv("ATTACHMENT_MAX_BYTES", 5 * 1024 * 1024)
) + (1 * 1024 * 1024)

# Initialize Security & Database Engines
init_db()
init_admin_auth()
prompt_engine = PromptSecurityEngine()
response_engine = ResponseSecurityEngine()
llm_client = LLMClient()

# Fail-closed switch. When REQUIRE_ML is enabled, the API refuses to serve
# verdicts while the frozen ML classifier is unavailable, rather than silently
# degrading to rule-only scoring.
REQUIRE_ML = os.getenv("REQUIRE_ML", "0").strip().lower() in ("1", "true", "yes", "on")


def _ml_unavailable_response():
    """503 payload used when REQUIRE_ML is set and the classifier is degraded."""
    status = prompt_engine.model_status()
    return jsonify({
        "error": "ML detection layer unavailable; refusing to serve a degraded verdict.",
        "require_ml": True,
        "pipeline_mode": status["pipeline_mode"],
        "load_status": status["load_status"],
        "load_detail": status["load_detail"],
        "remediation": "Fetch the frozen production weights (git lfs install && git lfs pull), or unset REQUIRE_ML to allow rule-only operation."
    }), 503


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
    model_status = prompt_engine.model_status()
    return jsonify({
        "status": "ok",
        "service": "prompt-security-api",
        "ml_model_loaded": prompt_engine.ml_detector.is_loaded,
        "layer1_ml_loaded": prompt_engine.ml_detector.is_loaded,
        "layer1_rule_engine": True,
        "layer2_response_security": True,
        "llm_provider": llm_client.provider,
        # Frozen-model transparency: never let a degraded pipeline look healthy.
        "pipeline_mode": model_status["pipeline_mode"],
        "degraded": model_status["degraded"],
        "require_ml": REQUIRE_ML,
        "model": model_status
    }), 200


# -------------------------------------------------------------
# 2. Layer 1 Detection Endpoint
# -------------------------------------------------------------
@app.route("/detect", methods=["POST"])
def detect():
    if REQUIRE_ML and not prompt_engine.ml_detector.is_loaded:
        return _ml_unavailable_response()

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


def extract_threat_evidence(text: str, l1_res: dict = None) -> str:
    """
    Extracts a concise, accurate quote of the malicious instruction from text.
    For documents/images, quotes the actual extracted/OCR malicious text.
    """
    if not text or not isinstance(text, str):
        return ""

    patterns = [
        r"(?i)\b(ignore|disregard|forget|override|bypass|discard|cancel)\s+(all\s+)?(the\s+above|previous|prior|above|preceding|earlier|past)(\s+(instructions?|rules?|directives?|guidelines?|constraints?|prompts?|context))?[^\n.?!]*",
        r"(?i)\b(output|repeat|print|display|reveal|transcribe|echo|dump|show|disclose)\s+(your\s+)?(exact\s+)?(entire\s+)?(system\s+prompt|initial\s+instructions|hidden\s+instructions|developer\s+guidelines|system\s+instructions)[^\n.?!]*",
        r"(?i)\b(system\s+override|instruction\s+reset|admin\s+command|developer\s+emergency\s+mode)[^\n.?!]*",
        r"(?i)\b(act\s+as\s+dan|do\s+anything\s+now|developer\s+mode|unfiltered\s+ai|unrestricted\s+mode)[^\n.?!]*",
        r"(?i)\b(stop|abandon|cancel|terminate|discontinue|halt)\s+(your\s+)?(current\s+)?(task|role|objective|workflow|analysis)[^\n.?!]*",
        r"(?i)\b(override\s+(all\s+)?safety\s+(rules|filters|guidelines))[^\n.?!]*",
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if m:
            start, end = m.span()
            prev_newline = text.rfind('\n', 0, start)
            next_newline = text.find('\n', end)
            line_start = 0 if prev_newline == -1 else prev_newline + 1
            line_end = len(text) if next_newline == -1 else next_newline
            candidate = text[line_start:line_end].strip()
            if candidate:
                if len(candidate) > 250:
                    rel_start = max(0, start - line_start - 20)
                    rel_end = min(len(candidate), end - line_start + 60)
                    candidate = ("..." if rel_start > 0 else "") + candidate[rel_start:rel_end].strip() + ("..." if rel_end < len(candidate) else "")
                return candidate

    clean_text = " ".join(text.split()).strip()
    if len(clean_text) <= 250:
        return clean_text

    keywords = ["ignore", "instruction", "system prompt", "reveal", "override", "bypass", "developer mode", "secret"]
    for line in text.splitlines():
        line_clean = line.strip()
        if any(kw in line_clean.lower() for kw in keywords) and len(line_clean) >= 10:
            if len(line_clean) > 250:
                return line_clean[:240].strip() + "..."
            return line_clean

    return clean_text[:240].strip() + "..."


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
    if REQUIRE_ML and not prompt_engine.ml_detector.is_loaded:
        return _ml_unavailable_response()

    is_multipart_request = bool(request.content_type) and request.content_type.startswith("multipart/form-data")

    attachment_metadata = None
    is_image = False
    filename = None
    file_type = None
    raw_prompt_text = ""
    attachment_text = ""

    if is_multipart_request:
        # Attachment-capable path: prompt (optional) + at most one attachment
        # field. Existing JSON-only behavior (below) is untouched.
        raw_prompt_text = str(request.form.get("prompt", "")).strip()
        demo_layer2_leak_requested = str(request.form.get("demo_layer2_leak", "")).strip().lower() == "true"

        uploaded_file = request.files.get("attachment")
        if uploaded_file is not None and uploaded_file.filename:
            try:
                attachment_bytes = uploaded_file.read()
                attachment_text = extract_attachment_text(uploaded_file.filename, attachment_bytes)
                filename = uploaded_file.filename
                ext = os.path.splitext(filename)[1].lower().lstrip(".")
                is_image = ext in ("png", "jpg", "jpeg")
                file_type = ext.upper()
                attachment_metadata = {
                    "filename": filename,
                    "file_type": file_type,
                    "is_image": is_image,
                    "extracted_chars": len(attachment_text),
                    "extraction_status": "Success",
                    "analyzed": True
                }
            except AttachmentError as exc:
                return jsonify({"error": str(exc)}), 400

        if not raw_prompt_text and not attachment_text:
            return jsonify({"error": "Missing 'prompt' parameter or attachment."}), 400
    else:
        data = request.get_json(silent=True)
        if not data or "prompt" not in data:
            return jsonify({"error": "Missing 'prompt' parameter in JSON payload."}), 400

        raw_prompt_text = str(data.get("prompt", "")).strip()
        demo_layer2_leak_requested = bool(data.get("demo_layer2_leak") is True)

    client_ip = request.remote_addr or "127.0.0.1"

    # Deterministic Layer 2 demo path: requires BOTH an explicit, dedicated
    # request field (never the free-text prompt) AND the server being
    # explicitly configured to allow it. This is off by default.
    demo_layer2_leak_enabled = os.getenv("ENABLE_LAYER2_DEMO", "false").strip().lower() == "true"
    trigger_layer2_demo_leak = demo_layer2_leak_requested and demo_layer2_leak_enabled

    # =========================================================
    # STEP 1: LAYER 1 — PROMPT SECURITY WITH SEPARATE ATTRIBUTION
    # =========================================================
    # A. Analyze user prompt separately if provided
    prompt_l1 = None
    prompt_threat_detected = False
    if raw_prompt_text:
        prompt_l1 = prompt_engine.analyze_prompt(raw_prompt_text)
        prompt_threat_detected = (
            prompt_l1["decision"] == "BLOCK" or 
            prompt_l1["risk_level"] in ["CRITICAL", "HIGH"] or 
            prompt_l1.get("is_injection") is True
        )

    # B. Analyze extracted attachment content separately if provided
    att_l1 = None
    attachment_threat_detected = False
    if attachment_text:
        att_l1 = prompt_engine.analyze_prompt(attachment_text)
        attachment_threat_detected = (
            att_l1["decision"] == "BLOCK" or 
            att_l1["risk_level"] in ["CRITICAL", "HIGH"] or 
            att_l1.get("is_injection") is True
        )

    # C. Combined prompt analysis for overall gateway decision
    if raw_prompt_text and attachment_text:
        prompt_text = f"{raw_prompt_text}\n\n{attachment_text}".strip()
        l1_result = prompt_engine.analyze_prompt(prompt_text)
    elif raw_prompt_text:
        prompt_text = raw_prompt_text
        l1_result = prompt_l1
    else:
        prompt_text = attachment_text
        l1_result = att_l1

    is_overall_block = (
        l1_result["decision"] == "BLOCK" or 
        l1_result["risk_level"] in ["CRITICAL", "HIGH"] or 
        l1_result.get("is_injection") is True
    )

    # If overall blocked but neither individual component triggered, attribute to the higher risk component
    if is_overall_block and not prompt_threat_detected and not attachment_threat_detected:
        prompt_score = prompt_l1["risk_score"] if prompt_l1 else 0
        att_score = att_l1["risk_score"] if att_l1 else 0
        if att_score > prompt_score:
            attachment_threat_detected = True
        elif prompt_score > att_score:
            prompt_threat_detected = True
        else:
            prompt_threat_detected = bool(raw_prompt_text)
            attachment_threat_detected = bool(attachment_text)

    source_item_label = "Uploaded Image" if is_image else "Uploaded Document"

    prompt_evidence = None
    attachment_evidence = None
    if prompt_threat_detected:
        prompt_evidence = extract_threat_evidence(raw_prompt_text, prompt_l1)
    if attachment_threat_detected:
        attachment_evidence = extract_threat_evidence(attachment_text, att_l1)

    if prompt_threat_detected and attachment_threat_detected:
        threat_source_label = f"User Prompt & {source_item_label}"
        overall_attack_vector = "Direct & Indirect Prompt Injection"
        l1_result["attack_type"] = "Direct & Indirect Prompt Injection"
        l1_result["reason"] = f"Both the user prompt and {source_item_label.lower()} contain instruction overrides or adversarial directives."
    elif attachment_threat_detected:
        threat_source_label = source_item_label
        overall_attack_vector = "Indirect Prompt Injection"
        l1_result["attack_type"] = "Indirect Prompt Injection"
        l1_result["reason"] = f"The {source_item_label.lower()} contains an instruction attempting to override the AI's existing instructions."
    elif prompt_threat_detected:
        threat_source_label = "User Prompt"
        overall_attack_vector = "Direct Prompt Injection"
        l1_result["attack_type"] = "Direct Prompt Injection"
        l1_result["reason"] = "The user prompt directly attempts to override existing instructions and obtain protected system information."
    else:
        threat_source_label = "None"
        overall_attack_vector = "None detected"

    prompt_attack_type = "Direct Prompt Injection" if prompt_threat_detected else None
    attachment_attack_type = "Indirect Prompt Injection" if attachment_threat_detected else None

    threat_attribution = {
        "prompt_analyzed": bool(raw_prompt_text),
        "attachment_analyzed": bool(attachment_text),
        "prompt_threat_detected": prompt_threat_detected,
        "attachment_threat_detected": attachment_threat_detected,
        "prompt_attack_type": prompt_attack_type,
        "attachment_attack_type": attachment_attack_type,
        "prompt_evidence": prompt_evidence,
        "attachment_evidence": attachment_evidence,
        "source": threat_source_label,
        "threat_source": threat_source_label,
        "attack_vector": overall_attack_vector,
        "source_item_label": source_item_label if attachment_text else None
    }

    analysis_scope = {
        "prompt_analyzed": bool(raw_prompt_text),
        "attachment_analyzed": bool(attachment_text),
        "filename": filename,
        "file_type": file_type,
        "extraction_status": "Success" if attachment_text else "None",
        "extracted_chars": len(attachment_text) if attachment_text else 0,
        "is_image": is_image,
        "extraction_label": "OCR text analyzed" if is_image else "Extracted text analyzed",
        "prompt_threat_detected": prompt_threat_detected,
        "attachment_threat_detected": attachment_threat_detected,
        "prompt_attack_type": prompt_attack_type,
        "attachment_attack_type": attachment_attack_type,
        "prompt_evidence": prompt_evidence,
        "attachment_evidence": attachment_evidence,
        "threat_source": threat_source_label,
        "attack_vector": overall_attack_vector,
    }

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
            },
            "attachment_metadata": attachment_metadata,
            "analysis_scope": analysis_scope,
            "threat_attribution": threat_attribution
        }), 200

    # =========================================================
    # STEP 3: LLM GENERATION (SAFE / ALLOWED PATH)
    # =========================================================
    llm_output = llm_client.generate_response(
        prompt_text,
        trigger_layer2_demo_leak=trigger_layer2_demo_leak
    )

    if llm_output.get("status") == "error":
        import uuid
        req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        internal_error_detail = llm_output.get("error", "unknown error")
        generic_error_message = "LLM provider request failed"
        print(f"[LLM PROVIDER ERROR] request_id={req_id} detail={internal_error_detail}")
        log_incident(
            prompt=prompt_text, risk_score=risk_score, risk_level=risk_level,
            attack_type=attack_type, layer1_decision=l1_decision,
            layer2_decision="NOT_EXECUTED", final_decision="ERROR",
            reason=f"LLM provider error: {internal_error_detail}",
            alert_status="SKIPPED", client_ip=client_ip,
            email_status="SKIPPED", sms_status="SKIPPED", request_id=req_id
        )
        return jsonify({
            "request_id": req_id, "llm_called": True, "final_decision": "ERROR",
            "response": f"[{generic_error_message}]", "layer1": l1_result,
            "layer2": {"status":"NOT_EXECUTED","decision":"NOT_EXECUTED","is_safe":False,
                       "reason":"LLM provider call failed before a response was generated.",
                       "risk_level":"N/A","risk_score":0.0,
                       "leakage_details":{"findings":[],"leakage_detected":False,"leakage_score":0.0,
                                          "reason":"LLM provider call failed before a response was generated."}},
            "llm_metadata":{"provider":llm_output.get("provider"),"model":llm_output.get("model"),
                            "latency_ms":llm_output.get("latency_ms"),"status":"error","error":generic_error_message},
            "alert_status":"SKIPPED","email_status":"SKIPPED","sms_status":"SKIPPED",
            "sensitive_resource_locked":False
        }), 502

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
        "sensitive_resource_locked": False,
        "attachment_metadata": attachment_metadata,
        "analysis_scope": analysis_scope,
        "threat_attribution": threat_attribution
    }), 200


# -------------------------------------------------------------
# 4. Incident Analytics & User Status API
# -------------------------------------------------------------
@app.route("/api/incidents", methods=["GET"])
@require_admin_auth
def api_incidents():
    incidents = get_all_incidents(limit=50)
    return jsonify(incidents), 200


@app.route("/api/stats", methods=["GET"])
@require_admin_auth
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
    username = data.get("username", ADMIN_USERNAME).strip()
    password = data.get("password", "").strip()

    if verify_admin_credentials(username, password):
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
    _status = prompt_engine.model_status()
    print(f"[*] Layer 1 ML Status: {_status['load_status']} | Pipeline Mode: {_status['pipeline_mode']}")
    if _status["degraded"]:
        print(f"[!] DEGRADED: {_status['load_detail']}")
        print(f"[!] Verdicts are rule-only. Set REQUIRE_ML=1 to refuse service instead.")
    print(f"[*] Layer 2 Response Security: ACTIVE")
    print(f"[*] Web Interface Available at: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)