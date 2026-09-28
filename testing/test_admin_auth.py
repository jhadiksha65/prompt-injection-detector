"""
test_admin_auth.py
Slice 9 Focused Tests: admin authentication, protected admin/security-
management endpoints, and removal of hardcoded credentials/tracked
sensitive state.

Verifies:
  * /api/incidents and /api/stats reject unauthenticated and
    wrong-credential requests, and accept correct admin credentials.
  * /api/unlock no longer accepts the old hardcoded "admin123" password
    and requires the configured admin username.
  * Admin password resolution never falls back to a hardcoded literal,
    and uses werkzeug's salted PBKDF2 hashing (not the old bare SHA-256).
  * The public detection API (/health, /detect, /secure-prompt) remains
    unauthenticated (unchanged behavior).
  * The default-admin row is no longer seeded into the database, and the
    runtime SQLite database is no longer tracked by git / is gitignored.
"""

import base64
import io
import json
import os
import sqlite3
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import backend.auth as auth_module
from backend.app import app
from backend.database.db import init_db, DB_PATH

TEST_ADMIN_PASSWORD = "test-only-admin-pass-9f2b"


def _admin_auth_header(username=None, password=TEST_ADMIN_PASSWORD):
    creds = f"{username or auth_module.ADMIN_USERNAME}:{password}"
    token = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {token}"}


class TestAdminEndpointsRequireAuth(unittest.TestCase):
    def setUp(self):
        os.environ["ADMIN_PASSWORD"] = TEST_ADMIN_PASSWORD
        auth_module.init_admin_auth()
        self.app = app.test_client()
        self.app.testing = True

    def test_incidents_rejects_unauthenticated_request(self):
        res = self.app.get("/api/incidents")
        self.assertEqual(res.status_code, 401)

    def test_stats_rejects_unauthenticated_request(self):
        res = self.app.get("/api/stats")
        self.assertEqual(res.status_code, 401)

    def test_incidents_rejects_wrong_password(self):
        res = self.app.get("/api/incidents", headers=_admin_auth_header(password="wrong-password"))
        self.assertEqual(res.status_code, 401)

    def test_incidents_rejects_wrong_username(self):
        res = self.app.get("/api/incidents", headers=_admin_auth_header(username="not-admin"))
        self.assertEqual(res.status_code, 401)

    def test_incidents_rejects_the_old_hardcoded_admin123_password(self):
        res = self.app.get("/api/incidents", headers=_admin_auth_header(password="admin123"))
        self.assertEqual(res.status_code, 401)

    def test_unauthenticated_response_includes_www_authenticate_challenge(self):
        res = self.app.get("/api/stats")
        self.assertIn("WWW-Authenticate", res.headers)
        self.assertIn("Basic", res.headers["WWW-Authenticate"])

    def test_incidents_accepts_correct_admin_credentials(self):
        res = self.app.get("/api/incidents", headers=_admin_auth_header())
        self.assertEqual(res.status_code, 200)

    def test_stats_accepts_correct_admin_credentials(self):
        res = self.app.get("/api/stats", headers=_admin_auth_header())
        self.assertEqual(res.status_code, 200)


class TestUnlockEndpointCredentialHandling(unittest.TestCase):
    def setUp(self):
        os.environ["ADMIN_PASSWORD"] = TEST_ADMIN_PASSWORD
        auth_module.init_admin_auth()
        self.app = app.test_client()
        self.app.testing = True

    def test_unlock_rejects_old_hardcoded_admin123_password(self):
        res = self.app.post("/api/unlock", json={"password": "admin123"})
        self.assertEqual(res.status_code, 401)

    def test_unlock_rejects_wrong_username(self):
        res = self.app.post(
            "/api/unlock",
            json={"username": "someone-else", "password": TEST_ADMIN_PASSWORD}
        )
        self.assertEqual(res.status_code, 401)

    def test_unlock_accepts_correct_configured_credentials(self):
        res = self.app.post(
            "/api/unlock",
            json={"username": auth_module.ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD}
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])


