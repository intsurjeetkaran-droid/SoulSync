"""
SoulSync AI - Intent Detector
Classifies user messages into one of four intents:

  personal_info_store  : "My name is Rohit", "I am 25 years old"
  personal_info_query  : "What is my name?", "What are my goals?"
  task_command         : "Plan my tomorrow", "Remind me to call doctor"
  normal_chat          : everything else

This is the routing brain of SoulSync.
"""

import re
import logging

logger = logging.getLogger("soulsync.intent_detector")

# ─── Personal Info Store Patterns ─────────────────────────
# "My <key> is <value>" or "I am <value>" or "I'm <value>"

PERSONAL_INFO_STORE_PATTERNS = [
    # English patterns
    (r"my\s+name\s+is\s+(.+)",                    "name"),
    (r"call\s+me\s+(.+)",                          "name"),
    (r"i(?:'m| am)\s+called\s+(.+)",               "name"),
    (r"my\s+age\s+is\s+(\d+)",                     "age"),
    (r"i(?:'m| am)\s+(\d+)\s+years?\s+old",        "age"),
    (r"my\s+goal\s+is\s+(.+)",                     "goal"),
    (r"my\s+dream\s+is\s+(.+)",                    "dream"),
    (r"my\s+aim\s+is\s+(.+)",                      "aim"),
    (r"i\s+want\s+to\s+become\s+(.+)",             "goal"),
    (r"i\s+want\s+to\s+be\s+(.+)",                 "goal"),
    (r"my\s+job\s+is\s+(.+)",                      "job"),
    (r"my\s+profession\s+is\s+(.+)",               "job"),
    (r"i\s+work\s+as\s+(.+)",                      "job"),
    (r"i(?:'m| am)\s+a(?:n)?\s+(.+)",              "job"),
    (r"my\s+hobby\s+is\s+(.+)",                    "hobby"),
    (r"my\s+hobbies\s+are\s+(.+)",                 "hobby"),
    (r"i\s+love\s+(.+)",                           "interest"),
    (r"i\s+enjoy\s+(.+)",                          "interest"),
    (r"my\s+favorite\s+(\w+)\s+is\s+(.+)",         "favorite"),
    (r"i\s+live\s+in\s+(.+)",                      "location"),
    (r"i(?:'m| am)\s+from\s+(.+)",                 "location"),
    (r"my\s+email\s+is\s+(.+)",                    "email"),
    (r"my\s+phone\s+(?:number\s+)?is\s+(.+)",      "phone"),
    # ── Hindi / Hinglish patterns ──────────────────────────
    (r"mera\s+naam\s+(?:hai\s+)?([A-Za-z][A-Za-z\s]{1,30})$", "name"),  # mera naam Rohit hai (name must start with capital or be short)
    (r"mujhe\s+([A-Za-z][A-Za-z\s]{1,20})\s+(?:kehte|bulao|bolo)\s+hain?", "name"),
    (r"meri\s+umar\s+(?:hai\s+)?(\d+)",            "age"),
    (r"main\s+(\d+)\s+saal\s+ka",                  "age"),
    (r"mera\s+goal\s+(?:hai\s+)?(.{5,80})",        "goal"),
    (r"mera\s+sapna\s+(?:hai\s+)?(.{5,80})",       "dream"),
    (r"main\s+([A-Za-z][A-Za-z\s]{2,20})\s+(?:hun|hoon)\s*$", "job"),  # main engineer hun (short, ends sentence)
    (r"mujhe\s+(.{5,50})\s+(?:pasand|acha laga|achha laga)", "interest"),
    (r"main\s+(.{3,30})\s+mein\s+rehta",           "location"),
    (r"mera\s+ghar\s+(.{3,30})\s+mein",            "location"),
]

# ─── Personal Info Query Patterns ─────────────────────────

