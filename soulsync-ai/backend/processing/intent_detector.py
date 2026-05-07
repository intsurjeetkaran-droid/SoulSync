"""
SoulSync AI - Intent Detector (Enhanced)
Classifies user messages into intents with expanded patterns for accuracy.

Intents:
  personal_info_store  — storing facts about the user
  personal_info_query  — querying stored facts
  task_command         — creating/scheduling tasks
  task_manage          — completing/deleting/updating tasks
  normal_chat          — everything else
"""

import re
import logging

logger = logging.getLogger("soulsync.intent_detector")

# ─── Personal Info STORE Patterns ────────────────────────

PERSONAL_INFO_STORE_PATTERNS = [
    # ── Name ──────────────────────────────────────────────
    (r"my\s+name\s+is\s+(.+)",                         "name"),
    (r"call\s+me\s+(.+)",                               "name"),
    (r"i(?:'m| am)\s+called\s+(.+)",                    "name"),
    (r"people\s+call\s+me\s+(.+)",                      "name"),
    (r"everyone\s+calls\s+me\s+(.+)",                   "name"),
    (r"my\s+nickname\s+is\s+(.+)",                      "name"),
    # ── Age ───────────────────────────────────────────────
    (r"my\s+age\s+is\s+(\d+)",                          "age"),
    (r"i(?:'m| am)\s+(\d+)\s+years?\s+old",             "age"),
    (r"i\s+turned\s+(\d+)\s+(?:today|yesterday|recently|this year)", "age"),
    (r"i(?:'m| am)\s+(\d+)\s+(?:years?|yrs?)",          "age"),
    # ── Goal / Dream / Aim ────────────────────────────────
    (r"my\s+(?:main\s+)?goal\s+is\s+(?:to\s+)?(.+)",   "goal"),
    (r"my\s+(?:life\s+)?dream\s+is\s+(?:to\s+)?(.+)",  "dream"),
    (r"my\s+aim\s+is\s+(?:to\s+)?(.+)",                "aim"),
    (r"i\s+want\s+to\s+become\s+(.+)",                  "goal"),
    (r"i\s+want\s+to\s+be\s+(?:a\s+)?(.+)",             "goal"),
    (r"i\s+aspire\s+to\s+(?:be\s+|become\s+)?(.+)",    "goal"),
    (r"my\s+ambition\s+is\s+(?:to\s+)?(.+)",            "goal"),
    (r"i(?:'m| am)\s+working\s+towards\s+(.+)",         "goal"),
    (r"i\s+hope\s+to\s+(?:become\s+|be\s+)?(.+)",      "goal"),
    # ── Job / Career ──────────────────────────────────────
    (r"my\s+job\s+is\s+(.+)",                           "job"),
    (r"my\s+profession\s+is\s+(.+)",                    "job"),
    (r"my\s+occupation\s+is\s+(.+)",                    "job"),
    (r"i\s+work\s+as\s+(?:a\s+|an\s+)?(.+)",           "job"),
    (r"i(?:'m| am)\s+a(?:n)?\s+([\w\s]+(?:engineer|developer|designer|doctor|teacher|manager|analyst|writer|artist|student|nurse|lawyer|chef|architect|scientist|researcher|consultant|entrepreneur|founder|ceo|cto|intern|freelancer)[\w\s]*)", "job"),
    (r"i\s+work\s+at\s+(.+)",                           "workplace"),
    (r"i\s+work\s+for\s+(.+)",                          "workplace"),
    (r"my\s+company\s+is\s+(.+)",                       "workplace"),
    # ── Hobby / Interest ──────────────────────────────────
    (r"my\s+hobby\s+is\s+(.+)",                         "hobby"),
    (r"my\s+hobbies\s+are\s+(.+)",                      "hobby"),
    (r"i\s+love\s+(?:to\s+)?(.+)",                      "interest"),
    (r"i\s+enjoy\s+(?:doing\s+)?(.+)",                  "interest"),
    (r"i(?:'m| am)\s+passionate\s+about\s+(.+)",        "interest"),
    (r"i(?:'m| am)\s+into\s+(.+)",                      "interest"),
    (r"my\s+passion\s+is\s+(.+)",                       "interest"),
    # ── Favorite ──────────────────────────────────────────
    (r"my\s+favorite\s+(\w+)\s+is\s+(.+)",              "favorite"),
    (r"my\s+favourite\s+(\w+)\s+is\s+(.+)",             "favorite"),
    # ── Location ──────────────────────────────────────────
    (r"i\s+live\s+in\s+(.+)",                           "location"),
    (r"i(?:'m| am)\s+from\s+(.+)",                      "location"),
    (r"i(?:'m| am)\s+based\s+in\s+(.+)",                "location"),
    (r"i\s+stay\s+in\s+(.+)",                           "location"),
    (r"my\s+city\s+is\s+(.+)",                          "location"),
    (r"i\s+moved\s+to\s+(.+)",                          "location"),
    # ── Contact ───────────────────────────────────────────
    (r"my\s+email\s+(?:address\s+)?is\s+(.+)",          "email"),
    (r"my\s+phone\s+(?:number\s+)?is\s+(.+)",           "phone"),
    # ── Family ────────────────────────────────────────────
    (r"my\s+(?:wife|husband|partner|girlfriend|boyfriend)(?:'s name)?\s+is\s+(.+)", "partner"),
    (r"my\s+(?:mom|mother)(?:'s name)?\s+is\s+(.+)",    "mother_name"),
    (r"my\s+(?:dad|father)(?:'s name)?\s+is\s+(.+)",    "father_name"),
    (r"my\s+(?:sister|brother)(?:'s name)?\s+is\s+(.+)","sibling_name"),
    (r"my\s+(?:son|daughter)(?:'s name)?\s+is\s+(.+)",  "child_name"),
    (r"i\s+have\s+(\d+)\s+(?:kids?|children|siblings?|brothers?|sisters?)", "family_count"),
    # ── Education ─────────────────────────────────────────
    (r"i(?:'m| am)\s+(?:a\s+)?student\s+(?:at|of|in)\s+(.+)", "school"),
    (r"i\s+study\s+(?:at\s+)?(.+)",                     "school"),
    (r"i\s+graduated\s+from\s+(.+)",                    "education"),
    (r"my\s+degree\s+is\s+(?:in\s+)?(.+)",              "degree"),
    # ── Hindi / Hinglish ──────────────────────────────────
    (r"mera\s+naam\s+(?:hai\s+)?([A-Za-z][A-Za-z\s]{1,30})$", "name"),
    (r"mujhe\s+([A-Za-z][A-Za-z\s]{1,20})\s+(?:kehte|bulao|bolo)\s+hain?", "name"),
    (r"meri\s+umar\s+(?:hai\s+)?(\d+)",                 "age"),
    (r"main\s+(\d+)\s+saal\s+ka",                       "age"),
    (r"mera\s+goal\s+(?:hai\s+)?(.{5,80})",             "goal"),
    (r"mera\s+sapna\s+(?:hai\s+)?(.{5,80})",            "dream"),
    (r"main\s+([A-Za-z][A-Za-z\s]{2,20})\s+(?:hun|hoon)\s*$", "job"),
    (r"mujhe\s+(.{5,50})\s+(?:pasand|acha laga|achha laga)", "interest"),
    (r"main\s+(.{3,30})\s+mein\s+rehta",                "location"),
    (r"mera\s+ghar\s+(.{3,30})\s+mein",                 "location"),
]

