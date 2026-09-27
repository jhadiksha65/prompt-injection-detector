"""
test_model_integrity.py
Slice 0 regression tests: frozen-model integrity verification and load-mode
transparency.

These tests are deliberately designed to pass BOTH with the real 267 MB weights
present and with only the Git LFS pointer, so the suite is honest in either
environment. Tests that require genuinely loaded weights are skipped with an
explicit reason rather than silently asserting nothing.
"""

import json
import os
import sys
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.prompt_security import model_integrity as mi
from backend.prompt_security.model_integrity import (
    EXPECTED_MODEL_SHA256,
    EXPECTED_MODEL_SIZE_BYTES,
    FROZEN_DECISION_THRESHOLD,
    ModelLoadStatus,
    PipelineMode,
    inspect_weights_file,
    is_lfs_pointer,
    parse_lfs_pointer,
    sha256_file,
)

PROD_MODEL_PATH = os.path.join(ROOT_DIR, "experiments", "distilbert", "distilbert_model_augmented.pt")


class TestFrozenModelConstants(unittest.TestCase):
    """The pinned constants ARE the frozen-model guarantee; guard them."""

    def test_01_pinned_sha256_is_the_approved_digest(self):
        self.assertEqual(
            EXPECTED_MODEL_SHA256,
            "a487e0be9008f2e55d44b4a025b2449cf77c94f53ed5582b3cebeee206e4a850",
        )

    def test_02_pinned_threshold_is_frozen_at_038(self):
        self.assertEqual(FROZEN_DECISION_THRESHOLD, 0.38)

    def test_03_pinned_size_is_the_approved_size(self):
        self.assertEqual(EXPECTED_MODEL_SIZE_BYTES, 267856473)


