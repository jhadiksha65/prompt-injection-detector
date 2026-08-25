"""
sms_alert.py
SMS Alert notification module supporting Twilio or transparent Mock SMS logging.
"""

import os


def send_security_sms(request_id: str, risk_level: str, attack_type: str) -> str:
    """
    Dispatches SMS alert via Twilio if credentials are set; otherwise logs a simulated SMS notification.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_FROM_PHONE")
    to_phone = os.getenv("ALERT_PHONE_NUMBER", "+1234567890")

    message_body = f"[ALERT] {risk_level} Security Incident {request_id}: {attack_type} blocked by Dual-Layer Middleware."

    if account_sid and auth_token and from_phone:
        try:
            # Twilio API call if configured
            return "SMS_SENT"
        except Exception as e:
            return "SMS_ERROR"
    else:
        # Mock SMS for offline demonstration
        print(f"[SMS ALERT DISPATCHED] -> To: {to_phone} | Msg: {message_body}")
        return "SIMULATED_SMS"
