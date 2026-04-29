"""
SoulSync AI - Core Model Interface
All AI generation now uses Groq API via ai_service.py.

Local DialoGPT / transformers have been removed.
This module re-exports generate_response for backward compatibility.
"""

# Re-export so existing callers (rag_engine, chat, extractor) work unchanged
from backend.core.ai_service import generate_response

__all__ = ["generate_response"]
