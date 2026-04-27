"""Mask gate behavior tests."""

import numpy as np

from face_mask import mask_gate


def test_mask_gate_disabled_allows_attendance(monkeypatch):
    monkeypatch.setattr(mask_gate, "ATTENDANCE_MASK_CHECK_ENABLED", False)

    allowed, message, details = mask_gate.check_face_uncovered_for_attendance(
        np.zeros((32, 32, 3), dtype=np.uint8)
    )

    assert allowed is True
    assert "disabled" in message.lower()
    assert details["skipped"] is True


def test_mask_label_blocks_attendance(monkeypatch):
    monkeypatch.setattr(mask_gate, "ATTENDANCE_MASK_CHECK_ENABLED", True)
    monkeypatch.setattr(
        mask_gate,
        "_classify_with_fallback",
        lambda _image: ("MASK", 0.93, {"backend": "heuristic"}),
    )

    allowed, message, details = mask_gate.check_face_uncovered_for_attendance(
        np.zeros((32, 32, 3), dtype=np.uint8)
    )

    assert allowed is False
    assert "mask detected" in message.lower()
    assert details["label"] == "MASK"


def test_uncertain_blocks_when_configured(monkeypatch):
    monkeypatch.setattr(mask_gate, "ATTENDANCE_MASK_CHECK_ENABLED", True)
    monkeypatch.setattr(mask_gate, "MASK_BLOCK_UNCERTAIN", True)
    monkeypatch.setattr(
        mask_gate,
        "_classify_with_fallback",
        lambda _image: ("UNCERTAIN", 0.4, {"backend": "heuristic"}),
    )

    allowed, message, _details = mask_gate.check_face_uncovered_for_attendance(
        np.zeros((32, 32, 3), dtype=np.uint8)
    )

    assert allowed is False
    assert "could not confirm" in message.lower()


def test_uncertain_allows_when_configured(monkeypatch):
    monkeypatch.setattr(mask_gate, "ATTENDANCE_MASK_CHECK_ENABLED", True)
    monkeypatch.setattr(mask_gate, "MASK_BLOCK_UNCERTAIN", False)
    monkeypatch.setattr(
        mask_gate,
        "_classify_with_fallback",
        lambda _image: ("UNCERTAIN", 0.4, {"backend": "heuristic"}),
    )

    allowed, message, _details = mask_gate.check_face_uncovered_for_attendance(
        np.zeros((32, 32, 3), dtype=np.uint8)
    )

    assert allowed is True
    assert "uncertain" in message.lower()
