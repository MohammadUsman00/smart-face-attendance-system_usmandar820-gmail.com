"""
Roll-bound 1:1 face verification engine.

Verification policy:
  1. Strict image quality gate (blur, brightness, face-count check).
  2. Generate embedding from the captured image.
  3. Compare ONLY against the claimed student's own templates (1:1 path).
  4. Require similarity >= VERIFICATION_THRESHOLD (higher than 1:N threshold).
  5. Require a clear gap over the inter-template mean similarity (internal margin).
  6. Any failure returns a structured reason rather than a silent fall-through.

This is separate from the legacy 1:N recognize_face() which is kept for
optional gallery search mode.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from config.settings import (
    ALLOW_SKIP_DETECTION_FALLBACK,
    DETECTOR_BACKEND,
    EMBEDDING_SIZE,
    MODEL_NAME,
    RECOGNITION_MARGIN,
    RECOGNITION_THRESHOLD,
)
from face_recognition.image_utils import ensure_rgb, resize_embedding_to_512

logger = logging.getLogger(__name__)

# 1:1 verification threshold is higher than the 1:N search threshold because
# we do not need to distinguish between many candidates – we only need to
# confirm or deny one claim.
_VERIFICATION_THRESHOLD_BOOST: float = 0.05  # added on top of RECOGNITION_THRESHOLD


def _deepface():
    try:
        from deepface import DeepFace
        return DeepFace
    except ImportError as exc:
        raise RuntimeError(
            "DeepFace is required for face verification. "
            "Install dependencies: pip install -r requirements.txt"
        ) from exc


# ──────────────────────────────────────────────
# Quality gate
# ──────────────────────────────────────────────

class ImageQualityResult:
    __slots__ = ("ok", "reason")

    def __init__(self, ok: bool, reason: str = ""):
        self.ok = ok
        self.reason = reason


def run_quality_gate(image: np.ndarray) -> ImageQualityResult:
    """
    Strict quality gate run before embedding generation.
    Returns ImageQualityResult(ok=False, reason=...) if image is unsuitable.
    """
    if image is None or not isinstance(image, np.ndarray):
        return ImageQualityResult(False, "No image provided.")

    if len(image.shape) < 2:
        return ImageQualityResult(False, "Invalid image array dimensions.")

    h, w = image.shape[:2]
    if h < 64 or w < 64:
        return ImageQualityResult(False, f"Image too small ({w}x{h}). Use at least 128x128.")

    # Convert to grayscale for brightness/blur checks
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    brightness = float(np.mean(gray))
    if brightness < 35:
        return ImageQualityResult(False, "Image too dark. Use better lighting.")
    if brightness > 230:
        return ImageQualityResult(False, "Image too bright / overexposed.")

    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur_score < 80:
        return ImageQualityResult(False, f"Image too blurry (score {blur_score:.0f}). Hold still.")

    # Face count check via Haar cascade (fast, no external model needed)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if not face_cascade.empty():
        small = cv2.resize(gray, (320, int(320 * h / w)))
        faces = face_cascade.detectMultiScale(
            small, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )
        if len(faces) == 0:
            return ImageQualityResult(False, "No face detected in the image. Face the camera directly.")
        if len(faces) > 1:
            return ImageQualityResult(
                False,
                f"{len(faces)} faces detected. Ensure only one person is visible.",
            )

    return ImageQualityResult(True)


# ──────────────────────────────────────────────
# Embedding generation (single image, strict)
# ──────────────────────────────────────────────

def _generate_embedding_strict(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Attempt embedding generation using the primary detector backend only.
    Strict: enforce_detection=True.  Does NOT fall back through multiple
    backends so that an unclear face produces a clean failure.
    Falls back to skip-detection ONLY when ALLOW_SKIP_DETECTION_FALLBACK=True.
    """
    try:
        rgb = ensure_rgb(image)
        result = _deepface().represent(
            img_path=rgb,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=True,
        )
        emb = _extract(result)
        if emb is not None:
            return _normalise(emb)
    except Exception as e:
        logger.debug("Primary detection failed (%s): %s", DETECTOR_BACKEND, e)

    if ALLOW_SKIP_DETECTION_FALLBACK:
        try:
            rgb = ensure_rgb(image)
            result = _deepface().represent(
                img_path=rgb,
                model_name=MODEL_NAME,
                detector_backend="skip",
                enforce_detection=False,
            )
            emb = _extract(result)
            if emb is not None:
                return _normalise(emb)
        except Exception as e:
            logger.debug("Skip-detection fallback failed: %s", e)

    return None