PERSONAL_INFO_QUERY_PATTERNS = [
    r"what(?:'s| is) my name",
    r"do you know my name",
    r"what(?:'s| is) my age",
    r"how old am i",
    r"what(?:'s| are) my goals?",
    r"what(?:'s| is) my dream",
    r"what(?:'s| is) my aim",
    r"what(?:'s| is) my job",
    r"what(?:'s| is) my profession",
    r"what do i do for work",
    r"where do i live",
    r"where am i from",
    r"what(?:'s| are) my hobbies?",
    r"what(?:'s| is) my hobby",
    r"what(?:'s| is) my favorite",
    r"what do you know about me",
    r"tell me about me",
    r"what(?:'s| is) my email",
    r"what(?:'s| is) my phone",
    r"who am i",
    r"remind me (?:of )?(?:my|who)\s*$",
    r"remind me (?:of )?my (?:goals?|name|job|hobby|dream|aim|age|location|email|phone|interests?)",
    r"what(?:'s| are) my interests?",
    # ── Hindi / Hinglish query patterns ───────────────────
    r"mera\s+naam\s+(?:kya\s+)?(?:hai|bata|batao)",   # mera naam kya hai
    r"mujhe\s+(?:kya|batao)\s+(?:mera|apna)\s+naam",
    r"(?:apne\s+baare\s+mein|mere\s+baare\s+mein)\s+(?:batao|bolo)",
    r"mera\s+(?:goal|sapna|kaam|job)\s+(?:kya\s+)?(?:hai|bata|batao)",
    r"main\s+(?:kaun|kya)\s+(?:hun|hoon)",
    r"(?:yaad\s+dilao|yaad\s+karo)\s+(?:mera|meri|mere)",
    r"mujhe\s+(?:kya|batao|bata)\s+(?:mera|apna)",    # mujhe batao mera naam
    # ── Chronological / first-experience queries ──────────
    r"what(?:'s| was| were) (?:the )?first (?:thing|experience|message|story|event)",
    r"what did i (?:first|initially) (?:tell|share|say|mention)",
    r"what was the first (?:thing|experience|event|story) i (?:shared|told|mentioned)",
    r"what(?:'s| is) my (?:earliest|oldest|first) (?:memory|experience|message|story)",
    r"do you remember (?:the )?first (?:thing|time|experience|event)",
    r"what did i tell you (?:first|at the start|at the beginning|initially)",
    r"what was my first",
    r"recall (?:my )?first",
]

# ─── Task Command Patterns ────────────────────────────────
# STRICT: only explicit planning/reminder/scheduling commands
# NOT: "I want to talk", "I should be better", "I will try"

TASK_COMMAND_PATTERNS = [
    r"plan\s+my\s+",
    r"remind\s+me\s+to\s+",
    r"remind\s+me\s+(?:about|of)\s+(?!(?:my|who)\s*$)",
    r"remind\s+me\s+my\s+\w+",
    r"add\s+(?:a\s+)?task",
    r"create\s+(?:a\s+)?task",
    r"set\s+(?:a\s+)?reminder",
    r"schedule\s+",
    r"i\s+need\s+to\s+(?:finish|complete|submit|send|call|email|meet|buy|fix|write|prepare|go|visit|pick)",
    r"i\s+have\s+to\s+(?:finish|complete|submit|send|call|email|meet|buy|fix|write|prepare|go|visit|pick)",
    r"i\s+(?:gotta|gonna)\s+(?:go|do|finish|complete|submit|send|call|email|meet|buy|fix|write|prepare|visit|pick)",
    r"don'?t\s+let\s+me\s+forget\s+to\s+",
    r"make\s+(?:a\s+)?(?:to-?do|todo|task|list)",
    r"i\s+need\s+to\s+go\s+(?:to\s+)?(?:the\s+)?\w+\s+(?:tomorrow|today|tonight|this week|next week)",
    r"i\s+have\s+to\s+go\s+(?:to\s+)?(?:the\s+)?\w+\s+(?:tomorrow|today|tonight|this week|next week)",
    r"i(?:'m| am)\s+going\s+to\s+(?:the\s+)?\w+\s+(?:tomorrow|today|tonight|this week|next week)",
    r"i\s+(?:gotta|gonna)\s+\w+",
    r"^gotta\s+\w+",
    r"i(?:'m| am)\s+gonna\s+\w+",
    r"i\s+should\s+go\s+(?:to\s+)?(?:the\s+)?\w+",
    # ── Hindi / Hinglish task patterns ────────────────────
    r"mujhe\s+.+\s+(?:karna|karni|karni\s+hai|karna\s+hai)",  # mujhe gym karna hai
    r"mujhe\s+.+\s+(?:jana|jaana)\s+(?:hai|hoga)",            # mujhe market jana hai
    r"(?:kal|aaj|parso)\s+.+\s+(?:karna|jana|attend|milna)",  # kal doctor ke paas jana
    r"yaad\s+(?:dilao|karo|rakhna)\s+(?:ki\s+)?mujhe",        # yaad dilao mujhe
    r"mat\s+bhoolna\s+",                                        # mat bhoolna
    r"bhool\s+na\s+jaana\s+",                                   # bhool na jaana
]

