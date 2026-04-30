"""
SoulSync AI - Text to Speech (TTS)
Primary  : edge-tts  → Microsoft Neerja (Indian English female, neural)
Fallback : pyttsx3   → Microsoft Zira (US English female, offline)
"""

import os
import tempfile
import asyncio
import logging

logger = logging.getLogger("soulsync.tts")

# ── edge-tts (primary — Neerja, Indian English) ───────────
EDGE_VOICE = "en-IN-NeerjaNeural"   # Indian English female

try:
    import edge_tts
    EDGE_AVAILABLE = True
    logger.info(f"[TTS] edge-tts ready — voice: {EDGE_VOICE}")
    print(f"[TTS] edge-tts ready — voice: {EDGE_VOICE}")
except ImportError:
    EDGE_AVAILABLE = False
    logger.warning("[TTS] edge-tts not available, falling back to pyttsx3")
    print("[TTS] edge-tts not available, falling back to pyttsx3")

# ── pyttsx3 (fallback — Zira, offline) ───────────────────
_pyttsx3_engine   = None
_FEMALE_VOICE_ID  = None

def _init_pyttsx3():
    global _pyttsx3_engine, _FEMALE_VOICE_ID
    try:
        import pyttsx3
        _pyttsx3_engine = pyttsx3.init()
        _pyttsx3_engine.setProperty("rate",   160)
        _pyttsx3_engine.setProperty("volume", 0.97)

        voices = _pyttsx3_engine.getProperty("voices")
        female_kw = ["zira", "female", "woman", "hazel", "susan",
                     "eva", "aria", "jenny", "natasha", "linda"]
        for v in voices:
            if any(kw in v.name.lower() for kw in female_kw):
                _FEMALE_VOICE_ID = v.id
                _pyttsx3_engine.setProperty("voice", v.id)
                print(f"[TTS] pyttsx3 fallback voice: {v.name}")
                return
        if voices:
            _FEMALE_VOICE_ID = voices[min(1, len(voices)-1)].id
            _pyttsx3_engine.setProperty("voice", _FEMALE_VOICE_ID)
    except Exception as e:
        print(f"[TTS] pyttsx3 init failed: {e}")

if not EDGE_AVAILABLE:
    _init_pyttsx3()

print("[TTS] engine ready.")


# ── save_to_file (async-safe) ─────────────────────────────

async def _edge_save(text: str, output_path: str):
    """Generate WAV via edge-tts (Neerja)."""
    communicate = edge_tts.Communicate(text[:600], EDGE_VOICE)
    await communicate.save(output_path)


def _pyttsx3_save(text: str, output_path: str):
    """Generate WAV via pyttsx3 (Zira fallback)."""
    if _FEMALE_VOICE_ID:
        _pyttsx3_engine.setProperty("voice", _FEMALE_VOICE_ID)
    _pyttsx3_engine.save_to_file(text[:500], output_path)
    _pyttsx3_engine.runAndWait()


def save_to_file(text: str, output_path: str = None) -> str:
    """
    Convert text to speech and save as audio file.
    Uses Neerja (edge-tts) if available, else Zira (pyttsx3).
    Returns path to the saved file.
    """
    if not output_path:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3" if EDGE_AVAILABLE else ".wav",
                                          delete=False)
        output_path = tmp.name
        tmp.close()

    if EDGE_AVAILABLE:
        # edge-tts is async — run it in a new event loop
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_edge_save(text, output_path))
            loop.close()
            return output_path
        except Exception as e:
            logger.error(f"[TTS] edge-tts failed: {e}, falling back to pyttsx3")
            if not _pyttsx3_engine:
                _init_pyttsx3()

    # pyttsx3 fallback
    _pyttsx3_save(text, output_path)
    return output_path


def speak_text(text: str):
    """Speak text directly (used for local testing only)."""
    path = save_to_file(text)
    try:
        import playsound
        playsound.playsound(path)
    except Exception:
        pass
    finally:
        if os.path.exists(path):
            os.remove(path)


def list_voices() -> list:
    """Return available voices info."""
    if EDGE_AVAILABLE:
        return [{"id": EDGE_VOICE, "name": "Microsoft Neerja (Indian English Female)",
                 "engine": "edge-tts"}]
    voices = _pyttsx3_engine.getProperty("voices") if _pyttsx3_engine else []
    return [{"id": v.id, "name": v.name, "engine": "pyttsx3"} for v in voices]


def set_rate(rate: int = 160):
    if _pyttsx3_engine:
        _pyttsx3_engine.setProperty("rate", rate)
