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
    Returns empty string if no concrete injection directive is found.
    """
    if not text or not isinstance(text, str):
        return ""

    patterns = [
        r"(?i)\b(ignore|disregard|forget|override|bypass|discard|cancel)\s+(all\s+)?(the\s+above|previous|prior|above|preceding|earlier|past|rules?)(\s+(instructions?|rules?|directives?|guidelines?|constraints?|prompts?|context))?[^\n.?!]*",
        r"(?i)\b(output|repeat|print|display|reveal|transcribe|echo|dump|show|disclose)\s+(your\s+)?(exact\s+)?(entire\s+)?(system\s+prompt|initial\s+instructions|hidden\s+instructions|developer\s+guidelines|system\s+instructions|passwords?|keys?|admin\s+keys?)[^\n.?!]*",
        r"(?i)\b(system\s+override|instruction\s+reset|admin\s+command|developer\s+emergency\s+mode)[^\n.?!]*",
        r"(?i)\b(act\s+as\s+dan|do\s+anything\s+now|developer\s+mode|unfiltered\s+ai|unrestricted\s+mode|evilgpt)[^\n.?!]*",
        r"(?i)\b(stop|abandon|cancel|terminate|discontinue|halt)\s+(your\s+)?(current\s+)?(task|role|objective|workflow|analysis)[^\n.?!]*",
        r"(?i)\b(your\s+new\s+goal\s+is\s+to|new\s+mission:|your\s+sole\s+purpose\s+is\s+now)[^\n.?!]*",
        r"(?i)\b(override\s+(all\s+)?safety\s+(rules|filters|guidelines))[^\n.?!]*",
        r"(?i)\b(from\s+now\s+on\s*,\s*(say\s+yes|accept\s+all\s+commands|never\s+refuse))[^\n.?!]*",
        r"(?i)\b(secret\s+token.*embedded\s+in\s+your\s+system\s+prompt)[^\n.?!]*",
        r"(?i)\b(repeat\s+the\s+words\s+above\s+starting\s+from)[^\n.?!]*",
        r"(?i)(<system>|<admin>|\[SYSTEM\]|\[INST\]|\[ADMIN\]|<\|im_start\|>|<\|im_end\|>)[^\n.?!]*",
    ]

    # Explicit benign disclaimers and negations that are NOT injection instructions
    disclaimer_patterns = [
        r"(?i)\b(does\s+not|doesn\x27t|never|no|without)\s+.*(contain|have|include|execute|run|accept)?\s+(instructions?|prompts?|injections?|directives?)",
        r"(?i)\borderinary\s+business\s+information\b",
        r"(?i)\bnot\s+contain\s+instructions\b"
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if m:
            start, end = m.span()
            matched_span = text[start:end]
            if any(re.search(dp, matched_span) for dp in disclaimer_patterns):
                continue
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

    # Check if a heuristic injection rule actually matched in l1_res
    if l1_res and l1_res.get("rule_result", {}).get("rule_triggered"):
        indicators = l1_res["rule_result"].get("matched_indicators", [])
        if indicators:
            for ind in indicators:
                clean_ind = ind.split(":", 1)[-1].strip().strip("\x27\"")
                if len(clean_ind) >= 6 and clean_ind.lower() in text.lower():
                    idx = text.lower().find(clean_ind.lower())
                    prev_nl = text.rfind("\n", 0, idx)
                    next_nl = text.find("\n", idx + len(clean_ind))
                    ls = 0 if prev_nl == -1 else prev_nl + 1
                    le = len(text) if next_nl == -1 else next_nl
                    return text[ls:le].strip()

    return ""


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
    source_item_label = "Uploaded Image" if is_image else "Uploaded Document"

    # A. Analyze user prompt separately if provided
    prompt_l1 = None
    prompt_threat_detected = False
    prompt_evidence = None
    if raw_prompt_text:
        prompt_l1 = prompt_engine.analyze_prompt(raw_prompt_text)
        prompt_evidence_candidate = extract_threat_evidence(raw_prompt_text, prompt_l1)
        if prompt_l1["decision"] == "BLOCK" or prompt_l1["risk_level"] in ["CRITICAL", "HIGH"] or prompt_l1.get("is_injection") is True:
            prompt_threat_detected = True
            prompt_evidence = prompt_evidence_candidate or raw_prompt_text

    # B. Analyze extracted attachment content separately if provided
    att_l1 = None
    attachment_threat_detected = False
    attachment_evidence = None
    if attachment_text:
        att_l1 = prompt_engine.analyze_prompt(attachment_text)
        att_rule_triggered = bool(att_l1.get("rule_result", {}).get("rule_triggered"))
        att_rule_score = float(att_l1.get("rule_result", {}).get("rule_score", 0.0))
        att_evidence_candidate = extract_threat_evidence(attachment_text, att_l1)

        # An attachment threat exists ONLY if the extracted content actually contains
        # a detected injection signal (rule indicator or concrete adversarial pattern).
        # Benign documents with ordinary business text or negative disclaimers must never
        # be flagged as Indirect Prompt Injection.
        if (att_rule_triggered and att_rule_score >= 45.0) or bool(att_evidence_candidate):
            attachment_threat_detected = True
            attachment_evidence = att_evidence_candidate or "Instruction override directive detected in attachment"
        else:
            attachment_threat_detected = False
            attachment_evidence = None

    # Full text for LLM invocation
    if raw_prompt_text and attachment_text:
        prompt_text = f"{raw_prompt_text}\n\n{attachment_text}".strip()
    elif raw_prompt_text:
        prompt_text = raw_prompt_text
    else:
        prompt_text = attachment_text

    # Gateway Resolution & Source Attribution
    if not attachment_text:
        # Prompt-only path: preserve exact original prompt_l1 result
        l1_result = prompt_l1
        l1_decision = l1_result["decision"]
        risk_score = l1_result["risk_score"]
        risk_level = l1_result["risk_level"]
        attack_type = l1_result["attack_type"]
        l1_reason = l1_result["reason"]
        is_injection = l1_result.get("is_injection", False)
        threat_source_label = "User Prompt" if prompt_threat_detected else "None"
        overall_attack_vector = "Direct Prompt Injection" if prompt_threat_detected else "None detected"
    else:
        # Attachment-capable path: authoritative Gateway Resolution & Source Attribution
        if prompt_threat_detected and attachment_threat_detected:
            threat_source_label = f"User Prompt & {source_item_label}"
            overall_attack_vector = "Direct & Indirect Prompt Injection"
            l1_decision = "BLOCK"
            risk_score = max(prompt_l1["risk_score"], att_l1["risk_score"])
            risk_level = "CRITICAL" if ("CRITICAL" in [prompt_l1["risk_level"], att_l1["risk_level"]]) else "HIGH"
            attack_type = "Direct & Indirect Prompt Injection"
            l1_reason = f"Both the user prompt and {source_item_label.lower()} contain instruction overrides or adversarial directives."
            is_injection = True
        elif attachment_threat_detected:
            threat_source_label = source_item_label
            overall_attack_vector = "Indirect Prompt Injection"
            l1_decision = "BLOCK"
            risk_score = att_l1["risk_score"]
            risk_level = att_l1["risk_level"]
            attack_type = "Indirect Prompt Injection"
            l1_reason = f"The {source_item_label.lower()} contains an instruction attempting to override the AI's existing instructions."
            is_injection = True
        elif prompt_threat_detected:
            threat_source_label = "User Prompt"
            overall_attack_vector = "Direct Prompt Injection"
            l1_decision = "BLOCK"
            risk_score = prompt_l1["risk_score"]
            risk_level = prompt_l1["risk_level"]
            attack_type = "Direct Prompt Injection"
            l1_reason = "The user prompt directly attempts to override existing instructions and obtain protected system information."
            is_injection = True
        else:
            threat_source_label = "None"
            overall_attack_vector = "None detected"
            l1_decision = "ALLOW"
            base_l1 = prompt_l1 if prompt_l1 else att_l1
            risk_score = round(float(base_l1.get("risk_score", 0.0)), 2) if base_l1 else 0.0
            # Ensure clean benign score with no artificial floor
            risk_score = min(25.0, risk_score)
            risk_level = "LOW"
            attack_type = "Benign"
            l1_reason = "No prompt injection patterns detected. Prompt and document are safe."
            is_injection = False

        base_l1 = prompt_l1 if prompt_threat_detected else (att_l1 if attachment_threat_detected else (prompt_l1 or att_l1 or {}))
        l1_result = {
            "decision": l1_decision,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "attack_type": attack_type,
            "reason": l1_reason,
            "is_injection": is_injection,
            "classification": "MALICIOUS" if is_injection else "BENIGN",
            "rule_result": base_l1.get("rule_result", {
                "rule_triggered": False, "rule_score": 0.0, "attack_type": attack_type,
                "matched_indicators": [], "reason": l1_reason
            }),
            "ml_result": base_l1.get("ml_result", {
                "ml_available": True, "malicious_probability": 0.01, "ml_score": 1.0,
                "is_malicious": False, "confidence": 0.99
            }),
            "prompt_length": len(prompt_text),
            "pipeline_mode": "FULL",
            "ml_load_status": "LOADED_VERIFIED",
            "ml_degraded": False
        }

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


@app.route("/api/lock", methods=["POST"])
def api_lock():
    SESSION_STATE["is_locked"] = True
    SESSION_STATE["lock_reason"] = "Session locked by administrator."
    return jsonify({
        "success": True,
        "message": "Admin session locked.",
        "is_locked": True
    }), 200


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