"""
email_alert.py
Automated email notification dispatcher for HIGH and CRITICAL security incidents.
Supports configured SMTP servers or transparent simulated dispatch for offline demonstrations.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Robust .env loader
def load_env():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while current_dir and current_dir != "/":
        env_path = os.path.join(current_dir, ".env")
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
            break
        current_dir = os.path.dirname(current_dir)

load_env()


def send_security_email(
    request_id: str,
    risk_score: float,
    risk_level: str,
    attack_type: str,
    action_taken: str,
    reason: str,
    prompt_snippet: str,
    layer1_status: str = "BLOCKED",
    llm_called: str = "NO",
    layer2_status: str = "NOT_EXECUTED",
    leakage_detected: str = "FALSE",
    leakage_score: str = "N/A",
    final_decision: str = "BLOCKED"
) -> str:
    """
    Sends a security alert email or logs a simulated alert.
    Returns: "SENT", "FAILED", or "NOT_CONFIGURED".
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587)) if os.getenv("SMTP_PORT") else 587
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
- Layer 1:         {layer1_status}
- LLM Called:       {llm_called}
- Layer 2:         {layer2_status}
- Leakage Detected: {leakage_detected}
- Leakage Score:    {leakage_score}
- Final Decision:   {final_decision}
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

            # Connect using SSL (port 465) or standard TLS (other ports)
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
                
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipient, msg.as_string())
            server.quit()
            return "SENT"
        except Exception as e:
            print(f"[EmailAlert] Failed to send real email ({e}).")
            return "FAILED"
    else:
        # Simulated alert for offline demonstration
        print(f"\n[ALERT SIMULATED] -> To: {recipient} | Subject: {subject}")
        return "NOT_CONFIGURED"
