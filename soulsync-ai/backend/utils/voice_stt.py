"""
SoulSync AI - Speech to Text (STT)
Converts audio → text using two methods:

Method 1: Whisper (file-based, high accuracy)
  - Accepts audio file path (.wav, .mp3, .m4a)
  - Uses the already-installed openai-whisper model

Method 2: Microphone (live recording)
  - Records from mic using SpeechRecognition + pyaudio
  - Saves to temp file → passes to Whisper
"""

import os
import tempfile
import whisper

# ─── Load Whisper Model (once) ────────────────────────────
# Using 'base' model — fast, good accuracy, ~140MB
print("[STT] Loading Whisper base model...")
_whisper_model = whisper.load_model("base")
print("[STT] Whisper ready.")


# ─── Transcribe Audio File ────────────────────────────────

def transcribe_file(audio_path: str, language: str = "en") -> dict:
    """
    Transcribe an audio file to text using Whisper.

    Args:
        audio_path : path to audio file (.wav, .mp3, .m4a, .webm)
        language   : language code (default: 'en')

    Returns:
        dict with 'text' and 'language'
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    result = _whisper_model.transcribe(audio_path, language=language)

    return {
        "text"    : result["text"].strip(),
        "language": result.get("language", language),
    }


# ─── Record from Microphone ───────────────────────────────

def record_from_mic(duration: int = 5, sample_rate: int = 16000) -> str:
    """
    Record audio from microphone and save to a temp WAV file.

    Args:
        duration    : recording duration in seconds
        sample_rate : audio sample rate (Whisper needs 16000)

    Returns:
        path to the saved temp WAV file
    """
    import speech_recognition as sr

    recognizer = sr.Recognizer()

    with sr.Microphone(sample_rate=sample_rate) as source:
        print(f"[STT] 🎙️ Recording for {duration} seconds... Speak now!")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.record(source, duration=duration)
        print("[STT] Recording complete.")

    # Save to temp WAV file
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(audio.get_wav_data())
    tmp.close()

    return tmp.name


def transcribe_from_mic(duration: int = 5) -> dict:
    """
    Record from mic and transcribe in one call.

    Returns:
        dict with 'text' and 'language'
    """
    audio_path = record_from_mic(duration=duration)
    try:
        result = transcribe_file(audio_path)
        return result
    finally:
        # Clean up temp file
        if os.path.exists(audio_path):
            os.remove(audio_path)