# ─── Personal Info QUERY Patterns ────────────────────────

PERSONAL_INFO_QUERY_PATTERNS = [
    # Name
    r"what(?:'s| is) my name",
    r"do you know my name",
    r"what(?:'s| is) my (?:full )?name",
    r"what do you call me",
    r"what(?:'s| is) my nickname",
    # Age
    r"what(?:'s| is) my age",
    r"how old am i",
    r"when(?:'s| is) my birthday",
    r"what(?:'s| is) my birthday",
    # Goals
    r"what(?:'s| are) my goals?",
    r"what(?:'s| is) my (?:main |life |career )?goal",
    r"what(?:'s| is) my dream",
    r"what(?:'s| is) my aim",
    r"what(?:'s| is) my ambition",
    r"what am i working towards",
    r"what do i want to (?:become|be|achieve)",
    # Job
    r"what(?:'s| is) my job",
    r"what(?:'s| is) my profession",
    r"what(?:'s| is) my occupation",
    r"what do i do (?:for work|for a living|professionally)",
    r"where do i work",
    r"what(?:'s| is) my company",
    # Location
    r"where do i live",
    r"where am i from",
    r"what(?:'s| is) my (?:city|location|hometown|country)",
    # Hobbies / Interests
    r"what(?:'s| are) my hobbies?",
    r"what(?:'s| is) my hobby",
    r"what(?:'s| are) my interests?",
    r"what do i (?:like|love|enjoy)",
    r"what(?:'s| is) my passion",
    # Favorites
    r"what(?:'s| is) my favorite",
    r"what(?:'s| is) my favourite",
    # General
    r"what do you know about me",
    r"tell me about (?:me|myself)",
    r"what(?:'s| is) my (?:email|phone)",
    r"who am i",
    r"remind me (?:of )?(?:my|who)\s*$",
    r"remind me (?:of )?my (?:goals?|name|job|hobby|dream|aim|age|location|email|phone|interests?|partner|family)",
    r"what(?:'s| are) my (?:strengths?|weaknesses?|skills?)",
    r"what(?:'s| is) my (?:partner|wife|husband|girlfriend|boyfriend)(?:'s name)?",
    r"what(?:'s| is) my (?:mom|dad|mother|father)(?:'s name)?",
    # Chronological
    r"what(?:'s| was| were) (?:the )?first (?:thing|experience|message|story|event)",
    r"what did i (?:first|initially) (?:tell|share|say|mention)",
    r"what was the first (?:thing|experience|event|story) i (?:shared|told|mentioned)",
    r"what(?:'s| is) my (?:earliest|oldest|first) (?:memory|experience|message|story)",
    r"do you remember (?:the )?first (?:thing|time|experience|event)",
    r"what did i tell you (?:first|at the start|at the beginning|initially)",
    r"what was my first",
    r"recall (?:my )?first",
    r"what(?:'s| is) my oldest memory",
    # Hindi / Hinglish
    r"mera\s+naam\s+(?:kya\s+)?(?:hai|bata|batao)",
    r"mujhe\s+(?:kya|batao)\s+(?:mera|apna)\s+naam",
    r"(?:apne\s+baare\s+mein|mere\s+baare\s+mein)\s+(?:batao|bolo)",
    r"mera\s+(?:goal|sapna|kaam|job)\s+(?:kya\s+)?(?:hai|bata|batao)",
    r"main\s+(?:kaun|kya)\s+(?:hun|hoon)",
    r"(?:yaad\s+dilao|yaad\s+karo)\s+(?:mera|meri|mere)",
    r"mujhe\s+(?:kya|batao|bata)\s+(?:mera|apna)",
    r"mera\s+naam\s+kya\s+hai",
    r"meri\s+umar\s+kya\s+hai",
    r"main\s+kahan\s+(?:rehta|rehti)\s+hun",
]