# ─── Task Management Patterns (CRUD on existing tasks) ────
# These handle: delete, complete, change priority of existing tasks

TASK_MANAGE_PATTERNS = [
    # Delete
    r"(?:delete|remove|cancel|drop)\s+(?:the\s+)?(?:task\s+)?(?:called\s+|named\s+|about\s+)?(.+)",
    r"(?:i\s+don'?t\s+need\s+to|i\s+no\s+longer\s+need\s+to)\s+(.+)",
    r"(?:scratch|forget)\s+(?:the\s+)?(?:task\s+)?(?:about\s+)?(.+)",
    # Complete
    r"(?:i\s+(?:finished|completed|done|did|accomplished))\s+(.+)",
    r"(?:mark|set)\s+(.+?)\s+(?:as\s+)?(?:done|complete|completed|finished)",
    r"(?:check\s+off|tick\s+off)\s+(.+)",
    r"(.+)\s+(?:is\s+)?done",
    # Priority change
    r"(?:make|set|change)\s+(.+?)\s+(?:to\s+)?(?:high|urgent|important)\s+priority",
    r"(?:make|set|change)\s+(.+?)\s+(?:to\s+)?(?:low|not\s+urgent)\s+priority",
    r"(?:make|set|change)\s+(.+?)\s+(?:to\s+)?(?:medium|normal)\s+priority",
    r"(.+?)\s+(?:is\s+)?(?:urgent|high\s+priority|very\s+important)",
]

# ─── Phrases that look like tasks but are NOT ─────────────
# These override task detection

NOT_TASK_PHRASES = [
    r"i\s+want\s+to\s+(?:talk|chat|speak|discuss|share|tell|ask|know|understand|learn|feel|think)",
    r"i\s+want\s+to\s+(?:be\s+better|improve|grow|change)",
    r"i\s+(?:should|will|must)\s+(?:try|be|do\s+better|improve|focus|work\s+on\s+myself)",
    r"i\s+(?:should|will|must)\s+(?:be\s+more|become|get\s+better)",
    r"i\s+(?:feel|felt|am\s+feeling)",
    r"i\s+(?:think|believe|hope|wish|wonder)",
    r"i\s+(?:like|love|enjoy|hate|dislike)",
    r"i\s+(?:am|was|were|been)\s+(?:happy|sad|tired|stressed|excited|worried|anxious|bored)",
    # NOTE: removed "i had/have/got/get" and "i went/go/came/come" —
    # these were blocking "i gotta", "i gonna", "i should go"
]


# ─── Main Intent Classifier ───────────────────────────────

