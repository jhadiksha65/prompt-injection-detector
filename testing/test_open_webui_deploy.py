"""
test_open_webui_deploy.py
Unit and Integration tests for Open WebUI Deployment and Integration endpoints.

Verifies:
1. GET /v1/models and GET /api/v1/models return OpenAI-compatible model listing with 'prompt-security-guard'.
2. GET /deploy serves the clean 'Deploy Prompt Security Guard' landing page.
3. GET /api/open-webui/status reports connection status accurately.
4. POST /api/open-webui/connect checks connectivity and verifies dual-layer protection.
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import app


class TestOpenWebUIDeploy(unittest.TestCase):
    """Test suite for Open WebUI deployment page and endpoints."""

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_deploy_page_renders_cleanly(self):
        """GET /deploy should return HTTP 200 with title 'Deploy Prompt Security Guard'."""
        res = self.client.get("/deploy")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("Deploy Prompt Security Guard", html)
        self.assertIn("Connect to Open WebUI", html)
        self.assertIn("prompt-security-guard", html)
        # Should NOT contain complex dashboards or charts
        self.assertNotIn("chart.js", html.lower())
        self.assertNotIn("<canvas", html.lower())

    def test_models_endpoint_openwebui_format(self):
        """GET /v1/models should return valid OpenAI models payload containing prompt-security-guard."""
        for path in ["/v1/models", "/api/v1/models", "/models", "/api/models"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("object"), "list")
            ids = [m["id"] for m in data.get("data", [])]
            self.assertIn("prompt-security-guard", ids)
            # Find the guard model
            guard = next(m for m in data["data"] if m["id"] == "prompt-security-guard")
            self.assertEqual(guard["owned_by"], "prompt-security")

    def test_openwebui_status_endpoint_offline(self):
        """When Open WebUI port is not responding, status should be 'Not Connected'."""
        with patch("urllib.request.urlopen", side_effect=OSError("Connection refused")):
            res = self.client.get("/api/open-webui/status")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("status"), "Not Connected")
            self.assertFalse(data.get("connected"))

    def test_openwebui_status_endpoint_online(self):
        """When Open WebUI port responds, status should report 'Connected — Protection Verified'."""
        mock_res = MagicMock()
        mock_res.status = 200
        mock_res.__enter__.return_value = mock_res
        with patch("urllib.request.urlopen", return_value=mock_res):
            res = self.client.get("/api/open-webui/status")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("status"), "Connected — Protection Verified")
            self.assertTrue(data.get("connected"))

    def test_openwebui_connect_failure_handling(self):
        """When connection fails, connect returns 400 with exact instructions and truthful state."""
        with patch("urllib.request.urlopen", side_effect=OSError("Connection refused")):
            res = self.client.post("/api/open-webui/connect")
            self.assertEqual(res.status_code, 400)
            data = res.get_json()
            self.assertEqual(data.get("status"), "Connection Failed")
            self.assertFalse(data.get("connected"))
            self.assertIn("instruction", data)

    def test_integrate_page_renders_cleanly(self):
        """GET /integrate serves the 'Integrate Prompt Security Guard' landing page."""
        res = self.client.get("/integrate")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("Integrate Prompt Security Guard", html)
        self.assertIn("targetAppUrl", html)
        self.assertIn("prompt-security-guard", html)

    def test_integrate_connect_unconfigured_target_returns_configuration_required(self):
        """When target URL is reachable but not yet verified to route through gateway, return Configuration Required."""
        mock_res = MagicMock()
        mock_res.status = 200
        mock_res.__enter__.return_value = mock_res
        with patch("urllib.request.urlopen", return_value=mock_res):
            res = self.client.post("/api/integrate/connect", json={"target_url": "http://localhost:3000"})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("status"), "Configuration Required")
            self.assertFalse(data.get("connected"))
            self.assertIn("instruction", data)
            self.assertIn("/v1", data["instruction"])

    def test_integrate_connect_unreachable_target_returns_connection_failed(self):
        """When target URL is unreachable, return HTTP 400 Connection Failed."""
        with patch("urllib.request.urlopen", side_effect=OSError("Connection refused")):
            res = self.client.post("/api/integrate/connect", json={"target_url": "http://localhost:9999"})
            self.assertEqual(res.status_code, 400)
            data = res.get_json()
            self.assertEqual(data.get("status"), "Connection Failed")
            self.assertFalse(data.get("connected"))
            self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