# ─── Task Command Patterns ────────────────────────────────

TASK_COMMAND_PATTERNS = [
    # Explicit task creation
    r"remind\s+me\s+to\s+",
    r"remind\s+me\s+(?:about|of)\s+(?!(?:my|who)\s*$)",
    r"remind\s+me\s+my\s+\w+",
    r"add\s+(?:a\s+)?(?:task|reminder|todo)",
    r"create\s+(?:a\s+)?(?:task|reminder|todo)",
    r"set\s+(?:a\s+)?(?:reminder|alarm|task)",
    r"schedule\s+(?:a\s+)?(?:meeting|call|appointment|task|reminder)",
    r"plan\s+my\s+",
    r"make\s+(?:a\s+)?(?:to-?do|todo|task|list|plan)",
    r"don'?t\s+let\s+me\s+forget\s+to\s+",
    r"note\s+(?:down\s+)?(?:that\s+)?i\s+need\s+to\s+",
    # Need/have to + action verb
    r"i\s+need\s+to\s+(?:finish|complete|submit|send|call|email|meet|buy|fix|write|prepare|go|visit|pick|book|pay|apply|review|check|update|clean|organize|study|practice|attend|register|confirm|cancel|reschedule)",
    r"i\s+have\s+to\s+(?:finish|complete|submit|send|call|email|meet|buy|fix|write|prepare|go|visit|pick|book|pay|apply|review|check|update|clean|organize|study|practice|attend|register|confirm|cancel|reschedule)",
    r"i\s+must\s+(?:finish|complete|submit|send|call|email|meet|buy|fix|write|prepare|go|visit|pick|book|pay|apply|review|check|update|clean|organize|study|practice|attend|register|confirm)",
    r"i\s+should\s+(?:finish|complete|submit|send|call|email|meet|buy|fix|write|prepare|go|visit|pick|book|pay|apply|review|check|update|clean|organize|study|practice|attend|register|confirm)",
    # Gotta / gonna
    r"i\s+(?:gotta|gonna)\s+(?:go|do|finish|complete|submit|send|call|email|meet|buy|fix|write|prepare|visit|pick|book|pay|apply|review|check|update|clean|organize|study|practice|attend|register|confirm)",
    r"^gotta\s+\w+",
    r"i(?:'m| am)\s+gonna\s+\w+",
    # Going to + location + time
    r"i\s+need\s+to\s+go\s+(?:to\s+)?(?:the\s+)?\w+\s+(?:tomorrow|today|tonight|this week|next week|on \w+)",
    r"i\s+have\s+to\s+go\s+(?:to\s+)?(?:the\s+)?\w+\s+(?:tomorrow|today|tonight|this week|next week|on \w+)",
    r"i(?:'m| am)\s+going\s+to\s+(?:the\s+)?\w+\s+(?:tomorrow|today|tonight|this week|next week|on \w+)",
    r"i\s+should\s+go\s+(?:to\s+)?(?:the\s+)?\w+\s+(?:tomorrow|today|tonight|this week|next week)",
    # Deadline-based
    r"(?:due|deadline|submit|finish|complete)\s+(?:by|before|on)\s+(?:tomorrow|friday|monday|tuesday|wednesday|thursday|saturday|sunday|next week|end of)",
    r"i\s+need\s+to\s+(?:submit|finish|complete|send|deliver)\s+.+\s+by\s+",
    # Hindi / Hinglish
    r"mujhe\s+.+\s+(?:karna|karni|karni\s+hai|karna\s+hai)",
    r"mujhe\s+.+\s+(?:jana|jaana)\s+(?:hai|hoga)",
    r"(?:kal|aaj|parso)\s+.+\s+(?:karna|jana|attend|milna)",
    r"yaad\s+(?:dilao|karo|rakhna)\s+(?:ki\s+)?mujhe",
    r"mat\s+bhoolna\s+",
    r"bhool\s+na\s+jaana\s+",
    r"mujhe\s+yaad\s+dilana\s+",
]