def detect_intent(text: str) -> dict:
    """
    Classify user message into one of four intents.

    Returns:
        {
          "intent"     : "personal_info_store" | "personal_info_query"
                         | "task_command" | "normal_chat",
          "key"        : str or None   (for personal_info_store)
          "value"      : str or None   (for personal_info_store)
          "confidence" : float
        }
    """
    text_lower = text.lower().strip()
    # Remove trailing punctuation for matching
    text_clean = re.sub(r'[?.!,]+$', '', text_lower).strip()

    logger.debug(f"[Intent] Classifying: '{text_clean}'")

    # ── 0. Hindi/Hinglish query check FIRST ───────────────
    # Must run before store patterns to prevent "mera naam kya hai"
    # from matching the store pattern "mera naam (.+)"
    for pattern in PERSONAL_INFO_QUERY_PATTERNS:
        if re.search(pattern, text_clean, re.IGNORECASE):
            logger.info(f"[Intent] personal_info_query (pre-check) | pattern={pattern}")
            return {
                "intent"    : "personal_info_query",
                "key"       : _extract_query_key(text_clean),
                "value"     : None,
                "confidence": 0.90,
            }

    # ── 1. Check personal info STORE ──────────────────────
    for pattern, key in PERSONAL_INFO_STORE_PATTERNS:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            # Handle "my favorite X is Y" (2 groups)
            if key == "favorite" and len(match.groups()) == 2:
                actual_key   = f"favorite_{match.group(1).strip()}"
                actual_value = match.group(2).strip()
            else:
                actual_key   = key
                actual_value = match.group(1).strip()

            # Clean up value — remove trailing filler
            actual_value = re.sub(r'\s+(?:and|but|so|because|since|though).*$',
                                  '', actual_value, flags=re.IGNORECASE).strip()
            # Remove quotes if present
            actual_value = actual_value.strip('"\'')

            if actual_value and len(actual_value) > 0:
                logger.info(f"[Intent] personal_info_store | key={actual_key} | value={actual_value}")
                return {
                    "intent"    : "personal_info_store",
                    "key"       : actual_key,
                    "value"     : actual_value,
                    "confidence": 0.95,
                }

    # ── 2. Check personal info QUERY (already checked above for Hindi) ──
    # This catches any remaining English patterns not caught by pre-check
    for pattern in PERSONAL_INFO_QUERY_PATTERNS:
        if re.search(pattern, text_clean, re.IGNORECASE):
            logger.info(f"[Intent] personal_info_query | pattern={pattern}")
            return {
                "intent"    : "personal_info_query",
                "key"       : _extract_query_key(text_clean),
                "value"     : None,
                "confidence": 0.90,
            }

    # ── 3. Check NOT-task phrases first (override) ────────
    is_not_task = any(
        re.search(p, text_clean, re.IGNORECASE)
        for p in NOT_TASK_PHRASES
    )

    # ── 3b. Check task MANAGE (delete/complete/priority) ──
    if not is_not_task:
        for pattern in TASK_MANAGE_PATTERNS:
            m = re.search(pattern, text_clean, re.IGNORECASE)
            if m:
                # Determine operation type
                op = "complete"
                if re.search(r"delete|remove|cancel|drop|scratch|forget|don'?t need|no longer need", text_clean):
                    op = "delete"
                elif re.search(r"high|urgent|important|very important", text_clean):
                    op = "priority_high"
                elif re.search(r"low|not urgent", text_clean):
                    op = "priority_low"
                elif re.search(r"medium|normal", text_clean):
                    op = "priority_medium"

                keyword = m.group(1).strip() if m.lastindex else ""
                logger.info(f"[Intent] task_manage | op={op} | keyword={keyword}")
                return {
                    "intent"    : "task_manage",
                    "key"       : op,
                    "value"     : keyword,
                    "confidence": 0.85,
                }

    # ── 4. Check task command ──────────────────────────────
    if not is_not_task:
        for pattern in TASK_COMMAND_PATTERNS:
            if re.search(pattern, text_clean, re.IGNORECASE):
                logger.info(f"[Intent] task_command | pattern={pattern}")
                return {
                    "intent"    : "task_command",
                    "key"       : None,
                    "value"     : None,
                    "confidence": 0.85,
                }

    # ── 5. Default: normal chat ───────────────────────────
    logger.info(f"[Intent] normal_chat")
    return {
        "intent"    : "normal_chat",
        "key"       : None,
        "value"     : None,
        "confidence": 1.0,
    }


def _extract_query_key(text: str) -> str | None:
    """Extract which personal info key is being queried."""
    text = text.lower()

    # ── Chronological / first-experience queries ──────────
    chrono_patterns = [
        r"first (?:thing|experience|message|story|event)",
        r"(?:first|initially) (?:tell|share|say|mention)",
        r"(?:earliest|oldest|first) (?:memory|experience|message|story)",
        r"first (?:thing|time|experience|event)",
        r"tell you (?:first|at the start|at the beginning|initially)",
        r"what was my first",
        r"recall (?:my )?first",
    ]
    for p in chrono_patterns:
        if re.search(p, text):
            return "__earliest__"   # special sentinel key

    if "name"       in text: return "name"
    if "age"        in text or "old" in text: return "age"
    if "goal"       in text or "goals" in text: return "goal"
    if "dream"      in text: return "dream"
    if "aim"        in text: return "aim"
    if "job"        in text or "profession" in text or "work" in text: return "job"
    if "hobby"      in text or "hobbies" in text: return "hobby"
    if "interest"   in text or "interests" in text: return "interest"
    if "live"       in text or "location" in text: return "location"
    if "from"       in text: return "location"
    if "email"      in text: return "email"
    if "phone"      in text: return "phone"
    if "about me"   in text or "who am i" in text: return None  # return all

    # "what is my favorite color/food/movie/etc."
    fav_match = re.search(r"favorite\s+(\w+)", text)
    if fav_match:
        return f"favorite_{fav_match.group(1)}"

    return None
