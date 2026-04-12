"""
Attendance gate: block marking when a face covering is detected or uncertain.
Prefers Ultralytics YOLO-World when available; falls back to OpenCV heuristics.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

import numpy as np

from config.settings import (
    ATTENDANCE_MASK_CHECK_ENABLED,
    MASK_BLOCK_UNCERTAIN,
    MASK_USE_YOLO,
)
from face_mask.mask_detector_rt import RealtimeMaskDetector

logger = logging.getLogger(__name__)


def _classify_with_fallback(image_bgr: np.ndarray) -> Tuple[str, float, Dict[str, Any]]:
    """YOLO first (if enabled), then heuristic detector."""
    details: Dict[str, Any] = {}

    if MASK_USE_YOLO:
        try:
            from face_mask.yolo_mask_detector import classify_image_yolo, is_yolo_mask_available

            if is_yolo_mask_available():
                label, conf, ydbg = classify_image_yolo(image_bgr)
                details["backend"] = "yolo_world"
                details.update(ydbg)
                return label, conf, details
            details["yolo_skipped"] = "model_unavailable"
        except Exception as e:
            logger.warning("YOLO mask check failed, using heuristic: %s", e)
            details["yolo_error"] = str(e)

    det = RealtimeMaskDetector(strict_attendance=True)
    label, conf, dbg = det.classify_image_best_face(image_bgr)
    details["backend"] = "heuristic"
    details["scores"] = dbg
    return label, conf, details


def check_face_uncovered_for_attendance(
    image_bgr: np.ndarray,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Returns (allowed_to_mark_attendance, message, details).

    When `MASK_BLOCK_UNCERTAIN` is True (default), UNCERTAIN also blocks
    attendance so users must show a clearly uncovered face.
    """
    if not ATTENDANCE_MASK_CHECK_ENABLED:
        return True, "Mask check disabled.", {"skipped": True}

    if image_bgr is None or not isinstance(image_bgr, np.ndarray) or image_bgr.size == 0:
        return False, "Invalid image. Please capture or upload again.", {}

    label, conf, details = _classify_with_fallback(image_bgr)
    details["label"] = label

    if details.get("backend") == "yolo_world" and details.get("num_boxes") == 0:
        return (
            False,
            "Could not clearly see your face in this photo. Face the camera, use good lighting, and try again.",
            details,
        )

    if details.get("backend") == "heuristic" and details.get("scores", {}).get("error") == "no_face":
        return (
            False,
            "No face detected. Center your face in the frame, use good lighting, and try again.",
            details,
        )

    if label == "MASK":
        return (
            False,
            "Face mask detected. Please remove your mask so your face is visible, then take the photo again.",
            details,
        )

    if label == "UNCERTAIN":
        if MASK_BLOCK_UNCERTAIN:
            return (
                False,
                "Could not confirm your face is uncovered. Remove any mask, use bright lighting, face the camera, and try again.",
                details,
            )
        return True, "Proceeding with uncertain mask check (configured to allow).", details

    if label == "NO MASK":
        return (
            True,
            "Face covering check passed.",
            details,
        )

    return False, "Could not verify face. Please try again with a clear frontal photo.", details