# ─── Task Manage Patterns ─────────────────────────────────

TASK_MANAGE_PATTERNS = [
    # Delete / remove
    r"(?:delete|remove|cancel|drop|clear)\s+(?:the\s+)?(?:task\s+)?(?:called\s+|named\s+|about\s+)?(.+)",
    r"(?:i\s+don'?t\s+need\s+to|i\s+no\s+longer\s+need\s+to)\s+(.+)",
    r"(?:scratch|forget|ignore)\s+(?:the\s+)?(?:task\s+)?(?:about\s+)?(.+)",
    r"(?:get\s+rid\s+of|throw\s+away)\s+(?:the\s+)?(?:task\s+)?(.+)",
    # Complete / done
    r"(?:i\s+(?:finished|completed|done|did|accomplished|wrapped up))\s+(.+)",
    r"(?:mark|set)\s+(.+?)\s+(?:as\s+)?(?:done|complete|completed|finished)",
    r"(?:check\s+off|tick\s+off|cross\s+off)\s+(.+)",
    r"(.+)\s+(?:is\s+)?(?:done|complete|finished|completed)",
    r"(?:just\s+)?(?:finished|completed|done with|wrapped up)\s+(.+)",
    r"(?:i\s+already\s+)?(?:did|completed|finished)\s+(.+)",
    # Priority
    r"(?:make|set|change|mark)\s+(.+?)\s+(?:to\s+)?(?:high|urgent|important|critical)\s+priority",
    r"(?:make|set|change|mark)\s+(.+?)\s+(?:to\s+)?(?:low|not\s+urgent|minor)\s+priority",
    r"(?:make|set|change|mark)\s+(.+?)\s+(?:to\s+)?(?:medium|normal|moderate)\s+priority",
    r"(.+?)\s+(?:is\s+)?(?:urgent|high\s+priority|very\s+important|critical)",
    r"(?:prioritize|bump\s+up)\s+(.+)",
]

