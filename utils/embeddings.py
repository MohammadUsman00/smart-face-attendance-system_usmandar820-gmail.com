"""
Embedding cache utilities.

Stores and loads face embeddings to a fast on-disk cache file (embeddings.npy)
to speed up recognition, while keeping the SQLite database as the source of truth.
"""

from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np

from config.settings import BASE_DIR, EMBEDDING_SIZE
from utils.face_utils import ensure_dir_exists

# Cache file location: data/embeddings.npy
EMBEDDINGS_FILE: Path = BASE_DIR / "data" / "embeddings.npy"


def get_cache_path() -> Path:
    """Return the path to the embeddings cache file."""
    return EMBEDDINGS_FILE


def save_embeddings_cache(student_embeddings: List[Tuple[int, str, str, np.ndarray]]) -> Path:
    """
    Persist student embeddings to embeddings.npy.

    The cache format is a NumPy object array of dicts:
    {
        "student_id": int,
        "name": str,
        "roll_number": str,
        "embedding": np.ndarray (float32, length EMBEDDING_SIZE)
    }
    """
    ensure_dir_exists(EMBEDDINGS_FILE.parent)

    records = []
    for student_id, name, roll_number, embedding in student_embeddings:
        # Ensure ndarray and correct dtype/size
        emb_arr = np.asarray(embedding, dtype=np.float32)
        if emb_arr.shape[0] != EMBEDDING_SIZE:
            # Pad or truncate to expected size, without mutating original
            fixed = np.zeros(EMBEDDING_SIZE, dtype=np.float32)
            size = min(EMBEDDING_SIZE, emb_arr.shape[0])
            fixed[:size] = emb_arr[:size]
            emb_arr = fixed

        records.append(
            {
                "student_id": int(student_id),
                "name": str(name),
                "roll_number": str(roll_number),
                "embedding": emb_arr,
            }
        )

    # Store as a 1D object array of dicts for flexibility
    np.save(EMBEDDINGS_FILE, np.array(records, dtype=object))
    return EMBEDDINGS_FILE


def load_embeddings_cache() -> Optional[List[Tuple[int, str, str, np.ndarray]]]:
    """
    Load embeddings from embeddings.npy, if available.

    Returns a list of (student_id, name, roll_number, embedding) tuples,
    or None if the cache file does not exist or is invalid.
    """
    if not EMBEDDINGS_FILE.exists():
        return None

    try:
        # This requires allow_pickle=True because we stored dict objects.
        raw = np.load(EMBEDDINGS_FILE, allow_pickle=True)
        student_embeddings: List[Tuple[int, str, str, np.ndarray]] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            emb = np.asarray(item.get("embedding"), dtype=np.float32)
            if emb.shape[0] != EMBEDDING_SIZE:
                fixed = np.zeros(EMBEDDING_SIZE, dtype=np.float32)
                size = min(EMBEDDING_SIZE, emb.shape[0])
                fixed[:size] = emb[:size]
                emb = fixed

            student_embeddings.append(
                (
                    int(item.get("student_id")),
                    str(item.get("name")),
                    str(item.get("roll_number")),
                    emb,
                )
            )

        return student_embeddings

    except Exception:
        # If anything goes wrong, treat cache as unavailable
        return None


def clear_embeddings_cache() -> None:
    """Remove the embeddings cache file if it exists."""
    try:
        if EMBEDDINGS_FILE.exists():
            EMBEDDINGS_FILE.unlink()
    except Exception:
        # Fail silently – cache is an optimization, not critical
        pass

