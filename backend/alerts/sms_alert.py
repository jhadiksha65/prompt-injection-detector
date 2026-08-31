"""
sms_alert.py
SMS Alert notification module supporting Twilio or transparent Mock SMS logging.
"""

import os

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


def send_security_sms(request_id: str, risk_level: str, attack_type: str) -> str:
    """
    Dispatches SMS alert via Twilio if credentials are set; otherwise logs a simulated SMS notification.
    Returns: "SENT", "FAILED", or "NOT_CONFIGURED".
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_FROM_PHONE")
    to_phone = os.getenv("ALERT_PHONE_NUMBER", "+1234567890")

    message_body = f"[ALERT] {risk_level} Security Incident {request_id}: {attack_type} blocked by Dual-Layer Middleware."

    if account_sid and auth_token and from_phone:
        try:
            # Twilio integration check - clean non-digits except leading '+' to enforce E.164 format
            clean_to = "+" + "".join(c for c in to_phone if c.isdigit()) if to_phone.startswith("+") else "".join(c for c in to_phone if c.isdigit())
            clean_from = "+" + "".join(c for c in from_phone if c.isdigit()) if from_phone.startswith("+") else "".join(c for c in from_phone if c.isdigit())
            
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message_body,
                from_=clean_from,
                to=clean_to
            )
            return "SENT"
        except Exception as e:
            print(f"[SMSAlert] Failed to send real SMS ({e}).")
            return "FAILED"
    else:
        # Mock SMS for offline demonstration
        print(f"[SMS ALERT SIMULATED] -> To: {to_phone} | Msg: {message_body}")
        return "NOT_CONFIGURED"
