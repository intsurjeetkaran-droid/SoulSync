"""
SoulSync AI - Embedder
Converts text into vector embeddings using sentence-transformers.
Model: all-MiniLM-L6-v2 (fast, lightweight, 384 dimensions)
Loaded lazily on first use to reduce startup memory usage.
"""

import numpy as np
import logging

logger = logging.getLogger("soulsync.embedder")

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM    = 384

# ─── Lazy model holder ────────────────────────────────────
_embed_model = None

def _get_model():
    """Load the embedding model on first use (lazy load)."""
    global _embed_model
    if _embed_model is None:
        logger.info(f"[Embedder] Loading model: {EMBED_MODEL_NAME} ...")
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        logger.info(f"[Embedder] Ready. Dimension: {EMBEDDING_DIM}")
    return _embed_model


def embed_text(text: str) -> np.ndarray:
    """
    Convert a single text string into a 384-dim float32 vector.
    """
    vector = _get_model().encode(text, convert_to_numpy=True)
    return vector.astype(np.float32)


def embed_batch(texts: list) -> np.ndarray:
    """
    Convert a list of texts into a 2D array of embeddings.
    """
    vectors = _get_model().encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return vectors.astype(np.float32)
