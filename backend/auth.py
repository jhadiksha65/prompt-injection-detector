"""
auth.py
Admin authentication for security-management endpoints (incident/stats
dashboards, the re-authentication/unlock challenge).

No credentials are hardcoded in source. The admin password is resolved,
in order of preference, from:
  1. ADMIN_PASSWORD_HASH  - a pre-computed werkzeug password hash (preferred
                             for production: the plaintext password never
                             needs to touch the server's environment at
                             startup).
  2. ADMIN_PASSWORD       - a plaintext password (convenience for local/dev
                             use), hashed in memory at startup and never
                             logged or persisted.
  3. Neither set          - a random password is generated at startup and
                             printed to the server console ONCE, the same
                             pattern used by e.g. Django's createsuperuser
                             flow. There is no fixed fallback credential.

Password verification uses werkzeug.security's PBKDF2-based
generate_password_hash/check_password_hash (a salted, slow hash already
shipped with Flask's own dependency, so this adds no new dependency),
replacing the previous unsalted, single-round SHA-256 comparison.
"""

import os
import secrets
from functools import wraps

from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"

_ADMIN_PASSWORD_HASH = None
_ADMIN_PASSWORD_AUTO_GENERATED = False


def _resolve_admin_password_hash():
    global _ADMIN_PASSWORD_AUTO_GENERATED

    configured_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
    if configured_hash:
        return configured_hash

    configured_plain = os.getenv("ADMIN_PASSWORD", "").strip()
    if configured_plain:
        return generate_password_hash(configured_plain)

    # No credential configured anywhere: generate one, once, for this
    # process only. This is intentionally never persisted or reused across
    # restarts, so it must be explicitly configured for any real deployment.
    generated_password = secrets.token_urlsafe(18)
    _ADMIN_PASSWORD_AUTO_GENERATED = True
    print(
        "[AUTH] No ADMIN_PASSWORD_HASH or ADMIN_PASSWORD configured. "
        "Generated a one-time admin password for this session:\n"
        f"[AUTH]   username: {ADMIN_USERNAME}\n"
        f"[AUTH]   password: {generated_password}\n"
        "[AUTH] Set ADMIN_PASSWORD_HASH (preferred) or ADMIN_PASSWORD in "
        "the environment for a stable credential in real deployments."
    )
    return generate_password_hash(generated_password)


def init_admin_auth():
    """Resolves and caches the admin password hash. Call once at startup."""
    global _ADMIN_PASSWORD_HASH
    _ADMIN_PASSWORD_HASH = _resolve_admin_password_hash()
    return _ADMIN_PASSWORD_HASH


def verify_admin_credentials(username: str, password: str) -> bool:
    """Timing-safe credential check against the resolved admin hash."""
    if _ADMIN_PASSWORD_HASH is None:
        init_admin_auth()
    if not username or not password:
        return False
    if username != ADMIN_USERNAME:
        # Still run a hash check against a bogus value so a wrong username
        # takes roughly the same time as a wrong password (no early exit
        # that would let username enumeration be timed).
        check_password_hash(_ADMIN_PASSWORD_HASH, password)
        return False
    return check_password_hash(_ADMIN_PASSWORD_HASH, password)


def _unauthorized_response():
    response = jsonify({"error": "Authentication required to access this resource."})
    response.status_code = 401
    response.headers["WWW-Authenticate"] = 'Basic realm="Prompt Security Admin"'
    return response


def require_admin_auth(view_func):
    """Decorator: protects admin/security-management endpoints with HTTP
    Basic Auth, checked against the configured (never hardcoded) admin
    credential."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        if not auth or not verify_admin_credentials(auth.username, auth.password):
            return _unauthorized_response()
        return view_func(*args, **kwargs)

    return wrapped