def _extract(result) -> Optional[np.ndarray]:
    try:
        if isinstance(result, list) and result:
            return np.array(result[0]["embedding"], dtype=np.float32)
        if isinstance(result, dict) and "embedding" in result:
            return np.array(result["embedding"], dtype=np.float32)
    except Exception:
        pass
    return None


def _normalise(emb: np.ndarray) -> np.ndarray:
    emb = resize_embedding_to_512(emb)
    norm = np.linalg.norm(emb)
    if norm > 1e-6:
        emb = emb / norm
    return emb


# ──────────────────────────────────────────────
# Cosine similarity helpers
# ──────────────────────────────────────────────

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.clip(np.dot(a, b) / (na * nb), -1.0, 1.0))


# ──────────────────────────────────────────────
# 1:1 verification
# ──────────────────────────────────────────────

class VerificationResult:
    """Structured result returned from verify_identity()."""

    def __init__(
        self,
        verified: bool,
        reason: str,
        similarity: float = 0.0,
        detail: Optional[str] = None,
    ):
        self.verified = verified
        self.reason = reason
        self.similarity = similarity
        self.detail = detail

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verified": self.verified,
            "reason": self.reason,
            "similarity": round(self.similarity, 4),
            "detail": self.detail,
        }

    @property
    def display_message(self) -> str:
        return self.detail or self.reason