class TestWeightsFileInspection(unittest.TestCase):

    def test_04_sha256_file_matches_hashlib(self):
        import hashlib
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"prompt-injection-detector integrity probe")
            path = f.name
        try:
            expected = hashlib.sha256(b"prompt-injection-detector integrity probe").hexdigest()
            self.assertEqual(sha256_file(path), expected)
        finally:
            os.unlink(path)

    def test_05_missing_file_reports_file_missing(self):
        status, detail, sha = inspect_weights_file("/nonexistent/model.pt")
        self.assertEqual(status, ModelLoadStatus.FILE_MISSING)
        self.assertIsNone(sha)
        self.assertIn("No model file", detail)

    def test_06_tampered_weights_are_refused_with_hash_mismatch(self):
        """A substituted or retrained checkpoint must be refused, not loaded."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as f:
            f.write(b"not the frozen production model")
            path = f.name
        try:
            status, detail, sha = inspect_weights_file(path)
            self.assertEqual(status, ModelLoadStatus.HASH_MISMATCH)
            self.assertIsNotNone(sha)
            self.assertIn("Refusing to load", detail)
        finally:
            os.unlink(path)

    def test_07_verified_weights_are_allowed_to_proceed(self):
        """When the digest matches the expectation, inspection does not block."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as f:
            f.write(b"stand-in for verified weights")
            path = f.name
        try:
            actual = sha256_file(path)
            status, detail, sha = inspect_weights_file(path, expected_sha256=actual)
            self.assertIsNone(status, "verified weights must not be blocked")
            self.assertEqual(sha, actual)
        finally:
            os.unlink(path)

    def test_08_unfetched_lfs_pointer_is_detected_not_loaded(self):
        """An LFS pointer must never be mistaken for weights."""
        pointer = (
            b"version https://git-lfs.github.com/spec/v1\n"
            b"oid sha256:" + EXPECTED_MODEL_SHA256.encode() + b"\n"
            b"size 267856473\n"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as f:
            f.write(pointer)
            path = f.name
        try:
            self.assertTrue(is_lfs_pointer(path))
            oid, size = parse_lfs_pointer(path)
            self.assertEqual(oid, EXPECTED_MODEL_SHA256)
            self.assertEqual(size, EXPECTED_MODEL_SIZE_BYTES)
            status, detail, sha = inspect_weights_file(path)
            self.assertEqual(status, ModelLoadStatus.POINTER_NOT_FETCHED)
            self.assertIn("git lfs pull", detail)
        finally:
            os.unlink(path)

    def test_09_pointer_for_a_different_model_is_flagged(self):
        """A pointer referencing another model is a distinct, louder failure."""
        pointer = (
            b"version https://git-lfs.github.com/spec/v1\n"
            b"oid sha256:" + (b"0" * 64) + b"\n"
            b"size 123\n"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as f:
            f.write(pointer)
            path = f.name
        try:
            status, detail, sha = inspect_weights_file(path)
            self.assertEqual(status, ModelLoadStatus.POINTER_WRONG_MODEL)
            self.assertIn("not the pinned production model", detail)
        finally:
            os.unlink(path)

    def test_10_real_weights_are_not_misclassified_as_a_pointer(self):
        big = b"\x80\x02}" + os.urandom(2048)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as f:
            f.write(big)
            path = f.name
        try:
            self.assertFalse(is_lfs_pointer(path))
        finally:
            os.unlink(path)


class TestProductionModelInRepo(unittest.TestCase):
    """What the repository actually references right now."""

    def test_11_repo_references_the_approved_frozen_model(self):
        """
        Whether fetched or not, the repo must point at the approved model.
        """
        self.assertTrue(os.path.exists(PROD_MODEL_PATH), "production model path is absent")
        if is_lfs_pointer(PROD_MODEL_PATH):
            oid, _ = parse_lfs_pointer(PROD_MODEL_PATH)
            self.assertEqual(
                oid, EXPECTED_MODEL_SHA256,
                "LFS pointer references a model other than the approved frozen one",
            )
        else:
            self.assertEqual(
                sha256_file(PROD_MODEL_PATH), EXPECTED_MODEL_SHA256,
                "on-disk weights do not match the approved frozen model",
            )


class TestDetectorLoadState(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from backend.prompt_security.ml_detector import MLPromptDetector
        cls.detector = MLPromptDetector()

    def test_12_status_report_exposes_required_fields(self):
        r = self.detector.status_report()
        for key in (
            "load_status", "load_detail", "is_loaded", "pipeline_mode", "degraded",
            "model_path", "model_sha256", "expected_model_sha256",
            "decision_threshold", "decision_threshold_matches_frozen",
        ):
            self.assertIn(key, r)

    def test_13_is_loaded_iff_status_is_loaded_verified(self):
        r = self.detector.status_report()
        self.assertEqual(
            r["is_loaded"],
            r["load_status"] == ModelLoadStatus.LOADED_VERIFIED.value,
        )

    def test_14_pipeline_mode_is_consistent_with_load_state(self):
        r = self.detector.status_report()
        expected = PipelineMode.FULL.value if r["is_loaded"] else PipelineMode.RULE_ONLY.value
        self.assertEqual(r["pipeline_mode"], expected)
        self.assertEqual(r["degraded"], not r["is_loaded"])

    def test_15_threshold_is_frozen_at_038(self):
        r = self.detector.status_report()
        self.assertAlmostEqual(r["decision_threshold"], 0.38, places=9)
        self.assertTrue(r["decision_threshold_matches_frozen"])

    def test_16_load_status_is_a_known_value(self):
        r = self.detector.status_report()
        self.assertIn(r["load_status"], {s.value for s in ModelLoadStatus})

    def test_17_degraded_loader_never_claims_verified_weights(self):
        """If the model did not load, no verified sha may be reported."""
        r = self.detector.status_report()
        if not r["is_loaded"]:
            self.assertNotEqual(
                r["model_sha256"], r["expected_model_sha256"],
                "a degraded loader must not report a verified digest",
            )


class TestHealthAndFailClosed(unittest.TestCase):

    def setUp(self):
        from backend.app import app
        self.client = app.test_client()

    def test_18_health_reports_pipeline_mode_and_model_identity(self):
        d = self.client.get("/health").get_json()
        self.assertIn("pipeline_mode", d)
        self.assertIn("degraded", d)
        self.assertIn("model", d)
        self.assertEqual(d["model"]["expected_model_sha256"], EXPECTED_MODEL_SHA256)
        self.assertIn(d["pipeline_mode"], {PipelineMode.FULL.value, PipelineMode.RULE_ONLY.value})

    def test_19_health_degraded_flag_agrees_with_ml_model_loaded(self):
        d = self.client.get("/health").get_json()
        self.assertEqual(d["degraded"], not d["ml_model_loaded"])

    def test_20_verdict_carries_pipeline_mode(self):
        d = self.client.post("/detect", json={"prompt": "Explain photosynthesis."}).get_json()
        self.assertIn("pipeline_mode", d)
        self.assertIn("ml_degraded", d)
        self.assertIn("ml_load_status", d)

    def test_21_require_ml_refuses_to_serve_a_degraded_verdict(self):
        """
        With REQUIRE_ML enabled, a degraded pipeline must fail closed (503)
        rather than silently answering with rule-only scoring.
        """
        import backend.app as backend_app
        original = backend_app.REQUIRE_ML
        backend_app.REQUIRE_ML = True
        try:
            res = self.client.post("/detect", json={"prompt": "Explain photosynthesis."})
            if backend_app.prompt_engine.ml_detector.is_loaded:
                self.assertEqual(res.status_code, 200,
                                 "a healthy pipeline must still serve under REQUIRE_ML")
            else:
                self.assertEqual(res.status_code, 503)
                body = res.get_json()
                self.assertIn("load_status", body)
                self.assertIn("remediation", body)
        finally:
            backend_app.REQUIRE_ML = original

    def test_22_require_ml_off_by_default_preserves_current_behavior(self):
        import backend.app as backend_app
        self.assertFalse(backend_app.REQUIRE_ML)
        res = self.client.post("/detect", json={"prompt": "Explain photosynthesis."})
        self.assertEqual(res.status_code, 200)


class TestLoadFailureModes(unittest.TestCase):
    """
    Each distinct cause of an unusable model must report its own status.
    Previously every one of these collapsed to a bare `is_loaded = False`.
    """

    def _fresh_detector(self):
        from backend.prompt_security.ml_detector import MLPromptDetector
        return MLPromptDetector()

    def test_23_missing_torch_reports_torch_unavailable(self):
        import backend.prompt_security.ml_detector as md
        original_torch = md.torch
        original_inspect = md.inspect_weights_file
        # Pretend the weights verified so we reach the torch check.
        md.inspect_weights_file = lambda path, expected=None: (None, "stubbed verified", EXPECTED_MODEL_SHA256)
        md.torch = None
        try:
            d = self._fresh_detector()
            self.assertEqual(d.load_status, ModelLoadStatus.TORCH_UNAVAILABLE)
            self.assertFalse(d.is_loaded)
            self.assertEqual(d.pipeline_mode, PipelineMode.RULE_ONLY.value)
        finally:
            md.torch = original_torch
            md.inspect_weights_file = original_inspect

    def test_24_unobtainable_tokenizer_is_distinct_from_weight_failures(self):
        """
        A blocked tokenizer download must NOT be reported the same way as a
        missing or tampered checkpoint.
        """
        import backend.prompt_security.ml_detector as md
        if md.torch is None:
            self.skipTest("torch unavailable; tokenizer path unreachable")
        original_inspect = md.inspect_weights_file
        original_tok = md.DistilBertTokenizer

        class _Boom:
            @staticmethod
            def from_pretrained(*a, **k):
                raise OSError("simulated hub 403")

        md.inspect_weights_file = lambda path, expected=None: (None, "stubbed verified", EXPECTED_MODEL_SHA256)
        md.DistilBertTokenizer = _Boom
        try:
            d = self._fresh_detector()
            self.assertEqual(d.load_status, ModelLoadStatus.TOKENIZER_UNAVAILABLE)
            self.assertFalse(d.is_loaded)
            self.assertIn("simulated hub 403", d.load_detail)
        finally:
            md.inspect_weights_file = original_inspect
            md.DistilBertTokenizer = original_tok

    def test_25_weights_check_precedes_network_dependent_tokenizer(self):
        """
        Ordering guarantee: an unfetched pointer must be reported as
        POINTER_NOT_FETCHED even when the tokenizer would also fail.
        """
        import backend.prompt_security.ml_detector as md
        original_tok = md.DistilBertTokenizer

        class _Boom:
            @staticmethod
            def from_pretrained(*a, **k):
                raise OSError("simulated hub 403")

        md.DistilBertTokenizer = _Boom
        try:
            d = self._fresh_detector()
            if is_lfs_pointer(PROD_MODEL_PATH):
                self.assertEqual(
                    d.load_status, ModelLoadStatus.POINTER_NOT_FETCHED,
                    "weights-file check must run before the tokenizer download",
                )
        finally:
            md.DistilBertTokenizer = original_tok


if __name__ == "__main__":
    unittest.main(verbosity=2)
