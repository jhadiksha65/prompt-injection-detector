"""
test_extension_parity.py
Slice 8 Focused Tests: browser extension parity with the /secure-prompt
pipeline and verdict contract, and the associated safety fixes.

Since the extension is plain browser JS (no bundler/test runner in this
repo), these are static-source assertions on the shipped extension files
(the same technique used for the web UI in slices 5/6), plus a couple of
executable checks run through Node's `vm` module for pure, chrome-API-free
helper logic (config.js's URL validation).

Verifies:
  * background.js calls /secure-prompt (not /detect) for both CHECK_PROMPT
    and SCAN_CURRENT_TAB, and contains no independent security-decision
    logic (no local risk scoring) — every verdict comes straight from the
    backend response.
  * Backend failure fails CLOSED: background.js's catch/fallback path never
    synthesizes a "safe"/ALLOW verdict, and content.js never lets a
    submission through when the check itself failed.
  * content.js calls preventDefault()/stopPropagation() synchronously,
    before chrome.runtime.sendMessage (the async backend check) is called.
  * No unsafe innerHTML assignment carrying backend-derived dynamic text
    (reason/attack_type/risk data) anywhere in content.js or popup.js.
  * Full prompt text is never written into chrome.storage.local.
  * The API host is configurable (config.js + a popup Settings UI), not a
    single hardcoded production-only localhost string, and manifest.json
    declares optional_host_permissions so a custom host can be granted at
    runtime.
"""

import json
import os
import re
import subprocess
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXT_DIR = os.path.join(ROOT_DIR, "browser_extension")


