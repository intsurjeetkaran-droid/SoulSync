"""
SoulSync AI - Vector Store
Manages per-user FAISS indexes on disk.

Each user gets their own FAISS index file:
  data/vectors/{user_id}.index
  data/vectors/{user_id}.meta.json   ← stores original texts

Flow:
  add_memory()   → embed text → add to FAISS → save to disk
  search()       → embed query → search FAISS → return top-K texts
"""

import os
import json
import numpy as np
import faiss

from backend.retrieval.embedder import embed_text, embed_batch, EMBEDDING_DIM

# ─── Storage Path ─────────────────────────────────────────
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/vectors"))
os.makedirs(BASE_DIR, exist_ok=True)


def _index_path(user_id: str) -> str:
    return os.path.join(BASE_DIR, f"{user_id}.index")

def _meta_path(user_id: str) -> str:
    return os.path.join(BASE_DIR, f"{user_id}.meta.json")


# ─── Load or Create Index ─────────────────────────────────

def _load_index(user_id: str):
    """Load existing FAISS index from disk, or create a new one."""
    path = _index_path(user_id)
    if os.path.exists(path):
        return faiss.read_index(path)
    # Create new flat L2 index
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    return index


def _load_meta(user_id: str) -> list:
    """Load metadata (original texts) from disk."""
    path = _meta_path(user_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_index(user_id: str, index):
    """Save FAISS index to disk."""
    faiss.write_index(index, _index_path(user_id))


def _save_meta(user_id: str, meta: list):
    """Save metadata to disk."""
    with open(_meta_path(user_id), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


# ─── Public API ───────────────────────────────────────────

def add_memory(user_id: str, text: str):
    """
    Embed a text and add it to the user's FAISS index.

    Args:
        user_id : unique user identifier
        text    : memory text to store
    """
    index = _load_index(user_id)
    meta  = _load_meta(user_id)

    vector = embed_text(text).reshape(1, -1)  # shape (1, 384)
    index.add(vector)
    meta.append(text)

    _save_index(user_id, index)
    _save_meta(user_id, meta)


def add_memories_batch(user_id: str, texts: list):
    """
    Add multiple texts to the user's FAISS index at once.
    More efficient than calling add_memory() in a loop.
    """
    if not texts:
        return

    index   = _load_index(user_id)
    meta    = _load_meta(user_id)
    vectors = embed_batch(texts)  # shape (N, 384)

    index.add(vectors)
    meta.extend(texts)

    _save_index(user_id, index)
    _save_meta(user_id, meta)


def search_memory(user_id: str, query: str, top_k: int = 3,
                  max_distance: float = 1.2) -> list:
    """
    Find the top-K most semantically similar memories to the query.
    Filters out results with distance > max_distance (irrelevant memories).

    Args:
        user_id      : unique user identifier
        query        : the search query (current user message)
        top_k        : number of results to return
        max_distance : L2 distance threshold — results above this are dropped
                       (lower = more similar; 0.0 = identical)

    Returns:
        List of {text, score} dicts, sorted by relevance
    """
    index = _load_index(user_id)
    meta  = _load_meta(user_id)

    if index.ntotal == 0:
        return []  # no memories yet

    query_vector = embed_text(query).reshape(1, -1)
    top_k = min(top_k, index.ntotal)

    distances, indices = index.search(query_vector, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(meta) and float(dist) <= max_distance:
            results.append({
                "text":  meta[idx],
                "score": float(dist)   # lower = more similar
            })

    return results


def get_memory_count(user_id: str) -> int:
    """Return total number of vectors stored for a user."""
    index = _load_index(user_id)
    return index.ntotal