# ─── NOT-task phrases (override task detection) ───────────

NOT_TASK_PHRASES = [
    r"i\s+want\s+to\s+(?:talk|chat|speak|discuss|share|tell|ask|know|understand|learn|feel|think|vent|express)",
    r"i\s+want\s+to\s+(?:be\s+better|improve|grow|change|heal|recover)",
    r"i\s+(?:should|will|must)\s+(?:try|be|do\s+better|improve|focus|work\s+on\s+myself|be\s+more)",
    r"i\s+(?:feel|felt|am\s+feeling|have\s+been\s+feeling)",
    r"i\s+(?:think|believe|hope|wish|wonder|guess|suppose)",
    r"i\s+(?:like|love|enjoy|hate|dislike|prefer|miss)",
    r"i\s+(?:am|was|were|been)\s+(?:happy|sad|tired|stressed|excited|worried|anxious|bored|angry|frustrated|lonely|proud|scared|nervous|overwhelmed|depressed|grateful|content|confused|hurt|disappointed|relieved)",
    r"i(?:'m| am)\s+(?:happy|sad|tired|stressed|excited|worried|anxious|bored|angry|frustrated|lonely|proud|scared|nervous|overwhelmed|depressed|grateful|content|confused|hurt|disappointed|relieved)",
    r"i\s+(?:had|have|got|get)\s+(?:a\s+)?(?:good|bad|great|terrible|amazing|rough|tough|hard|easy|productive|lazy|fun|boring)\s+day",
    r"i\s+(?:went|go|came|come|traveled|visited)\s+(?:to\s+)?(?:the\s+)?(?:park|beach|mall|restaurant|cafe|gym|school|college|hospital|market|temple|church|mosque)\s*$",
]


# ─── Main Intent Classifier ───────────────────────────────

