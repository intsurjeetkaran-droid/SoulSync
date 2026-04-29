"""
SoulSync AI - Language Detector
Detects the language of a user message without any API call.
Supports: English, Hindi (Devanagari), Hinglish (Hindi in Roman script).

Returns a language code and a human-readable name for use in the system prompt.
"""

import re
import logging

logger = logging.getLogger("soulsync.language_detector")

# ── Hindi Devanagari Unicode range ────────────────────────
DEVANAGARI_PATTERN = re.compile(r'[\u0900-\u097F]')

# ── Common Hinglish words (Hindi written in Roman script) ─
HINGLISH_WORDS = {
    # Pronouns / common words
    "mera", "meri", "mujhe", "mujhko", "main", "mai", "hum", "aap", "tum",
    "yeh", "woh", "kya", "kaise", "kab", "kahan", "kyun", "kyunki",
    # Verbs
    "hai", "hain", "tha", "thi", "the", "ho", "hoga", "hogi", "hoge",
    "kar", "karo", "karna", "kiya", "ki", "ke", "ka", "ko",
    "aana", "aaya", "aayi", "jana", "gaya", "gayi", "gaye",
    "lena", "liya", "dena", "diya", "karna", "karo",
    "bata", "batao", "samjho", "dekho", "suno",
    # Time words
    "aaj", "kal", "parso", "abhi", "jaldi", "baad", "pehle",
    "subah", "shaam", "raat", "dopahar",
    # Common expressions
    "bahut", "thoda", "zyada", "kam", "accha", "theek", "sahi",
    "nahi", "nahin", "haan", "bilkul", "zaroor", "shayad",
    "bhi", "sirf", "bas", "toh", "phir", "lekin", "aur", "ya",
    "yaar", "bhai", "dost", "bhaiya", "didi", "ji",
    # Task/action words
    "karna", "karo", "kiya", "karli", "kar li", "kar liya",
    "attend", "gaya", "gayi", "gaye", "aya", "ayi",
    "mila", "mili", "mile", "dekha", "dekhi",
    "shaadi", "birthday", "party", "kaam", "khaana", "paani",
    # Emotions
    "khush", "dukhi", "pareshan", "thaka", "thaki", "tension",
    "mast", "bekar", "bura", "acha",
}

# ── Language codes ─────────────────────────────────────────
LANG_ENGLISH  = "en"
LANG_HINDI    = "hi"
LANG_HINGLISH = "hi-en"   # Hindi in Roman script


def detect_language(text: str) -> dict:
    """
    Detect the language of a message.

    Returns:
        {
          "code"        : "en" | "hi" | "hi-en",
          "name"        : "English" | "Hindi" | "Hinglish",
          "is_hindi"    : bool,   # True for both hi and hi-en
          "confidence"  : float,
        }
    """
    if not text or not text.strip():
        return {"code": LANG_ENGLISH, "name": "English",
                "is_hindi": False, "confidence": 1.0}

    # ── Check for Devanagari script (pure Hindi) ──────────
    devanagari_chars = len(DEVANAGARI_PATTERN.findall(text))
    if devanagari_chars > 0:
        confidence = min(1.0, devanagari_chars / max(len(text) * 0.3, 1))
        logger.debug(f"[Lang] Detected Hindi (Devanagari) | conf={confidence:.2f}")
        return {"code": LANG_HINDI, "name": "Hindi",
                "is_hindi": True, "confidence": confidence}

    # ── Check for Hinglish (Hindi words in Roman script) ──
    words      = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    hindi_hits = words & HINGLISH_WORDS
    total_words = max(len(words), 1)
    hindi_ratio = len(hindi_hits) / total_words

    if hindi_ratio >= 0.25 or len(hindi_hits) >= 2:
        confidence = min(1.0, hindi_ratio * 2)
        logger.debug(f"[Lang] Detected Hinglish | hits={hindi_hits} | conf={confidence:.2f}")
        return {"code": LANG_HINGLISH, "name": "Hinglish",
                "is_hindi": True, "confidence": confidence}

    # ── Default: English ───────────────────────────────────
    return {"code": LANG_ENGLISH, "name": "English",
            "is_hindi": False, "confidence": 1.0}


def get_language_instruction(lang: dict) -> str:
    """
    Return a system prompt instruction telling the AI which language to use.
    """
    code = lang["code"]

    if code == LANG_HINDI:
        return (
            "IMPORTANT: The user is writing in Hindi (Devanagari script). "
            "You MUST respond entirely in Hindi using Devanagari script. "
            "Be warm, natural, and conversational in Hindi."
        )
    if code == LANG_HINGLISH:
        return (
            "IMPORTANT: The user is writing in Hinglish (Hindi words in Roman/English script). "
            "You MUST respond in Hinglish — mix Hindi and English naturally, "
            "the way friends talk in India. Use Roman script for Hindi words. "
            "Example style: 'Haan bilkul! Main tumhari help karunga. Kya karna hai?' "
            "Be casual, warm, and natural."
        )
    # English — no special instruction needed
    return ""
