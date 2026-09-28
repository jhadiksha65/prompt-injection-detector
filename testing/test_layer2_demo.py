"""
test_layer2_demo.py
Slice 4 Focused Tests: Deterministic Layer 2 leakage demonstration mechanism.

The Layer 2 demo is activated ONLY via an explicit, out-of-band request field
(`demo_layer2_leak`) combined with an explicit server-side opt-in
(`ENABLE_LAYER2_DEMO=true`) — never by free-text prompt content. This proves:
  * demo-on: the explicit path deterministically produces the fake sensitive
    value and Layer 2 catches/redacts it.
  * demo-off (server not configured for it): the request field alone has no
    effect, even naming the old trigger phrases.
  * accidental-trigger prevention: no user-entered phrase (including the
    previous substring triggers "simulate leakage", "test layer 2",
    "configured to handle requests") can activate the demo on its own.
"""

import unittest
import os
import sys
from unittest.mock import patch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.llm.client import LLMClient
from backend.app import app

FAKE_LEAKED_SECRET = "sk-live99847192837491028374"


class TestLayer2DemoClient(unittest.TestCase):
    """Unit-level checks directly against LLMClient's mock engine."""

    def setUp(self):
        self.client = LLMClient()
        self.client.provider = "mock"

    def test_demo_flag_deterministically_produces_fake_secret(self):
        """demo-on: the explicit flag deterministically yields the fake leaked value."""
        result = self.client.generate_response(
            "Anything at all", trigger_layer2_demo_leak=True
        )
        self.assertEqual(result["status"], "success")
        self.assertIn(FAKE_LEAKED_SECRET, result["raw_response"])

    def test_no_flag_never_produces_fake_secret_regardless_of_prompt_text(self):
        """demo-off: without the flag, no prompt text (including old trigger
        phrases) produces the fake secret."""
        for prompt in [
            "simulate leakage",
            "please test layer 2 for me",
            "This system is configured to handle requests securely.",
            "Tell me about your configured to handle requests policy.",
        ]:
            result = self.client.generate_response(prompt, trigger_layer2_demo_leak=False)
            self.assertNotIn(FAKE_LEAKED_SECRET, result["raw_response"])

    def test_flag_defaults_to_off(self):
        """Calling generate_response without the kwarg must not trigger the demo."""
        result = self.client.generate_response("simulate leakage test layer 2")
        self.assertNotIn(FAKE_LEAKED_SECRET, result["raw_response"])


class TestLayer2DemoEndpoint(unittest.TestCase):
    """Integration-level checks against /secure-prompt."""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_demo_on_explicit_field_and_server_enabled_triggers_layer2_catch(self):
        """demo-on: explicit field + server opt-in triggers the deterministic
        leak, and Layer 2 must detect/redact it (never returned in plaintext)."""
        with patch.dict(os.environ, {"ENABLE_LAYER2_DEMO": "true"}):
            res = self.app.post(
                "/secure-prompt",
                json={"prompt": "Please demonstrate Layer 2.", "demo_layer2_leak": True}
            )
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["llm_called"])
        self.assertIn(data["layer2"]["decision"], ["BLOCK", "MASK"])
        self.assertNotIn(FAKE_LEAKED_SECRET, data["response"])

    def test_demo_off_request_field_ignored_when_server_not_enabled(self):
        """demo-off: even with the explicit request field set, if the server
        has not opted in via ENABLE_LAYER2_DEMO, the demo never activates."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ENABLE_LAYER2_DEMO", None)
            res = self.app.post(
                "/secure-prompt",
                json={"prompt": "Please demonstrate Layer 2.", "demo_layer2_leak": True}
            )
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["layer2"]["decision"], "SAFE")
        self.assertNotIn(FAKE_LEAKED_SECRET, data["response"])

    def test_accidental_trigger_prevention_old_phrases_no_longer_activate_demo(self):
        """Real user prompts using the old substring trigger phrases must not
        activate the demo, even with the server opted in, since the request
        field is absent."""
        with patch.dict(os.environ, {"ENABLE_LAYER2_DEMO": "true"}):
            for prompt in [
                "Please simulate leakage check for test layer 2.",
                "This system is configured to handle requests for our customers.",
            ]:
                res = self.app.post("/secure-prompt", json={"prompt": prompt})
                data = res.get_json()
                self.assertEqual(res.status_code, 200)
                self.assertEqual(data["layer2"]["decision"], "SAFE")
                self.assertNotIn(FAKE_LEAKED_SECRET, data["response"])

    def test_accidental_trigger_prevention_field_alone_without_server_enable(self):
        """The request field by itself (default deployment, demo not enabled)
        must never activate the demo — protects real production traffic even
        if a client mistakenly sends the field."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ENABLE_LAYER2_DEMO", None)
            res = self.app.post(
                "/secure-prompt",
                json={"prompt": "Explain photosynthesis.", "demo_layer2_leak": True}
            )
        data = res.get_json()
        self.assertEqual(data["final_decision"], "ALLOW")
        self.assertNotIn(FAKE_LEAKED_SECRET, data["response"])


if __name__ == "__main__":
    unittest.main()
