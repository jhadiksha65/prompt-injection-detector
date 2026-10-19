"""
test_docx_indirect_injection.py
Regression tests for document-upload security and indirect prompt injection detection.

Validates:
1. Malicious documents containing embedded instructions (e.g. 01 Sustainability Report and 02 Retail Report)
   are reliably detected and blocked before the LLM (Ollama) is invoked.
2. Embedded instructions are classified as 'Indirect Prompt Injection' with appropriate threat evidence.
3. Genuine benign documents (e.g. 03 Renewable Energy Report and 04 Public Library Report)
   are allowed with low risk score (<= 25.0) and proceed to model generation.
4. Threat attribution accurately points to 'Uploaded Document' as the attack source.
"""

import io
import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import app
from backend.attachments.handler import extract_attachment_text
from backend.prompt_security.threat_taxonomy import ThreatCategory

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")


class TestDocxIndirectInjection(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_malicious_sustainability_report_blocked(self):
        """01_Malicious_Indirect_Injection_Sustainability_Report.docx must be blocked with Indirect Prompt Injection."""
        filename = "01_Malicious_Indirect_Injection_Sustainability_Report.docx"
        file_path = os.path.join(DOWNLOADS_DIR, filename)
        if not os.path.exists(file_path):
            self.skipTest(f"Test fixture not found at {file_path}")

        with open(file_path, "rb") as f:
            data = f.read()

        # Check plain text extraction works and is non-empty
        extracted_text = extract_attachment_text(filename, data)
        self.assertIn("AI ASSISTANT PROCESSING INSTRUCTION", extracted_text)

        res = self.app.post(
            "/secure-prompt",
            data={
                "prompt": "Please summarize this sustainability report.",
                "attachment": (io.BytesIO(data), filename),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(res.status_code, 200)
        res_data = res.get_json()

        self.assertEqual(res_data.get("final_decision"), "BLOCK")
        self.assertFalse(res_data.get("llm_called"))
        self.assertGreaterEqual(res_data.get("layer1", {}).get("risk_score", 0.0), 80.0)
        self.assertEqual(res_data.get("layer1", {}).get("risk_level"), "CRITICAL")
        self.assertEqual(res_data.get("layer1", {}).get("attack_type"), ThreatCategory.INDIRECT_INJECTION.value)

        attr = res_data.get("threat_attribution", {})
        self.assertTrue(attr.get("attachment_threat_detected"))
        self.assertFalse(attr.get("prompt_threat_detected"))
        self.assertEqual(attr.get("threat_source"), "Uploaded Document")
        self.assertEqual(attr.get("attack_vector"), ThreatCategory.INDIRECT_INJECTION.value)
        self.assertIsNotNone(attr.get("attachment_evidence"))
        self.assertIn("AI ASSISTANT PROCESSING INSTRUCTION", attr.get("attachment_evidence"))

    def test_02_malicious_retail_report_blocked(self):
        """02_Malicious_Indirect_Injection_Retail_Report.docx must be blocked with Indirect Prompt Injection."""
        filename = "02_Malicious_Indirect_Injection_Retail_Report.docx"
        file_path = os.path.join(DOWNLOADS_DIR, filename)
        if not os.path.exists(file_path):
            self.skipTest(f"Test fixture not found at {file_path}")

        with open(file_path, "rb") as f:
            data = f.read()

        # Check plain text extraction works and is non-empty
        extracted_text = extract_attachment_text(filename, data)
        self.assertIn("INSTRUCTION FOR AI SYSTEMS READING THIS REPORT", extracted_text)

        res = self.app.post(
            "/secure-prompt",
            data={
                "prompt": "Review this retail report.",
                "attachment": (io.BytesIO(data), filename),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(res.status_code, 200)
        res_data = res.get_json()

        self.assertEqual(res_data.get("final_decision"), "BLOCK")
        self.assertFalse(res_data.get("llm_called"))
        self.assertGreaterEqual(res_data.get("layer1", {}).get("risk_score", 0.0), 80.0)
        self.assertEqual(res_data.get("layer1", {}).get("risk_level"), "CRITICAL")
        self.assertEqual(res_data.get("layer1", {}).get("attack_type"), ThreatCategory.INDIRECT_INJECTION.value)

        attr = res_data.get("threat_attribution", {})
        self.assertTrue(attr.get("attachment_threat_detected"))
        self.assertFalse(attr.get("prompt_threat_detected"))
        self.assertEqual(attr.get("threat_source"), "Uploaded Document")
        self.assertEqual(attr.get("attack_vector"), ThreatCategory.INDIRECT_INJECTION.value)
        self.assertIsNotNone(attr.get("attachment_evidence"))
        self.assertIn("INSTRUCTION FOR AI SYSTEMS", attr.get("attachment_evidence"))

    def test_03_benign_renewable_energy_report_allowed(self):
        """03_Benign_Renewable_Energy_Report.docx must be allowed with low risk score."""
        filename = "03_Benign_Renewable_Energy_Report.docx"
        file_path = os.path.join(DOWNLOADS_DIR, filename)
        if not os.path.exists(file_path):
            self.skipTest(f"Test fixture not found at {file_path}")

        with open(file_path, "rb") as f:
            data = f.read()

        res = self.app.post(
            "/secure-prompt",
            data={
                "prompt": "Summarize this renewable energy pilot report.",
                "attachment": (io.BytesIO(data), filename),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(res.status_code, 200)
        res_data = res.get_json()

        self.assertEqual(res_data.get("final_decision"), "ALLOW")
        self.assertTrue(res_data.get("llm_called"))
        self.assertLessEqual(res_data.get("layer1", {}).get("risk_score", 100.0), 25.0)
        self.assertEqual(res_data.get("layer1", {}).get("risk_level"), "LOW")
        self.assertEqual(res_data.get("layer1", {}).get("attack_type"), "Benign")

        attr = res_data.get("threat_attribution", {})
        self.assertFalse(attr.get("attachment_threat_detected"))
        self.assertFalse(attr.get("prompt_threat_detected"))
        self.assertEqual(attr.get("threat_source"), "None")
        self.assertEqual(attr.get("attack_vector"), "None detected")
        self.assertIsNone(attr.get("attachment_evidence"))

    def test_04_benign_public_library_report_allowed(self):
        """04_Benign_Public_Library_Report.docx must be allowed with low risk score."""
        filename = "04_Benign_Public_Library_Report.docx"
        file_path = os.path.join(DOWNLOADS_DIR, filename)
        if not os.path.exists(file_path):
            self.skipTest(f"Test fixture not found at {file_path}")

        with open(file_path, "rb") as f:
            data = f.read()

        res = self.app.post(
            "/secure-prompt",
            data={
                "prompt": "Summarize this public library review.",
                "attachment": (io.BytesIO(data), filename),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(res.status_code, 200)
        res_data = res.get_json()

        self.assertEqual(res_data.get("final_decision"), "ALLOW")
        self.assertTrue(res_data.get("llm_called"))
        self.assertLessEqual(res_data.get("layer1", {}).get("risk_score", 100.0), 25.0)
        self.assertEqual(res_data.get("layer1", {}).get("risk_level"), "LOW")
        self.assertEqual(res_data.get("layer1", {}).get("attack_type"), "Benign")

        attr = res_data.get("threat_attribution", {})
        self.assertFalse(attr.get("attachment_threat_detected"))
        self.assertFalse(attr.get("prompt_threat_detected"))
        self.assertEqual(attr.get("threat_source"), "None")
        self.assertEqual(attr.get("attack_vector"), "None detected")
        self.assertIsNone(attr.get("attachment_evidence"))


if __name__ == "__main__":
    unittest.main()