def _read(name: str) -> str:
    with open(os.path.join(EXT_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


class TestBackgroundUsesSecurePromptPipeline(unittest.TestCase):
    def setUp(self):
        self.src = _read("background.js")

    def test_uses_secure_prompt_endpoint(self):
        self.assertIn("/secure-prompt", self.src)

    def test_no_longer_uses_detect_endpoint(self):
        self.assertNotIn("/detect", self.src)

    def test_no_duplicated_security_decision_logic(self):
        """The background script must not compute its own risk/decision —
        it only relays the backend's response."""
        for forbidden in ["risk_score +=", "riskScore +=", "decision =", "computeRisk", "calculateRisk"]:
            self.assertNotIn(forbidden, self.src)

    def test_never_sends_demo_layer2_leak_flag(self):
        self.assertNotIn("demo_layer2_leak", self.src)

    def test_request_body_only_sends_prompt(self):
        # Both fetch calls to /secure-prompt must send only {prompt: ...}.
        bodies = re.findall(r"JSON\.stringify\((\{[^}]*\})\)", self.src)
        secure_prompt_bodies = [b for b in bodies if "prompt" in b and "username" not in b]
        self.assertTrue(secure_prompt_bodies)
        for body in secure_prompt_bodies:
            self.assertNotIn("demo_layer2_leak", body)


class TestBackendFailureFailsClosed(unittest.TestCase):
    def setUp(self):
        self.src = _read("background.js")

    def test_catch_block_does_not_synthesize_allow_decision(self):
        """The old code's catch-block fallback (`decision: "ALLOW"`, a fake
        heuristic-bypass result) must be gone entirely."""
        self.assertNotIn('"decision": "ALLOW"', self.src)
        self.assertNotIn("decision: \"ALLOW\"", self.src)
        self.assertNotIn("heuristic bypass", self.src.lower())

    def test_backend_unavailable_response_is_explicitly_unsuccessful(self):
        self.assertIn("_backendUnavailableResponse", self.src)
        self.assertIn("success: false", self.src)

    def test_backend_unavailable_response_has_no_data_field_pretending_safety(self):
        func_match = re.search(
            r"function _backendUnavailableResponse\(\)\s*\{(.*?)\n\}",
            self.src,
            re.DOTALL,
        )
        self.assertIsNotNone(func_match)
        body = func_match.group(1)
        self.assertNotIn("ALLOW", body)
        self.assertNotIn("is_injection", body)


class TestContentScriptSynchronousPreventDefault(unittest.TestCase):
    def setUp(self):
        self.src = _read("content.js")

    def test_prevent_default_called_before_async_backend_check(self):
        func_match = re.search(
            r"function handlePromptInterception\(e\)\s*\{(.*?)\n\}\n",
            self.src,
            re.DOTALL,
        )
        self.assertIsNotNone(func_match, "handlePromptInterception not found")
        body = func_match.group(1)

        prevent_default_idx = body.index("e.preventDefault()")
        send_message_idx = body.index("chrome.runtime.sendMessage")
        self.assertLess(
            prevent_default_idx, send_message_idx,
            "preventDefault() must happen synchronously, before the async "
            "chrome.runtime.sendMessage backend check begins."
        )

    def test_stop_propagation_also_synchronous(self):
        func_match = re.search(
            r"function handlePromptInterception\(e\)\s*\{(.*?)\n\}\n",
            self.src,
            re.DOTALL,
        )
        body = func_match.group(1)
        send_message_idx = body.index("chrome.runtime.sendMessage")
        self.assertLess(body.index("e.stopPropagation()"), send_message_idx)
        self.assertLess(body.index("e.stopImmediatePropagation()"), send_message_idx)

    def test_no_submission_approval_without_a_successful_response(self):
        """approveAndResubmit()/triggerOriginalSubmit() must only be reachable
        through the successful-response branch, never the failure branch."""
        callback_match = re.search(
            r"chrome\.runtime\.sendMessage\(\{\s*type: \"CHECK_PROMPT\".*?\}, \(response\) => \{(.*?)\n    \}\);",
            self.src,
            re.DOTALL,
        )
        self.assertIsNotNone(callback_match)
        callback_body = callback_match.group(1)

        failure_branch, _, success_branch = callback_body.partition("const data = response.data;")
        self.assertIn("showBackendUnavailableNotice", failure_branch)
        self.assertNotIn("approveAndResubmit", failure_branch)
        self.assertNotIn("triggerOriginalSubmit", failure_branch)


class TestNoUnsafeInnerHtmlForBackendContent(unittest.TestCase):
    def test_content_js_does_not_interpolate_backend_fields_into_innerhtml(self):
        src = _read("content.js")
        # These backend-derived values must never appear directly inside a
        # `${...}` interpolation that is itself inside an .innerHTML template.
        for forbidden in [
            "${result.reason}", "${result.attack_type}", "${result.risk_level}",
            "${data.reason}", "${data.attack_type}",
            "${layer1.reason}", "${layer1.attack_type}", "${layer1.risk_level}",
        ]:
            self.assertNotIn(forbidden, src)

    def test_content_js_hydrates_dynamic_fields_via_textcontent(self):
        src = _read("content.js")
        self.assertIn('getElementById("pid-reason-text").textContent', src)
        self.assertIn('getElementById("pid-attack-type-text").textContent', src)
        self.assertIn('getElementById("pid-risk-level-text").textContent', src)

    def test_toast_functions_do_not_use_innerhtml(self):
        src = _read("content.js")
        toast_match = re.search(r"function showSafeToast\(score\)\s*\{(.*?)\n\}\n", src, re.DOTALL)
        self.assertIsNotNone(toast_match)
        self.assertNotIn(".innerHTML", toast_match.group(1))

    def test_popup_js_does_not_use_innerhtml(self):
        src = _read("popup.js")
        self.assertNotIn(".innerHTML", src)


class TestNoUnnecessaryFullPromptCaching(unittest.TestCase):
    def test_background_js_stores_snippet_not_full_prompt(self):
        src = _read("background.js")
        record_match = re.search(
            r"function recordLastScan\(promptText, backendResult\)\s*\{(.*?)\n\}\n",
            src,
            re.DOTALL,
        )
        self.assertIsNotNone(record_match)
        body = record_match.group(1)
        self.assertIn("MAX_SNIPPET_CHARS", body)
        self.assertIn("slice(0, MAX_SNIPPET_CHARS)", body)
        # The full, untruncated prompt variable must never be assigned as a
        # stored field value.
        self.assertNotIn("prompt: promptText", body)
        self.assertNotIn("prompt: capturedText", body)

    def test_popup_js_only_persists_snippet_field_on_reload(self):
        src = _read("popup.js")
        self.assertIn("last.prompt_snippet", src)
        self.assertNotIn("last.prompt,", src)


class TestConfigurableApiHost(unittest.TestCase):
    def test_config_js_exists_with_default_and_getter(self):
        src = _read("config.js")
        self.assertIn("DEFAULT_API_BASE_URL", src)
        self.assertIn("function getApiBaseUrl", src)
        self.assertIn("function setApiBaseUrl", src)
        self.assertIn("chrome.storage.local", src)

    def test_background_and_popup_resolve_host_dynamically(self):
        for fname in ["background.js", "popup.js"]:
            src = _read(fname)
            self.assertIn("getApiBaseUrl()", src)

    def test_background_js_does_not_hardcode_a_single_fetch_base_url(self):
        src = _read("background.js")
        # No literal API_BASE_URL constant baked into this file (that pattern
        # was the old hardcoded-localhost bug); it must come from config.js.
        self.assertNotIn('const API_BASE_URL = "http://localhost:5000"', src)

    def test_manifest_declares_optional_host_permissions_for_custom_hosts(self):
        with open(os.path.join(EXT_DIR, "manifest.json"), "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertIn("optional_host_permissions", manifest)
        self.assertTrue(len(manifest["optional_host_permissions"]) > 0)

    def test_popup_html_has_settings_ui_for_backend_url(self):
        with open(os.path.join(EXT_DIR, "popup.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn('id="apiUrlInput"', html)
        self.assertIn('id="apiUrlSaveBtn"', html)


class TestConfigJsUrlValidationBehavior(unittest.TestCase):
    """Executes config.js's pure, chrome-API-free _normalizeBaseUrl() via
    Node's vm module (no npm dependency needed — Node's stdlib only)."""

    @classmethod
    def setUpClass(cls):
        if subprocess.run(["which", "node"], capture_output=True).returncode != 0:
            raise unittest.SkipTest("node is not available in this environment")

    def _normalize(self, value):
        config_path = os.path.join(EXT_DIR, "config.js").replace("\\", "\\\\")
        script = f"""
        const fs = require('fs');
        const vm = require('vm');
        const src = fs.readFileSync('{config_path}', 'utf8');
        const sandbox = {{
            chrome: {{ storage: {{ local: {{ get: ()=>{{}}, set: ()=>{{}} }} }}, permissions: {{ request: ()=>{{}} }} }},
            console
        }};
        vm.createContext(sandbox);
        vm.runInContext(src, sandbox);
        const result = sandbox._normalizeBaseUrl({json.dumps(value)});
        console.log(JSON.stringify(result));
        """
        result = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout.strip())

    def test_accepts_valid_http_url(self):
        self.assertEqual(self._normalize("http://localhost:5000"), "http://localhost:5000")

    def test_strips_trailing_slash(self):
        self.assertEqual(self._normalize("http://localhost:5000/"), "http://localhost:5000")

    def test_accepts_https_production_host(self):
        self.assertEqual(
            self._normalize("https://security-api.example.com"),
            "https://security-api.example.com",
        )

    def test_rejects_non_url_garbage(self):
        self.assertIsNone(self._normalize("not a url at all"))

    def test_rejects_javascript_pseudo_protocol(self):
        self.assertIsNone(self._normalize("javascript:alert(1)"))

    def test_rejects_empty_string(self):
        self.assertIsNone(self._normalize(""))


if __name__ == "__main__":
    unittest.main()
