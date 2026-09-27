"""
model_integrity.py
Integrity verification and load-state reporting for the frozen production
prompt-injection classifier.

The production model is FROZEN. This module is the enforcement point for that
guarantee: it verifies the on-disk weights against a pinned SHA256 before they
are ever handed to torch, and it reports a precise, machine-readable reason
whenever the model cannot be loaded.

Rationale: the previous loader treated every failure identically (a bare
``except`` that set ``is_loaded = False``), so an unfetched Git LFS pointer, a
blocked tokenizer download, a missing torch install and a tampered checkpoint
were indistinguishable. The pipeline then silently degraded to rule-only
scoring with no operator-visible signal.
"""

import hashlib
import os
from enum import Enum
from typing import Optional, Tuple

# -------------------------------------------------------------------------
# Pinned production model identity. DO NOT EDIT without an explicit,
# documented model-change approval: these constants are what make the
# "model is frozen" guarantee verifiable rather than aspirational.
# -------------------------------------------------------------------------
EXPECTED_MODEL_SHA256 = "a487e0be9008f2e55d44b4a025b2449cf77c94f53ed5582b3cebeee206e4a850"
EXPECTED_MODEL_SIZE_BYTES = 267856473
FROZEN_DECISION_THRESHOLD = 0.38

# Git LFS pointer files are small UTF-8 text stubs that begin with this line.
LFS_POINTER_MAGIC = b"version https://git-lfs.github.com/spec/v1"
LFS_POINTER_MAX_BYTES = 1024


class ModelLoadStatus(str, Enum):
    """Precise reason describing the state of the production model."""

    LOADED_VERIFIED = "LOADED_VERIFIED"
    FILE_MISSING = "FILE_MISSING"
    POINTER_NOT_FETCHED = "POINTER_NOT_FETCHED"
    POINTER_WRONG_MODEL = "POINTER_WRONG_MODEL"
    HASH_MISMATCH = "HASH_MISMATCH"
    TORCH_UNAVAILABLE = "TORCH_UNAVAILABLE"
    TOKENIZER_UNAVAILABLE = "TOKENIZER_UNAVAILABLE"
    LOAD_ERROR = "LOAD_ERROR"


class PipelineMode(str, Enum):
    """Which detection layers actually contributed to a verdict."""

    FULL = "FULL"            # rule engine + verified ML classifier
    RULE_ONLY = "RULE_ONLY"  # rule engine alone; ML did not participate


def is_lfs_pointer(path: str) -> bool:
    """True if ``path`` is an unfetched Git LFS pointer stub rather than weights."""
    try:
        if os.path.getsize(path) > LFS_POINTER_MAX_BYTES:
            return False
        with open(path, "rb") as f:
            return f.read(len(LFS_POINTER_MAGIC)) == LFS_POINTER_MAGIC
    except OSError:
        return False


def parse_lfs_pointer(path: str) -> Tuple[Optional[str], Optional[int]]:
    """Extracts ``(oid_sha256, size_bytes)`` from an LFS pointer stub."""
    oid, size = None, None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line.startswith("oid sha256:"):
                    oid = line.split("oid sha256:", 1)[1].strip()
                elif line.startswith("size "):
                    try:
                        size = int(line.split("size ", 1)[1].strip())
                    except ValueError:
                        size = None
    except OSError:
        return None, None
    return oid, size


def sha256_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    """Streaming SHA256 of a file, safe for large checkpoints."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_weights_file(
    path: str,
    expected_sha256: str = EXPECTED_MODEL_SHA256,
) -> Tuple[Optional[ModelLoadStatus], str, Optional[str]]:
    """
    Validates the weights file on disk WITHOUT importing torch or touching the
    network. Runs before any download so a blocked tokenizer cannot mask a
    missing or tampered checkpoint.

    Returns ``(blocking_status, detail, sha256)``. ``blocking_status`` is None
    when the file is genuine, verified weights and loading may proceed.
    """
    if not os.path.exists(path):
        return (
            ModelLoadStatus.FILE_MISSING,
            f"No model file at {path}.",
            None,
        )

    if is_lfs_pointer(path):
        oid, size = parse_lfs_pointer(path)
        if oid and oid.lower() != expected_sha256.lower():
            return (
                ModelLoadStatus.POINTER_WRONG_MODEL,
                (
                    f"Git LFS pointer references oid {oid}, which is not the pinned "
                    f"production model {expected_sha256}."
                ),
                None,
            )
        return (
            ModelLoadStatus.POINTER_NOT_FETCHED,
            (
                "Model weights are an unfetched Git LFS pointer "
                f"({os.path.getsize(path)} bytes on disk, expected {size or EXPECTED_MODEL_SIZE_BYTES}). "
                "Run 'git lfs install && git lfs pull' to fetch the real weights."
            ),
            None,
        )

    actual = sha256_file(path)
    if actual.lower() != expected_sha256.lower():
        return (
            ModelLoadStatus.HASH_MISMATCH,
            (
                f"Model SHA256 {actual} does not match the pinned production model "
                f"{expected_sha256}. Refusing to load: the frozen model may have been "
                "replaced, retrained or corrupted."
            ),
            actual,
        )

    return (None, "Model weights verified against the pinned production SHA256.", actual)
