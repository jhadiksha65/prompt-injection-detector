"""
db.py
SQLite Database initialization, connection management, and helper queries
for incident logging, statistics, and user authentication.
"""

import sqlite3
import os
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "security.db"))


def get_connection():
    """Returns a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes database schema and creates default admin user if not exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Incidents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT UNIQUE NOT NULL,
        timestamp TEXT NOT NULL,
        prompt_snippet TEXT NOT NULL,
        risk_score REAL NOT NULL,
        risk_level TEXT NOT NULL,
        attack_type TEXT NOT NULL,
        layer1_decision TEXT NOT NULL,
        layer2_decision TEXT NOT NULL,
        final_decision TEXT NOT NULL,
        reason TEXT,
        alert_status TEXT NOT NULL,
        client_ip TEXT
    )
    """)

    # 2. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_locked INTEGER NOT NULL DEFAULT 0,
        role TEXT NOT NULL DEFAULT 'user',
        last_login TEXT
    )
    """)

    # Create default user if empty (demo_user / admin123)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        salt = "prompt_sentinel_salt"
        default_pwd_hash = hashlib.sha256((salt + "admin123").encode("utf-8")).hexdigest()
        cursor.execute("""
        INSERT INTO users (username, password_hash, is_locked, role, last_login)
        VALUES (?, ?, 0, 'admin', ?)
        """, ("admin", default_pwd_hash, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()


def log_incident(
    prompt: str,
    risk_score: float,
    risk_level: str,
    attack_type: str,
    layer1_decision: str,
    layer2_decision: str,
    final_decision: str,
    reason: str,
    alert_status: str = "SKIPPED",
    client_ip: str = "127.0.0.1"
) -> str:
    """Logs a security event to the SQLite database."""
    req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.utcnow().isoformat()
    # Mask prompt to avoid storing raw sensitive credentials
    snippet = prompt[:120] + "..." if len(prompt) > 120 else prompt

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO incidents (
        request_id, timestamp, prompt_snippet, risk_score, risk_level,
        attack_type, layer1_decision, layer2_decision, final_decision,
        reason, alert_status, client_ip
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        req_id, timestamp, snippet, risk_score, risk_level,
        attack_type, layer1_decision, layer2_decision, final_decision,
        reason, alert_status, client_ip
    ))
    conn.commit()
    conn.close()
    return req_id


def get_all_incidents(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent incidents."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    incidents = [dict(row) for row in rows]
    conn.close()
    return incidents


def get_security_stats() -> Dict[str, Any]:
    """Computes high-level security metrics for the admin dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM incidents")
    total_requests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE final_decision = 'BLOCK'")
    blocked_requests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE risk_level IN ('HIGH', 'CRITICAL')")
    high_critical_threats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE layer2_decision IN ('BLOCK', 'MASK')")
    layer2_actions = cursor.fetchone()[0]

    conn.close()
    return {
        "total_requests": total_requests,
        "blocked_requests": blocked_requests,
        "high_critical_threats": high_critical_threats,
        "layer2_actions": layer2_actions,
        "block_rate_pct": round((blocked_requests / total_requests) * 100, 2) if total_requests > 0 else 0.0
    }
