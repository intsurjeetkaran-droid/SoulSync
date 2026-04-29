"""
SoulSync AI - Text to Speech (TTS)
Converts AI response text → spoken audio using pyttsx3.

pyttsx3 works fully offline on Windows using
the built-in SAPI5 voice engine — no API key needed.

Features:
  - speak_text()     : speak text aloud directly
  - save_to_file()   : save speech to a WAV file
  - list_voices()    : show available system voices
  - set_voice()      : change voice (male/female)
"""

import pyttsx3
import os
import tempfile

# ─── Initialize TTS Engine (once) ─────────────────────────
_engine = pyttsx3.init()

# Default settings
_engine.setProperty("rate",   165)   # speed (words per minute)
_engine.setProperty("volume", 0.95)  # volume (0.0 to 1.0)

# Try to set a pleasant voice
def _set_default_voice():
    voices = _engine.getProperty("voices")
    if voices:
        # Prefer female voice if available (index 1 on most Windows)
        if len(voices) > 1:
            _engine.setProperty("voice", voices[1].id)
        else:
            _engine.setProperty("voice", voices[0].id)

_set_default_voice()
print("[TTS] pyttsx3 engine ready.")


# ─── Speak Text ───────────────────────────────────────────

def speak_text(text: str):
    """
    Speak text aloud through the system speakers.

    Args:
        text: the text to speak
    """
    if not text or not text.strip():
        return

    # Limit length to avoid very long speeches
    text = text[:500]

    _engine.say(text)
    _engine.runAndWait()


# ─── Save to Audio File ───────────────────────────────────

def save_to_file(text: str, output_path: str = None) -> str:
    """
    Save speech to a WAV file instead of playing it.

    Args:
        text        : text to convert
        output_path : where to save (auto-generates temp file if None)

    Returns:
        path to the saved audio file
    """
    if not output_path:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = tmp.name
        tmp.close()

    text = text[:500]
    _engine.save_to_file(text, output_path)
    _engine.runAndWait()

    return output_path


# ─── List Available Voices ────────────────────────────────

def list_voices() -> list:
    """Return list of available system voices."""
    voices = _engine.getProperty("voices")
    return [
        {"id": v.id, "name": v.name, "languages": v.languages}
        for v in voices
    ]


# ─── Set Voice ────────────────────────────────────────────

def set_voice(voice_index: int = 0):
    """
    Set voice by index.
    0 = first voice (usually male)
    1 = second voice (usually female)
    """
    voices = _engine.getProperty("voices")
    if voice_index < len(voices):
        _engine.setProperty("voice", voices[voice_index].id)


def set_rate(rate: int = 165):
    """Set speech rate (words per minute). Default: 165."""
    _engine.setProperty("rate", rate)