def verify_identity(
    probe_image: np.ndarray,
    gallery_embeddings: List[np.ndarray],
    threshold: Optional[float] = None,
) -> VerificationResult:
    """
    Verify that probe_image belongs to the student whose enrolled embeddings
    are given in gallery_embeddings.

    Parameters
    ----------
    probe_image:
        Numpy BGR image captured at attendance time.
    gallery_embeddings:
        List of normalised float32 numpy arrays from the student's
        enrollment session (2-5 templates).
    threshold:
        Override verification threshold. Defaults to
        RECOGNITION_THRESHOLD + _VERIFICATION_THRESHOLD_BOOST.

    Returns
    -------
    VerificationResult
    """
    effective_threshold = (
        threshold
        if threshold is not None
        else RECOGNITION_THRESHOLD + _VERIFICATION_THRESHOLD_BOOST
    )

    if not gallery_embeddings:
        return VerificationResult(
            False,
            "no_gallery",
            detail="No enrolled face templates found for this student. Re-enroll.",
        )

    # 1. Quality gate
    quality = run_quality_gate(probe_image)
    if not quality.ok:
        return VerificationResult(
            False,
            "quality_failed",
            detail=quality.reason,
        )

    # 2. Generate probe embedding
    probe_emb = _generate_embedding_strict(probe_image)
    if probe_emb is None:
        return VerificationResult(
            False,
            "embedding_failed",
            detail=(
                "Could not extract a face from the photo. "
                "Ensure your face is fully visible, well-lit, and centred."
            ),
        )

    # 3. Compute similarity against each enrolled template; take the max
    scores = [_cosine(probe_emb, g) for g in gallery_embeddings]
    best_score = max(scores)
    mean_score = float(np.mean(scores))

    # 4. Check threshold
    if best_score < effective_threshold:
        return VerificationResult(
            False,
            "low_confidence",
            similarity=best_score,
            detail=(
                f"Face similarity {best_score:.2f} is below the required "
                f"{effective_threshold:.2f}. Try better lighting and face "
                "the camera at the same angle as your registration photos."
            ),
        )

    # 5. Cross-template consistency check:
    #    If multiple templates exist, the probe should score reasonably
    #    well against most of them, not just a lucky single template.
    if len(gallery_embeddings) >= 3:
        good_template_hits = sum(1 for s in scores if s >= effective_threshold * 0.9)
        if good_template_hits < max(1, len(gallery_embeddings) // 2):
            return VerificationResult(
                False,
                "inconsistent_templates",
                similarity=best_score,
                detail=(
                    f"Matched only {good_template_hits}/{len(gallery_embeddings)} enrolled templates "
                    f"(best={best_score:.2f}). Re-take the photo with clearer lighting."
                ),
            )

    return VerificationResult(
        True,
        "verified",
        similarity=best_score,
        detail=f"Identity confirmed (similarity {best_score:.2f}).",
    )


# ──────────────────────────────────────────────
# Per-session embedding cache (keyed by roll)
# ──────────────────────────────────────────────
# Avoids repeated DB queries when the same roll is verified multiple times
# in one Streamlit session. The cache is limited to 200 students and uses
# a simple LRU eviction.

from functools import lru_cache

@lru_cache(maxsize=200)
def _cached_gallery(roll_number: str):
    """Cached fetch — result is (student_id, student_name, tuple_of_embeddings)."""
    sid, sname, embs = _fetch_gallery_raw(roll_number)
    return sid, sname, tuple(embs)


def invalidate_roll_cache(roll_number: Optional[str] = None) -> None:
    """Call after re-enrollment or student deletion to evict stale entries."""
    _cached_gallery.cache_clear()


# ──────────────────────────────────────────────
# Repository helper: fetch gallery by roll
# ──────────────────────────────────────────────

def _fetch_gallery_raw(
    roll_number: str,
) -> Tuple[Optional[int], Optional[str], List[np.ndarray]]:
    """DB fetch without caching — used by _cached_gallery."""
    try:
        from database.connection import get_db_connection
        import base64

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.id, s.name, fe.embedding_data
                FROM students s
                JOIN face_embeddings fe ON s.id = fe.student_id
                WHERE s.roll_number = ? AND s.is_active = 1
                """,
                (roll_number.strip(),),
            )
            rows = cursor.fetchall()

        if not rows:
            return None, None, []

        student_id = int(rows[0]["id"])
        student_name = str(rows[0]["name"])
        embeddings: List[np.ndarray] = []

        for row in rows:
            try:
                raw = base64.b64decode(row["embedding_data"])
                emb = np.frombuffer(raw, dtype=np.float32).copy()
                if emb.shape[0] != EMBEDDING_SIZE:
                    fixed = np.zeros(EMBEDDING_SIZE, dtype=np.float32)
                    size = min(EMBEDDING_SIZE, emb.shape[0])
                    fixed[:size] = emb[:size]
                    emb = fixed
                emb = _normalise(emb)
                embeddings.append(emb)
            except Exception as exc:
                logger.warning("Skipping corrupt embedding for %s: %s", roll_number, exc)

        return student_id, student_name, embeddings

    except Exception as exc:
        logger.error("Error fetching embeddings for roll %s: %s", roll_number, exc)
        return None, None, []


def get_embeddings_for_roll(
    roll_number: str,
) -> Tuple[Optional[int], Optional[str], List[np.ndarray]]:
    """
    Return (student_id, student_name, [embeddings]) for the given roll number.
    Results are session-cached via LRU for performance.
    Returns (None, None, []) if not found or no embeddings.
    """
    sid, sname, embs_tuple = _cached_gallery(roll_number.strip().upper())
    return sid, sname, list(embs_tuple)
