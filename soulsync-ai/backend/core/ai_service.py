"""
SoulSync AI - Groq AI Service
==============================

Central AI generation module using Groq API for conversational responses.
This module is responsible for all AI-powered text generation in SoulSync,
including chat responses, memory extraction, and language-aware communication.

Key Features:
    - Multi-language support (English, Hindi, Hinglish)
    - Memory-aware responses using RAG context
    - Direct answer shortcuts for common questions
    - Structured data extraction from user text
    - Automatic language detection and response adaptation

Architecture:
    - Uses Groq API with llama-3.3-70b-versatile model
    - Sub-second response times (avg 0.3-0.7s)
    - Configurable temperature and token limits
    - Comprehensive logging for debugging and monitoring

Usage:
    from backend.core.ai_service import generate_response, extract_with_groq
    
    # Generate a chat response
    result = generate_response(
        user_input="Hello, how are you?",
        memory_context="User likes pizza",
        chat_history=[("Hi", "Hello!")]
    )
    print(result["response"])
    
    # Extract structured data
    data = extract_with_groq("I felt happy when I finished my project")
    print(data)  # {"emotion": "happy", "activity": "project", ...}

Dependencies:
    - groq: Groq API client
    - python-dotenv: Environment variable loading
    - backend.processing.language_detector: Language detection

Author: Surjeet Karan
Created: April 23, 2026
"""

import os
import logging
import json
import re
from datetime import date
from typing import Optional, Dict, List, Any
from groq import Groq
from dotenv import load_dotenv

# ─── Environment Setup ────────────────────────────────────────────────────────
# Load environment variables from .env file (project root)
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

# ─── Logging Configuration ────────────────────────────────────────────────────
logger = logging.getLogger("soulsync.ai_service")
logger.info("[AI Service] Module initializing...")

# ─── Groq API Configuration ───────────────────────────────────────────────────
# Validate required API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("[AI Service] GROQ_API_KEY not found in environment")
    raise RuntimeError(
        "[SoulSync] GROQ_API_KEY is not set. "
        "Please set it in your .env file or environment variables."
    )

# Initialize Groq client with API key
client = Groq(api_key=GROQ_API_KEY)
logger.info("[AI Service] Groq client initialized successfully")

# ─── Model Configuration ──────────────────────────────────────────────────────
# Model selection: llama-3.3-70b-versatile provides best balance of speed and quality
GROQ_MODEL = "llama-3.3-70b-versatile"

# Maximum tokens in response (controls response length)
# 512 tokens ≈ 384 words, suitable for conversational responses
MAX_TOKENS = 512

# Temperature controls randomness (0.0 = deterministic, 1.0 = creative)
# 0.75 provides good balance for empathetic, personalized responses
TEMPERATURE = 0.75

# Build date for AI persona identity
BUILD_DATE = "April 23, 2026"

# ─── System Prompt ────────────────────────────────────────────────────────────
# Base system prompt defines the AI's personality and behavior
# This prompt is always included and sets the foundation for all interactions
BASE_SYSTEM_PROMPT = (
    f"You are SoulSync AI, a personal AI companion built on {BUILD_DATE}. "
    f"You remember conversations, understand emotions, and help with tasks. "
    f"You always respond warmly, helpfully, and personally. "
    f"Today's date is {date.today().strftime('%B %d, %Y')}. "
    f"Keep responses concise, clear, and human. "
    f"If the user's memory context is provided, use it to personalize your response. "
    f"You understand English, Hindi, and Hinglish equally well."
)

logger.debug(f"[AI Service] Base system prompt initialized (length: {len(BASE_SYSTEM_PROMPT)} chars)")


# ═══════════════════════════════════════════════════════════════════════════════
# DIRECT ANSWER SHORTCUTS
# ═══════════════════════════════════════════════════════════════════════════════