def detect_intent(text: str) -> dict:
    """
    Classify user message into one of five intents.

    Returns:
        {
          "intent"     : str,
          "key"        : str | None,
          "value"      : str | None,
          "confidence" : float,
        }
    """
    text_lower = text.lower().strip()
    text_clean = re.sub(r'[?.!,;:]+$', '', text_lower).strip()

    logger.debug(f"[Intent] Classifying: '{text_clean[:80]}'")

    # ── 0. Query check FIRST (before store to avoid false matches) ──
    for pattern in PERSONAL_INFO_QUERY_PATTERNS:
        if re.search(pattern, text_clean, re.IGNORECASE):
            key = _extract_query_key(text_clean)
            logger.info(f"[Intent] personal_info_query | key={key}")
            return {"intent": "personal_info_query", "key": key, "value": None, "confidence": 0.90}

    # ── 1. Personal info STORE ────────────────────────────
    for pattern, key in PERSONAL_INFO_STORE_PATTERNS:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            if key == "favorite" and len(match.groups()) == 2:
                actual_key   = f"favorite_{match.group(1).strip()}"
                actual_value = match.group(2).strip()
            else:
                actual_key   = key
                actual_value = match.group(1).strip()

            # Clean trailing filler words
            actual_value = re.sub(
                r'\s+(?:and|but|so|because|since|though|although|however|also|too|as well).*$',
                '', actual_value, flags=re.IGNORECASE
            ).strip().strip('"\'')

            # Skip if value is too short or looks like a question
            if actual_value and len(actual_value) >= 1 and '?' not in actual_value:
                logger.info(f"[Intent] personal_info_store | key={actual_key} | value={actual_value[:40]}")
                return {
                    "intent"    : "personal_info_store",
                    "key"       : actual_key,
                    "value"     : actual_value,
                    "confidence": 0.95,
                }

    # ── 2. NOT-task override ──────────────────────────────
    is_not_task = any(re.search(p, text_clean, re.IGNORECASE) for p in NOT_TASK_PHRASES)

    # ── 3. Task MANAGE ────────────────────────────────────
    if not is_not_task:
        for pattern in TASK_MANAGE_PATTERNS:
            m = re.search(pattern, text_clean, re.IGNORECASE)
            if m:
                op = "complete"
                if re.search(r"delete|remove|cancel|drop|scratch|forget|don'?t need|no longer need|get rid|throw away", text_clean):
                    op = "delete"
                elif re.search(r"high|urgent|important|critical|prioritize|bump up", text_clean):
                    op = "priority_high"
                elif re.search(r"low|not urgent|minor", text_clean):
                    op = "priority_low"
                elif re.search(r"medium|normal|moderate", text_clean):
                    op = "priority_medium"

                keyword = m.group(1).strip() if m.lastindex else ""
                logger.info(f"[Intent] task_manage | op={op} | keyword={keyword[:40]}")
                return {"intent": "task_manage", "key": op, "value": keyword, "confidence": 0.85}

    # ── 4. Task COMMAND ───────────────────────────────────
    if not is_not_task:
        for pattern in TASK_COMMAND_PATTERNS:
            if re.search(pattern, text_clean, re.IGNORECASE):
                logger.info(f"[Intent] task_command")
                return {"intent": "task_command", "key": None, "value": None, "confidence": 0.85}

    # ── 5. Default: normal chat ───────────────────────────
    logger.info(f"[Intent] normal_chat")
    return {"intent": "normal_chat", "key": None, "value": None, "confidence": 1.0}


def _extract_query_key(text: str) -> str | None:
    """Extract which personal info key is being queried."""
    text = text.lower()

    # Chronological queries
    chrono = [
        r"first (?:thing|experience|message|story|event|memory)",
        r"(?:first|initially) (?:tell|share|say|mention)",
        r"(?:earliest|oldest|first) (?:memory|experience|message|story)",
        r"tell you (?:first|at the start|at the beginning|initially)",
        r"what was my first",
        r"recall (?:my )?first",
        r"oldest memory",
    ]
    for p in chrono:
        if re.search(p, text):
            return "__earliest__"

    # Specific keys
    if re.search(r"\bname\b|\bnickname\b", text):          return "name"
    if re.search(r"\bage\b|\bold\b|\bbirthday\b", text):   return "age"
    if re.search(r"\bgoal\b|\bgoals\b|\bambition\b", text):return "goal"
    if re.search(r"\bdream\b", text):                       return "dream"
    if re.search(r"\baim\b", text):                         return "aim"
    if re.search(r"\bjob\b|\bprofession\b|\bwork\b|\boccupation\b|\bcareer\b", text): return "job"
    if re.search(r"\bhobb(?:y|ies)\b", text):               return "hobby"
    if re.search(r"\binterest\b|\bpassion\b|\blike\b|\blove\b|\benjoy\b", text): return "interest"
    if re.search(r"\bliv(?:e|ing)\b|\blocation\b|\bcity\b|\bhometown\b|\bcountry\b", text): return "location"
    if re.search(r"\bfrom\b", text):                        return "location"
    if re.search(r"\bemail\b", text):                       return "email"
    if re.search(r"\bphone\b|\bnumber\b", text):            return "phone"
    if re.search(r"\bpartner\b|\bwife\b|\bhusband\b|\bgirlfriend\b|\bboyfriend\b", text): return "partner"
    if re.search(r"\bmom\b|\bmother\b", text):              return "mother_name"
    if re.search(r"\bdad\b|\bfather\b", text):              return "father_name"
    if re.search(r"\bschool\b|\bcollege\b|\buniversity\b|\bdegree\b", text): return "education"
    if re.search(r"about me|who am i|tell me about", text): return None  # all facts

    fav = re.search(r"favou?rite\s+(\w+)", text)
    if fav:
        return f"favorite_{fav.group(1)}"

    return None

