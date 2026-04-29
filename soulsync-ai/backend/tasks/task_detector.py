"""
SoulSync AI - Task Detector
Detects tasks from natural language user messages.
Handles formal AND informal language (gotta, gonna, typos, etc.)

Examples:
  "I need to finish my project by Friday"   → Task: Finish project | due: Friday
  "Remind me to go to gym tomorrow"         → Task: Go to gym | due: tomorrow
  "i gonna market tomorrow"                 → Task: Go to market | due: tomorrow
  "i gotta call mom tonight"                → Task: Call mom | due: tonight
  "remind me my friend"                     → Task: Remind friend
"""

import re


# ─── Trigger Phrases ──────────────────────────────────────

TASK_TRIGGERS = [
    # Formal English
    "i need to", "i have to", "i must",
    "remind me to", "remind me my", "remind me about",
    "don't let me forget to", "don't let me forget",
    "i plan to", "i'm going to", "i will",
    "need to", "have to",
    "remember to", "don't forget to",
    # Informal / slang English
    "i gotta", "i've gotta", "i got to",
    "i gonna", "i'm gonna",
    "gotta", "gonna go", "gonna do",
    "i need", "i should go",
    # ── Hindi / Hinglish triggers ──────────────────────────
    "mujhe", "mujhko",          # "mujhe jana hai" = I need to go
    "karna hai", "karni hai",   # "karna hai" = need to do
    "jana hai", "jaana hai",    # "jana hai" = need to go
    "yaad dilao", "yaad karo",  # remind me
    "bhool na jaana", "mat bhoolna",  # don't forget
    "plan hai", "plan karo",    # plan to
    "sochna hai", "sochna",     # thinking of
]

# ─── Due Date Keywords ────────────────────────────────────

DUE_DATE_PATTERNS = {
    "today"     : r"\b(today|aaj|aaj ka)\b",
    "tomorrow"  : r"\b(tomorrow|kal|aane wala kal)\b",
    "monday"    : r"\b(monday|somvar|sombwar)\b",
    "tuesday"   : r"\b(tuesday|mangalvar)\b",
    "wednesday" : r"\b(wednesday|budhvar)\b",
    "thursday"  : r"\b(thursday|guruvar|brihaspativar)\b",
    "friday"    : r"\b(friday|shukravar)\b",
    "saturday"  : r"\b(saturday|shanivar)\b",
    "sunday"    : r"\b(sunday|ravivar|itwaar)\b",
    "this week" : r"\b(this week|is hafte|is week)\b",
    "next week" : r"\b(next week|agle hafte|agle week)\b",
    "tonight"   : r"\b(tonight|aaj raat)\b",
    "morning"   : r"\b(this morning|subah|in the morning)\b",
    "evening"   : r"\b(this evening|shaam|in the evening)\b",
}

# ─── Priority Keywords ────────────────────────────────────

HIGH_PRIORITY = ["urgent", "asap", "immediately", "critical",
                 "important", "must", "deadline", "by today", "tonight",
                 "zaruri", "bahut zaruri", "jaldi", "abhi", "turant"]
LOW_PRIORITY  = ["someday", "eventually", "maybe", "when i can",
                 "if possible", "no rush",
                 "baad mein", "kabhi bhi", "koi jaldi nahi"]


# ─── Helpers ──────────────────────────────────────────────

def _detect_due_date(text: str) -> str | None:
    """Extract due date keyword from text."""
    text_lower = text.lower()
    for label, pattern in DUE_DATE_PATTERNS.items():
        if re.search(pattern, text_lower):
            return label
    match = re.search(r'\bby\s+(\w+)', text_lower)
    if match:
        return match.group(1)
    return None


def _detect_priority(text: str) -> str:
    """Detect task priority from text."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in HIGH_PRIORITY):
        return "high"
    if any(kw in text_lower for kw in LOW_PRIORITY):
        return "low"
    return "medium"


def _clean_title(raw: str) -> str:
    """
    Clean up extracted task title.
    Removes filler trigger phrases, due-date words, and normalizes.
    """
    fillers = [
        # Formal
        "i need to", "i have to", "i must", "i should",
        "remind me to", "remind me my", "remind me about", "remind me",
        "i want to", "i plan to", "i'm going to", "i will",
        "need to", "have to", "must", "should",
        "remember to", "don't let me forget to", "don't forget to",
        "i need",
        # Informal
        "i gotta", "i've gotta", "i got to",
        "i'm gonna", "i gonna",
        "gotta", "gonna",
        "i should go to", "i should go",
        "i have to go to", "i have to go",
        "i need to go to", "i need to go",
        "i'm going to go to", "i'm going to go",
        "i am going to go to", "i am going to go",
        "please remind me my", "please remind me",
    ]

    title = raw.lower().strip()

    # Sort fillers longest-first so we match the most specific first
    for filler in sorted(fillers, key=len, reverse=True):
        if title.startswith(filler):
            title = title[len(filler):].strip()
            break

    # Remove due date phrases
    for label, pattern in DUE_DATE_PATTERNS.items():
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)

    # Remove "by <word>" pattern
    title = re.sub(r'\bby\s+\w+', "", title, flags=re.IGNORECASE)

    # Remove trailing filler words and phrases
    trailing_fillers = [
        r"\s+please\s+remind\s+me\s+my\s+\w+$",
        r"\s+please\s+remind\s+me$",
        r"\s+remind\s+me\s+my\s+\w+$",
        r"\s+remind\s+me$",
        r"\s+please$",
        r"\b(please|ok|okay)\s*$",
        r"\bmy\s+friend\s*$",
        r"\bfriend\s*$",
    ]
    for pattern in trailing_fillers:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE).strip()

    # Remove leading articles "the", "a", "an"
    title = re.sub(r'^(?:the|a|an)\s+', '', title, flags=re.IGNORECASE).strip()

    # Clean punctuation and extra spaces
    title = re.sub(r'[,\.!?]+', '', title).strip()
    title = re.sub(r'\s+', ' ', title).strip()

    # Normalize common typos / informal words
    title = re.sub(r'\bmarket\b', 'market', title)   # keep as-is
    title = re.sub(r'\bmrket\b',  'market', title)   # typo fix
    title = re.sub(r'\btommorow\b', 'tomorrow', title)
    title = re.sub(r'\btommorrow\b', 'tomorrow', title)

    # Capitalize first letter
    return title.capitalize() if title else raw.capitalize()


# ─── Main Detector ────────────────────────────────────────

def detect_tasks(text: str) -> list:
    """
    Detect tasks from a user message.

    Returns:
        List of task dicts: [{"title": "...", "due_date": "...", "priority": "..."}]
    """
    text_lower = text.lower()
    tasks      = []

    # Check if message contains any task trigger
    triggered = any(trigger in text_lower for trigger in TASK_TRIGGERS)
    if not triggered:
        return []

    # Split on conjunctions to handle multiple tasks
    parts = re.split(r'\band\b|\balso\b|\bplus\b', text, flags=re.IGNORECASE)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        title    = _clean_title(part)
        due_date = _detect_due_date(part)
        priority = _detect_priority(part)

        # Only add if title is meaningful (more than 2 chars)
        if len(title) > 2:
            tasks.append({
                "title"   : title,
                "due_date": due_date,
                "priority": priority,
            })

    return tasks


def is_task_message(text: str) -> bool:
    """
    Quick check if a message is a genuine task command.
    Uses the intent detector for accuracy.
    """
    from backend.processing.intent_detector import detect_intent
    result = detect_intent(text)
    return result["intent"] == "task_command"