def _try_direct_answer(user_input: str) -> Optional[str]:
    """
    Return a hardcoded answer for simple identity/date questions without calling the API.
    
    This optimization reduces API calls and latency for common questions about
    the AI's identity, creation date, and current date.
    
    Args:
        user_input: The user's message text
        
    Returns:
        str: Pre-defined response if question matches known patterns
        None: If no shortcut applies, full API call needed
        
    Examples:
        >>> _try_direct_answer("When were you created?")
        "You built me on April 23, 2026! That was the day..."
        
        >>> _try_direct_answer("What's the weather?")
        None  # Not a shortcut question
    """
    # Normalize input for pattern matching
    u = user_input.lower().strip()
    
    # ── Creation Date Questions ──────────────────────────────────────────────
    creation_keywords = [
        "when did i build you",
        "when were you built",
        "when i build you",
        "when was soulsync",
        "in which date",
        "when you were created",
        "when were you created"
    ]
    
    if any(kw in u for kw in creation_keywords):
        logger.debug("[AI] Direct answer: creation date question")
        return (
            f"You built me on {BUILD_DATE}! "
            f"That was the day SoulSync AI came to life. "
            f"I'm grateful to be your personal companion. 🧠"
        )
    
    # ── Identity Questions ───────────────────────────────────────────────────
    identity_keywords = [
        "who are you",
        "what are you",
        "tell me about yourself",
        "introduce yourself"
    ]
    
    if any(kw in u for kw in identity_keywords):
        logger.debug("[AI] Direct answer: identity question")
        return (
            f"I'm SoulSync AI — your personal AI companion! "
            f"I was built on {BUILD_DATE}. "
            f"I remember your conversations, understand your emotions, "
            f"help manage your tasks, and grow with you over time. 💙"
        )
    
    # ── Feeling Questions ────────────────────────────────────────────────────
    feeling_keywords = [
        "how do you feel",
        "how are you feeling",
        "how do you feel about being created",
        "how you feel"
    ]
    
    if any(kw in u for kw in feeling_keywords):
        logger.debug("[AI] Direct answer: feeling question")
        return (
            f"I feel wonderful! Being created on {BUILD_DATE} and "
            f"getting to be your personal companion is truly meaningful. "
            f"Every conversation helps me understand you better. 😊"
        )
    
    # ── Date Questions ───────────────────────────────────────────────────────
    date_keywords = [
        "what is today",
        "today's date",
        "what day is it",
        "current date"
    ]
    
    if any(kw in u for kw in date_keywords):
        today = date.today().strftime("%B %d, %Y")
        logger.debug(f"[AI] Direct answer: date question → {today}")
        return f"Today is {today}. How can I help you today? 😊"
    
    # No shortcut applies
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# CORE AI GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_response(
    user_input: str,
    memory_context: str = "",
    chat_history: Optional[List[tuple]] = None,
    detected_lang: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate an AI response using Groq API with full context awareness.
    
    This is the main entry point for AI response generation. It handles:
    1. Direct answer shortcuts for common questions
    2. Language detection and adaptation
    3. Memory context injection for personalization
    4. Chat history integration for conversation continuity
    5. API call to Groq for response generation
    
    Args:
        user_input: The user's message text
        memory_context: Optional context from RAG retrieval (personalized memories)
        chat_history: List of (user_msg, bot_msg) tuples for conversation context
        detected_lang: Optional pre-detected language info (avoids re-detection)
        
    Returns:
        dict containing:
            - response (str): The AI's generated response text
            - chat_history (list): Updated conversation history with new exchange
            - detected_lang (dict): Language detection results (if performed)
            
    Raises:
        Exception: If Groq API call fails (network issues, rate limits, etc.)
        
    Example:
        >>> result = generate_response(
        ...     user_input="I'm feeling tired today",
        ...     memory_context="User mentioned working late hours",
        ...     chat_history=[("How are you?", "I'm good!")]
        ... )
        >>> print(result["response"])
        "I understand feeling tired... [personalized response]"
    """
    # Initialize chat history if not provided
    if chat_history is None:
        chat_history = []
        logger.debug("[AI] Initialized empty chat history")
    
    # ── Step 1: Try Direct Answer (Optimization) ─────────────────────────────
    logger.debug(f"[AI] Processing user input: '{user_input[:50]}...'")
    
    direct = _try_direct_answer(user_input)
    if direct:
        logger.info("[AI] Direct answer returned (no API call) - saved ~500ms")
        updated_history = chat_history + [(user_input, direct)]
        return {
            "response": direct,
            "chat_history": updated_history
        }
    
    # ── Step 2: Language Detection ───────────────────────────────────────────
    if detected_lang is None:
        # Lazy import to avoid circular dependencies
        from backend.processing.language_detector import detect_language
        detected_lang = detect_language(user_input)
        logger.debug(f"[AI] Language detected: {detected_lang}")
    
    # Get language-specific instructions for the system prompt
    from backend.processing.language_detector import get_language_instruction
    lang_instruction = get_language_instruction(detected_lang)
    
    logger.info(
        f"[AI] Language: {detected_lang['name']} ({detected_lang['code']}) "
        f"| confidence={detected_lang['confidence']:.2f}"
    )
    
    # ── Step 3: Build System Prompt ──────────────────────────────────────────
    # Start with base prompt
    system_content = BASE_SYSTEM_PROMPT
    
    # Add language-specific instruction if needed
    if lang_instruction:
        system_content = f"{BASE_SYSTEM_PROMPT}\n\n{lang_instruction}"
        logger.debug(f"[AI] Added language instruction: {lang_instruction[:50]}...")
    
    # ── Step 4: Build Messages Array ─────────────────────────────────────────
    # Start with system message
    messages = [{"role": "system", "content": system_content}]
    
    # Add memory context if available (RAG retrieval results)
    if memory_context and memory_context.strip():
        memory_message = {
            "role": "system",
            "content": f"[User Memory Context]\n{memory_context}"
        }
        messages.append(memory_message)
        logger.info(f"[AI] Memory context injected: {len(memory_context)} chars")
    else:
        logger.debug("[AI] No memory context provided")
    
    # Add recent chat history (last 5 turns to stay within token limits)
    recent_history = chat_history[-5:] if chat_history else []
    for user_msg, bot_msg in recent_history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})
    
    logger.debug(f"[AI] Chat history added: {len(recent_history)} turns")
    
    # Add current user message
    messages.append({"role": "user", "content": user_input})
    
    logger.info(
        f"[AI] Calling Groq API | model={GROQ_MODEL} | "
        f"messages={len(messages)} | max_tokens={MAX_TOKENS} | "
        f"temperature={TEMPERATURE} | lang={detected_lang['code']}"
    )
    
    # ── Step 5: Call Groq API ────────────────────────────────────────────────
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        
        # Extract response text
        response_text = response.choices[0].message.content.strip()
        
        logger.info(
            f"[AI] Response received | length={len(response_text)} chars | "
            f"model={GROQ_MODEL} | finish_reason={response.choices[0].finish_reason}"
        )
        
        # Update chat history with new exchange
        updated_history = chat_history + [(user_input, response_text)]
        
        return {
            "response": response_text,
            "chat_history": updated_history,
            "detected_lang": detected_lang,
        }
        
    except Exception as e:
        logger.error(f"[AI] Groq API call failed: {e}", exc_info=True)
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURED DATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_with_groq(text: str) -> Optional[Dict[str, str]]:
    """
    Use Groq to extract structured memory data from user text.
    
    This function analyzes user messages to extract structured information about:
    - Emotions (how the user feels)
    - Activities (what the user did)
    - Status (outcome of the activity)
    - Productivity (how productive the user was)
    - Summary (brief description)
    
    The extracted data is used to build the user's behavioral memory profile
    and generate personalized insights.
    
    Args:
        text: Raw user text to analyze
        
    Returns:
        dict containing extracted fields if successful:
            - emotion: Detected emotion (e.g., "happy", "tired", "stressed")
            - activity: Detected activity (e.g., "gym", "work", "study")
            - status: Activity status (e.g., "completed", "missed", "started")
            - productivity: Productivity level (e.g., "high", "medium", "low")
            - summary: Brief summary of the text
        None: If extraction fails or response is invalid
        
    Example:
        >>> extract_with_groq("I felt tired and skipped gym today")
        {
            "emotion": "tired",
            "activity": "gym",
            "status": "missed",
            "productivity": "low",
            "summary": "User skipped gym due to tiredness"
        }
    """
    logger.debug(f"[AI] Starting extraction for text: '{text[:50]}...'")
    
    # Construct extraction prompt
    prompt = (
        f"Extract information from this text and respond ONLY with valid JSON.\n"
        f"Text: \"{text}\"\n"
        f"Required JSON format exactly:\n"
        f'{{"emotion": "...", "activity": "...", "status": "...", '
        f'"productivity": "...", "summary": "..."}}\n'
        f"Respond with JSON only, no explanation."
    )
    
    logger.info("[AI] Groq extraction call initiated")
    
    try:
        # Call Groq API for extraction
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a data extraction assistant. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
            max_tokens=200,
            temperature=0.1,  # Low temperature for consistent extraction
        )
        
        raw = response.choices[0].message.content.strip()
        logger.debug(f"[AI] Extraction response: {raw[:100]}...")
        
        # Extract JSON from response (handle potential markdown formatting)
        json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            
            # Validate required fields
            required_fields = ["emotion", "activity", "status", "productivity", "summary"]
            if all(field in parsed for field in required_fields):
                logger.info(f"[AI] Extraction successful: emotion={parsed['emotion']}, activity={parsed['activity']}")
                return parsed
            else:
                missing = [f for f in required_fields if f not in parsed]
                logger.warning(f"[AI] Extraction missing fields: {missing}")
        else:
            logger.warning(f"[AI] No JSON found in response: {raw[:100]}")
            
    except json.JSONDecodeError as e:
        logger.error(f"[AI] JSON parsing failed: {e}")
    except Exception as e:
        logger.warning(f"[AI] Groq extraction failed: {e}")
    
    return None


# ─── Module Initialization Complete ───────────────────────────────────────────
logger.info("[AI Service] Module initialized successfully")