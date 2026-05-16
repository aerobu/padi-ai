"""Singleton sentence-embedding service.

Previously `_check_dedup` instantiated `SentenceTransformer('all-MiniLM-L6-v2')`
on every call — a multi-second cold start. This module loads the model once
per process and reuses it.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_MODEL: Any | None = None
_MODEL_NAME = "all-MiniLM-L6-v2"


def get_embedding_model() -> Any:
    """Return the process-singleton sentence-transformers model.

    Raises:
        RuntimeError if `sentence-transformers` isn't installed.
    """
    global _MODEL
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "sentence-transformers not installed; cannot perform embedding-based dedup."
            ) from exc
        logger.info("Loading embedding model: %s", _MODEL_NAME)
        _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


def reset_embedding_model() -> None:
    """Test-only: drop the cached model so reloads work."""
    global _MODEL
    _MODEL = None
