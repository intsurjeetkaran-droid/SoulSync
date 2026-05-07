"""
SoulSync AI - Text Embedder
============================

Converts text into vector embeddings using sentence-transformers.
This module provides the semantic understanding capability for the RAG system.

Model Details:
    - Model: all-MiniLM-L6-v2
    - Dimensions: 384
    - Language: Multilingual (supports English, Hindi, Hinglish, etc.)
    - Size: ~90MB (downloaded on first use)
    - Speed: ~15ms per embedding on CPU
    - Quality: Good balance of speed and accuracy for semantic search

Features:
    - Lazy loading: Model is loaded on first use to reduce startup memory
    - Batch processing: Efficient batch embedding for multiple texts
    - Consistent output: Always returns float32 numpy arrays

Usage:
    >>> from backend.retrieval.embedder import embed_text, embed_batch
    >>> vector = embed_text("I love coding")  # Single text
    >>> vectors = embed_batch(["Hello", "World"])  # Batch
"""

import logging
from typing import List, Union

import numpy as np

logger = logging.getLogger("soulsync.embedder")

# ─── Model Configuration ──────────────────────────────────────────────

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
"""
Name of the sentence-transformers model to use.
all-MiniLM-L6-v2 is a lightweight, fast model that works well for:
- Semantic similarity search
- Text classification
- Clustering
- Supports 50+ languages including English and Hindi
"""

EMBEDDING_DIM = 384
"""Dimension of the output embedding vectors."""


# ─── Lazy Model Holder ────────────────────────────────────────────────

_embed_model = None
"""Module-level singleton for the embedding model (lazy loaded)."""


def _get_model():
    """
    Load the embedding model on first use (lazy loading pattern).
    
    This function ensures the model is only loaded when needed,
    reducing startup time and memory usage if embeddings aren't used.
    
    Returns:
        SentenceTransformer model instance
        
    Note:
        The model is downloaded automatically on first use if not present.
        Subsequent calls reuse the loaded model (singleton pattern).
    """
    global _embed_model
    if _embed_model is None:
        logger.info(f"[Embedder] Loading model: {EMBED_MODEL_NAME}...")
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
            logger.info(f"[Embedder] Model loaded successfully. Dimensions: {EMBEDDING_DIM}")
            logger.debug(f"[Embedder] Model device: {_embed_model.device}")
        except Exception as e:
            logger.error(f"[Embedder] Failed to load model: {e}")
            raise RuntimeError(
                f"Failed to load embedding model '{EMBED_MODEL_NAME}'. "
                "Make sure sentence-transformers is installed: pip install sentence-transformers"
            ) from e
    return _embed_model


def embed_text(text: str) -> np.ndarray:
    """
    Convert a single text string into a 384-dimensional float32 vector.
    
    This function encodes the input text using the sentence-transformers model
    and returns a normalized embedding vector suitable for semantic similarity
    search with FAISS.
    
    Args:
        text: The text string to embed (any language supported by the model)
            
    Returns:
        numpy.ndarray of shape (384,) with dtype float32
        The vector represents the semantic meaning of the text
        
    Example:
        >>> vector = embed_text("I feel happy today")
        >>> print(vector.shape)  # (384,)
        >>> print(vector.dtype)  # float32
        
    Note:
        - Empty strings return a zero vector
        - Very long texts (>512 tokens) may be truncated by the model
        - The model is multilingual and handles Hindi/Hinglish well
    """
    if not text or not text.strip():
        logger.debug("[Embedder] Empty text provided, returning zero vector")
        return np.zeros(EMBEDDING_DIM, dtype=np.float32)
    
    try:
        model = _get_model()
        vector = model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,  # L2 normalization for cosine similarity
        )
        # Ensure consistent dtype
        vector = vector.astype(np.float32)
        
        logger.debug(f"[Embedder] Embedded text: '{text[:30]}...' → shape={vector.shape}")
        return vector
        
    except Exception as e:
        logger.error(f"[Embedder] Failed to embed text: {e}")
        # Return zero vector on failure (graceful degradation)
        return np.zeros(EMBEDDING_DIM, dtype=np.float32)


def embed_batch(texts: List[str]) -> np.ndarray:
    """
    Convert a list of texts into a 2D array of embeddings.
    
    This function is more efficient than calling embed_text() in a loop
    because the model can process multiple texts in parallel.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        numpy.ndarray of shape (N, 384) with dtype float32
        where N is the number of input texts
        
    Example:
        >>> texts = ["Hello world", "How are you?", "Goodbye"]
        >>> vectors = embed_batch(texts)
        >>> print(vectors.shape)  # (3, 384)
        
    Note:
        - Empty list returns empty array with shape (0, 384)
        - None values in the list are treated as empty strings
        - All texts are processed in a single batch for efficiency
    """
    if not texts:
        logger.debug("[Embedder] Empty batch provided, returning empty array")
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)
    
    try:
        model = _get_model()
        
        # Preprocess: replace None with empty string
        clean_texts = [t if t is not None else "" for t in texts]
        
        vectors = model.encode(
            clean_texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,  # L2 normalization
            batch_size=32,  # Process in batches of 32
        )
        
        # Ensure consistent dtype and shape
        vectors = vectors.astype(np.float32)
        
        logger.debug(f"[Embedder] Batch embedded {len(texts)} texts → shape={vectors.shape}")
        return vectors
        
    except Exception as e:
        logger.error(f"[Embedder] Batch embedding failed: {e}")
        # Return empty array on failure
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)


def get_embedding_info() -> dict:
    """
    Get information about the embedding model and configuration.
    
    Returns:
        Dictionary with model details:
        - model_name: Name of the model
        - dimensions: Vector dimension
        - loaded: Whether the model is currently loaded in memory
        - device: Device the model is running on (cpu/cuda)
    """
    info = {
        "model_name": EMBED_MODEL_NAME,
        "dimensions": EMBEDDING_DIM,
        "loaded": _embed_model is not None,
        "device": str(_embed_model.device) if _embed_model else "not_loaded",
    }
    return info