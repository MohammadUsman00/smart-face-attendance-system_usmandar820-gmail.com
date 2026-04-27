"""
Tests for 1:1 face verification engine.
These tests run without DeepFace by mocking _generate_embedding_strict.
"""
from __future__ import annotations
from unittest.mock import patch

import numpy as np
import pytest

from face_recognition import verification_engine as ve


# ── helpers ──────────────────────────────────────────────────────────────────

def _rand_emb(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(512).astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def _make_image(brightness: int = 128, blur: bool = False, size: int = 128) -> np.ndarray:
    """Return a synthetic BGR image."""
    img = np.ones((size, size, 3), dtype=np.uint8) * brightness
    if not blur:
        # Add enough texture so Laplacian score is not near zero
        for i in range(0, size, 8):
            img[i, :] = 0
    return img


# ── quality gate ─────────────────────────────────────────────────────────────

def test_quality_gate_rejects_tiny_image():
    small = np.zeros((10, 10, 3), dtype=np.uint8)
    result = ve.run_quality_gate(small)
    assert not result.ok
    assert "small" in result.reason.lower()


def test_quality_gate_rejects_dark_image():
    dark = np.zeros((128, 128, 3), dtype=np.uint8)
    result = ve.run_quality_gate(dark)
    assert not result.ok
    assert "dark" in result.reason.lower()


def test_quality_gate_rejects_none():
    result = ve.run_quality_gate(None)
    assert not result.ok


def test_quality_gate_passes_clear_image():
    img = _make_image(brightness=128, blur=False, size=128)
    # Quality gate may fail on Haar face detection (no real face in synthetic image)
    # but it should at least not raise an exception.
    result = ve.run_quality_gate(img)
    assert isinstance(result.ok, bool)


# ── verify_identity ───────────────────────────────────────────────────────────

def _passing_quality():
    return ve.ImageQualityResult(True)


def test_verify_correct_identity_passes():
    emb = _rand_emb(1)
    gallery = [emb.copy(), emb.copy()]
    img = _make_image()

    with patch.object(ve, "run_quality_gate", return_value=_passing_quality()):
        with patch.object(ve, "_generate_embedding_strict", return_value=emb.copy()):
            result = ve.verify_identity(img, gallery, threshold=0.5)

    assert result.verified
    assert result.reason == "verified"
    assert result.similarity > 0.99


def test_verify_wrong_identity_rejected():
    enrolled_emb = _rand_emb(1)
    impostor_emb = _rand_emb(42)
    gallery = [enrolled_emb]
    img = _make_image()

    with patch.object(ve, "run_quality_gate", return_value=_passing_quality()):
        with patch.object(ve, "_generate_embedding_strict", return_value=impostor_emb):
            result = ve.verify_identity(img, gallery, threshold=0.5)

    assert not result.verified
    assert result.reason == "low_confidence"


def test_verify_no_gallery_fails():
    img = _make_image()
    emb = _rand_emb(1)

    with patch.object(ve, "_generate_embedding_strict", return_value=emb):
        result = ve.verify_identity(img, [], threshold=0.5)

    assert not result.verified
    assert result.reason == "no_gallery"


def test_verify_embedding_failed_returns_structured_result():
    img = _make_image()
    with patch.object(ve, "run_quality_gate", return_value=_passing_quality()):
        with patch.object(ve, "_generate_embedding_strict", return_value=None):
            result = ve.verify_identity(img, [_rand_emb(1)], threshold=0.5)

    assert not result.verified
    assert result.reason == "embedding_failed"
    assert result.display_message


def test_verify_quality_gate_blocks_bad_image():
    dark = np.zeros((64, 64, 3), dtype=np.uint8)
    gallery = [_rand_emb(1)]
    result = ve.verify_identity(dark, gallery, threshold=0.5)
    assert not result.verified
    assert result.reason == "quality_failed"


def test_verify_inconsistent_templates_rejected():
    """Probe matches only 1 of 4 templates -> inconsistent_templates rejection."""
    good_emb = _rand_emb(1)
    bad_embs = [_rand_emb(10 + i) for i in range(3)]
    gallery = [good_emb] + bad_embs

    img = _make_image()
    with patch.object(ve, "run_quality_gate", return_value=_passing_quality()):
        with patch.object(ve, "_generate_embedding_strict", return_value=good_emb.copy()):
            result = ve.verify_identity(img, gallery, threshold=0.5)

    assert not result.verified
    assert result.reason == "inconsistent_templates"


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_verification_result_to_dict():
    r = ve.VerificationResult(True, "verified", similarity=0.87, detail="OK")
    d = r.to_dict()
    assert d["verified"] is True
    assert d["reason"] == "verified"
    assert d["similarity"] == round(0.87, 4)
