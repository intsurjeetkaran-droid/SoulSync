"""
SoulSync AI - Voice API Router
Endpoints:
  POST /voice/transcribe  : upload audio file → get text (Whisper)
  POST /voice/speak       : text → WAV audio file (pyttsx3 TTS)
  POST /voice/chat        : full voice pipeline (audio in → audio out)
  GET  /voice/voices      : list available TTS voices
"""

import os
import tempfile
import shutil
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("soulsync.voice")

try:
    from backend.utils.voice_stt import transcribe_file
    from backend.utils.voice_tts import save_to_file, list_voices, speak_text
    VOICE_AVAILABLE = True
    logger.info("[Voice] STT + TTS loaded")
except ImportError as e:
    VOICE_AVAILABLE = False
    logger.warning(f"[Voice] STT/TTS not available: {e}")

from backend.retrieval.rag_engine  import rag_chat
from backend.memory.memory_manager import save_conversation, get_chat_history

router = APIRouter()


# ─── POST /voice/transcribe ───────────────────────────────

@router.post("/voice/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form(default="en")
):
    """Upload audio file → transcribed text (Whisper)."""
    if not VOICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Voice STT not available.")

    suffix = os.path.splitext(file.filename)[-1] or ".wav"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        shutil.copyfileobj(file.file, tmp)
        tmp.close()
        result = transcribe_file(tmp.name, language=language)
        return {"filename": file.filename, "text": result["text"], "language": result["language"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


# ─── POST /voice/speak ────────────────────────────────────

class SpeakRequest(BaseModel):
    text: str


@router.post("/voice/speak")
async def text_to_speech(request: SpeakRequest):
    """
    Convert text to speech and return WAV audio bytes.
    Used by the Voice Mode UI to speak AI responses aloud.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    if not VOICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Voice TTS not available.")

    tmp_path = None
    try:
        tmp_path = save_to_file(request.text)
        # Read file and return as bytes so temp file can be cleaned up
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": "inline; filename=soulsync_response.wav"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─── POST /voice/chat ─────────────────────────────────────

@router.post("/voice/chat")
async def voice_chat(
    user_id: str  = Form(...),
    file: UploadFile = File(...),
    language: str = Form(default="en")
):
    """
    Full voice pipeline:
      1. Transcribe uploaded audio → text (Whisper)
      2. Run RAG chat → AI response text
      3. Convert response → WAV audio
      4. Return audio with transcript in headers
    """
    if not VOICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Voice not available.")

    suffix = os.path.splitext(file.filename)[-1] or ".wav"
    tmp_input = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_output = None

    try:
        shutil.copyfileobj(file.file, tmp_input)
        tmp_input.close()

        stt_result  = transcribe_file(tmp_input.name, language=language)
        user_text   = stt_result["text"]
        if not user_text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio.")

        chat_history  = get_chat_history(user_id, turns=5)
        rag_result    = rag_chat(user_id=user_id, user_message=user_text,
                                 chat_history=chat_history, top_k=3)
        response_text = rag_result["response"]

        save_conversation(user_id, user_text, response_text)

        tmp_output = save_to_file(response_text)
        with open(tmp_output, "rb") as f:
            audio_bytes = f.read()

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "X-Transcribed-Text": user_text[:300],
                "X-AI-Response"     : response_text[:300],
                "X-Intent"          : rag_result.get("intent", ""),
                "Access-Control-Expose-Headers":
                    "X-Transcribed-Text, X-AI-Response, X-Intent",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice chat error: {str(e)}")
    finally:
        if os.path.exists(tmp_input.name):
            os.remove(tmp_input.name)
        if tmp_output and os.path.exists(tmp_output):
            os.remove(tmp_output)


# ─── GET /voice/voices ────────────────────────────────────

@router.get("/voice/voices")
async def get_voices():
    """List all available TTS voices on this system."""
    if not VOICE_AVAILABLE:
        return {"count": 0, "voices": [], "note": "TTS not available"}
    try:
        voices = list_voices()
        return {"count": len(voices), "voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