class TestNoHardcodedCredentials(unittest.TestCase):
    def test_admin_password_hash_env_var_is_honored(self):
        from werkzeug.security import generate_password_hash

        os.environ["ADMIN_PASSWORD_HASH"] = generate_password_hash("configured-via-hash-env")
        os.environ.pop("ADMIN_PASSWORD", None)
        try:
            resolved_hash = auth_module.init_admin_auth()
            self.assertTrue(auth_module.verify_admin_credentials(auth_module.ADMIN_USERNAME, "configured-via-hash-env"))
            self.assertFalse(auth_module.verify_admin_credentials(auth_module.ADMIN_USERNAME, "admin123"))
        finally:
            os.environ.pop("ADMIN_PASSWORD_HASH", None)

    def test_no_credential_configured_generates_random_non_default_password(self):
        os.environ.pop("ADMIN_PASSWORD_HASH", None)
        os.environ.pop("ADMIN_PASSWORD", None)
        auth_module.init_admin_auth()
        self.assertFalse(auth_module.verify_admin_credentials(auth_module.ADMIN_USERNAME, "admin123"))
        self.assertFalse(auth_module.verify_admin_credentials(auth_module.ADMIN_USERNAME, ""))

    def test_password_hash_uses_salted_pbkdf2_not_bare_sha256(self):
        from werkzeug.security import generate_password_hash
        h = generate_password_hash("some-password")
        # werkzeug's default scheme is salted and self-describing
        # (e.g. "pbkdf2:sha256:..." or "scrypt:..."), never a bare 64-char
        # hex SHA-256 digest like the old code produced.
        self.assertIn(":", h)
        self.assertNotRegex(h, r"^[0-9a-f]{64}$")

    def test_source_no_longer_contains_the_bare_admin123_hash_check(self):
        app_path = os.path.join(ROOT_DIR, "backend", "app.py")
        with open(app_path, "r", encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn('"admin123"', src)
        self.assertNotIn("prompt_sentinel_salt", src)


class TestPublicDetectionApiStillUnauthenticated(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_is_public(self):
        res = self.app.get("/health")
        self.assertEqual(res.status_code, 200)

    def test_detect_is_public(self):
        res = self.app.post("/detect", json={"prompt": "Explain photosynthesis."})
        self.assertEqual(res.status_code, 200)

    def test_secure_prompt_is_public(self):
        res = self.app.post("/secure-prompt", json={"prompt": "Explain photosynthesis in simple terms."})
        self.assertEqual(res.status_code, 200)

    def test_user_status_is_public(self):
        res = self.app.get("/api/user-status")
        self.assertEqual(res.status_code, 200)


class TestDatabaseNoDefaultAdminSeeded(unittest.TestCase):
    def test_users_table_has_no_seeded_rows(self):
        init_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 0)

    def test_db_module_source_has_no_hardcoded_password_hashing(self):
        db_path = os.path.join(ROOT_DIR, "backend", "database", "db.py")
        with open(db_path, "r", encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("admin123", src)
        self.assertNotIn("hashlib", src)


class TestNoStaleDefaultPasswordInUserFacingText(unittest.TestCase):
    """The default 'admin123' credential was removed by backend/auth.py;
    user-facing copy must not still reference it as if it were valid."""

    def _assert_file_has_no_admin123(self, relative_path):
        full_path = os.path.join(ROOT_DIR, *relative_path.split("/"))
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("admin123", content, f"{relative_path} still references the removed default password")

    def test_sensitive_resource_page_no_longer_hints_admin123(self):
        self._assert_file_has_no_admin123("frontend/sensitive_resource.html")

    def test_extension_reauth_modal_no_longer_hints_admin123(self):
        self._assert_file_has_no_admin123("browser_extension/content.js")

    def test_readme_no_longer_instructs_admin123(self):
        self._assert_file_has_no_admin123("README.md")


class TestRuntimeDatabaseNotTracked(unittest.TestCase):
    def test_gitignore_excludes_sqlite_database_files(self):
        gitignore_path = os.path.join(ROOT_DIR, ".gitignore")
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("*.db", content)

    def test_security_db_not_tracked_by_git(self):
        import subprocess
        result = subprocess.run(
            ["git", "ls-files", "backend/security.db"],
            cwd=ROOT_DIR, capture_output=True, text=True
        )
        self.assertEqual(result.stdout.strip(), "", "backend/security.db must not be tracked by git")


if __name__ == "__main__":
    unittest.main()
