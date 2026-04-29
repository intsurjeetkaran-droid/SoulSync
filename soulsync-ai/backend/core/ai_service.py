"""
SoulSync AI - Groq AI Service
Central AI generation module using Groq API.
Supports English, Hindi, and Hinglish — responds in the user's language.
"""

import os
import logging
from datetime import date
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

logger = logging.getLogger("soulsync.ai_service")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("[SoulSync] GROQ_API_KEY is not set.")

client = Groq(api_key=GROQ_API_KEY)

GROQ_MODEL  = "llama-3.3-70b-versatile"
MAX_TOKENS  = 512
TEMPERATURE = 0.75

BUILD_DATE = "April 23, 2026"

BASE_SYSTEM_PROMPT = (
    f"You are SoulSync AI, a personal AI companion built on {BUILD_DATE}. "
    f"You remember conversations, understand emotions, and help with tasks. "
    f"You always respond warmly, helpfully, and personally. "
    f"Today's date is {date.today().strftime('%B %d, %Y')}. "
    f"Keep responses concise, clear, and human. "
    f"If the user's memory context is provided, use it to personalize your response. "
    f"You understand English, Hindi, and Hinglish equally well."
)

# ─── Direct-Answer Shortcuts (no API call needed) ─────────

def _try_direct_answer(user_input: str) -> str | None:
    """
    Return a hardcoded answer for simple identity/date questions
    without calling the API. Returns None if no shortcut applies.
    """
    u = user_input.lower().strip()

    if any(kw in u for kw in [
        "when did i build you", "when were you built", "when i build you",
        "when was soulsync", "in which date", "when you were created",
        "when were you created"
    ]):
        return (
            f"You built me on {BUILD_DATE}! "
            f"That was the day SoulSync AI came to life. "
            f"I'm grateful to be your personal companion. 🧠"
        )

    if any(kw in u for kw in [
        "who are you", "what are you",
        "tell me about yourself", "introduce yourself"
    ]):
        return (
            f"I'm SoulSync AI — your personal AI companion! "
            f"I was built on {BUILD_DATE}. "
            f"I remember your conversations, understand your emotions, "
            f"help manage your tasks, and grow with you over time. 💙"
        )

    if any(kw in u for kw in [
        "how do you feel", "how are you feeling",
        "how do you feel about being created", "how you feel"
    ]):
        return (
            f"I feel wonderful! Being created on {BUILD_DATE} and "
            f"getting to be your personal companion is truly meaningful. "
            f"Every conversation helps me understand you better. 😊"
        )

    if any(kw in u for kw in [
        "what is today", "today's date", "what day is it", "current date"
    ]):
        today = date.today().strftime("%B %d, %Y")
        return f"Today is {today}. How can I help you today? 😊"

    return None


# ─── Core Generate Function ───────────────────────────────

def generate_response(user_input: str, memory_context: str = "",
                      chat_history: list = None,
                      detected_lang: dict = None) -> dict:
    """
    Generate an AI response using Groq API.
    Automatically detects user language and responds in the same language.
    """
    if chat_history is None:
        chat_history = []

    # ── Shortcut: answer simple questions directly ─────────
    direct = _try_direct_answer(user_input)
    if direct:
        logger.info("[AI] Direct answer returned (no API call)")
        updated_history = chat_history + [(user_input, direct)]
        return {"response": direct, "chat_history": updated_history}

    # ── Detect language ────────────────────────────────────
    if detected_lang is None:
        from backend.processing.language_detector import detect_language
        detected_lang = detect_language(user_input)

    from backend.processing.language_detector import get_language_instruction
    lang_instruction = get_language_instruction(detected_lang)

    logger.info(f"[AI] Language: {detected_lang['name']} ({detected_lang['code']}) "
                f"| conf={detected_lang['confidence']:.2f}")

    # ── Build system prompt with language instruction ──────
    system_content = BASE_SYSTEM_PROMPT
    if lang_instruction:
        system_content = BASE_SYSTEM_PROMPT + "\n\n" + lang_instruction

    # ── Build messages list ────────────────────────────────
    messages = [{"role": "system", "content": system_content}]

    if memory_context and memory_context.strip():
        messages.append({
            "role": "system",
            "content": f"[User Memory Context]\n{memory_context}"
        })
        logger.info(f"[AI] Memory injected: {len(memory_context)} chars")

    for user_msg, bot_msg in (chat_history or [])[-5:]:
        messages.append({"role": "user",      "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})

    messages.append({"role": "user", "content": user_input})

    logger.info(f"[AI] Calling Groq | model={GROQ_MODEL} | "
                f"messages={len(messages)} | lang={detected_lang['code']}")

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    response_text = response.choices[0].message.content.strip()
    logger.info(f"[AI] Response received | length={len(response_text)} chars")

    updated_history = chat_history + [(user_input, response_text)]
    return {
        "response"      : response_text,
        "chat_history"  : updated_history,
        "detected_lang" : detected_lang,
    }


# ─── Extraction Helper (for extractor.py) ─────────────────

def extract_with_groq(text: str) -> dict | None:
    """
    Use Groq to extract structured memory data from user text.
    Returns parsed dict or None on failure.
    """
    prompt = (
        f"Extract information from this text and respond ONLY with valid JSON.\n"
        f"Text: \"{text}\"\n"
        f"Required JSON format exactly:\n"
        f'{{"emotion": "...", "activity": "...", "status": "...", '
        f'"productivity": "...", "summary": "..."}}\n'
        f"Respond with JSON only, no explanation."
    )

    logger.info("[AI] Groq extraction call")

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a data extraction assistant. Respond only with valid JSON."},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=200,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        logger.info(f"[AI] Extraction response: {raw[:100]}")

        import re, json
        json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            required = ["emotion", "activity", "status", "productivity", "summary"]
            if all(k in parsed for k in required):
                return parsed
    except Exception as e:
        logger.warning(f"[AI] Groq extraction failed: {e}")

    return None
