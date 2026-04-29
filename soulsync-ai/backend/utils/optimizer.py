"""
SoulSync AI - Optimizer
Previously handled ONNX export for local DialoGPT model.

Local model has been removed. AI is now served via Groq API.
This module is kept as a placeholder for future optimization utilities
(e.g., embedding cache warming, DB query optimization).
"""

import logging

logger = logging.getLogger("soulsync.optimizer")


def noop(*args, **kwargs):
    """No-op placeholder — local model optimization no longer applicable."""
    logger.info("[Optimizer] Local model optimization is disabled (Groq API in use).")
    return None


# Aliases kept for any legacy imports
export_to_onnx = noop
verify_onnx    = noop
benchmark      = noop
