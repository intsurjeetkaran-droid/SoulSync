"""
SoulSync AI - Embedder
Converts text into vector embeddings using sentence-transformers.
Model: all-MiniLM-L6-v2 (fast, lightweight, 384 dimensions)
Loaded once and reused across all requests.
"""

from sentence_transformers import SentenceTransformer
import numpy as np

# ─── Load Embedding Model (once) ──────────────────────────
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
print(f"[Embedder] Loading embedding model: {EMBED_MODEL_NAME} ...")
embed_model = SentenceTransformer(EMBED_MODEL_NAME)
EMBEDDING_DIM = 384
print(f"[Embedder] Ready. Dimension: {EMBEDDING_DIM}")


def embed_text(text: str) -> np.ndarray:
    """
    Convert a single text string into a 384-dim float32 vector.

    Args:
        text: input string

    Returns:
        numpy array of shape (384,) dtype float32
    """
    vector = embed_model.encode(text, convert_to_numpy=True)
    return vector.astype(np.float32)


def embed_batch(texts: list) -> np.ndarray:
    """
    Convert a list of texts into a 2D array of embeddings.

    Args:
        texts: list of strings

    Returns:
        numpy array of shape (N, 384) dtype float32
    """
    vectors = embed_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return vectors.astype(np.float32)
