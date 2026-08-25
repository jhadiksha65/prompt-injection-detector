"""
email_alert.py
Automated email notification dispatcher for HIGH and CRITICAL security incidents.
Supports configured SMTP servers or transparent simulated dispatch for offline demonstrations.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any


def send_security_email(
    request_id: str,
    risk_score: float,
    risk_level: str,
    attack_type: str,
    action_taken: str,
    reason: str,
    prompt_snippet: str
) -> str:
    """
    Sends a security alert email or logs a simulated alert.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("ALERT_EMAIL_RECIPIENT", "security-admin@enterprise.local")

    subject = f"[{risk_level}] Prompt Security Alert: {attack_type} ({request_id})"

    body = f"""
=====================================================
PROMPT INJECTION SECURITY ALERT
=====================================================
Incident ID:     {request_id}
Threat Level:    {risk_level} (Risk Score: {risk_score}/100)
Attack Vector:   {attack_type}
Action Taken:    {action_taken}
Explanation:     {reason}

Captured Context:
"{prompt_snippet}"

System Status:
- Layer 1 Execution: Intercepted & Evaluated
- Response Action: {action_taken}
- Sensitive Resource: Access Locked (Re-authentication required)
=====================================================
    """

    is_valid_config = (
        smtp_host and 
        smtp_user and 
        smtp_pass and 
        "your_email" not in smtp_user and 
        "your_16" not in smtp_pass
    )

    if is_valid_config:
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(smtp_host, smtp_port, timeout=5)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipient, msg.as_string())
            server.quit()
            return "EMAIL_SENT"
        except Exception as e:
            print(f"[EmailAlert] Failed to send real email ({e}). Defaulting to simulation.")
            return "SIMULATION_FALLBACK"
    else:
        # Simulated alert for offline demonstration
        print(f"\n[ALERT DISPATCHED] -> To: {recipient} | Subject: {subject}")
        return "SIMULATED_EMAIL"
