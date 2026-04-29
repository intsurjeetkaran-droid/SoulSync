"""
SoulSync AI - Collection Classifier
Classifies every user message into one of 19 typed collections
and extracts the event_date when the message refers to a real event.

Collections:
  experience, achievement, future_plan, emotion_log, relationship,
  opinion, health, learning, gratitude, goal, habit, financial,
  decision, dream_aspiration, conflict, reflection, social_event,
  creative_work, conversation (fallback)
"""

import re
import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger("soulsync.collection_classifier")

# ── Collection patterns (ordered by specificity) ──────────

COLLECTION_PATTERNS = [

    # ── health (must be before experience — "went to gym" is health not experience) ──
    ("health", [
        r"i (?:went to the gym|worked out|exercised|ran|jogged|cycled|swam|did yoga|meditated|hit the gym)",
        r"i (?:skipped|missed) (?:gym|workout|exercise|run)",
        r"i(?:'m| am) (?:sick|ill|unwell|not feeling well|under the weather)",
        r"(?:doctor|physician|hospital|clinic|appointment) (?:said|told|recommended|prescribed)",
        r"i(?:'ve| have) been (?:sleeping|eating|drinking|exercising)",
        r"(?:sleep|diet|nutrition|fitness|weight|health) (?:has been|is|was)",
        r"i (?:started|stopped|quit) (?:eating|drinking|smoking|exercising|sleeping)",
        r"(?:gym|workout|exercise|run|jog|yoga|meditation) (?:this morning|today|yesterday|this week)",
    ]),

    # ── financial (must be before achievement — "got salary" is financial not achievement) ──
    ("financial", [
        r"i (?:got|received) (?:my )?(?:salary|paycheck|bonus|raise|payment|refund)",
        r"i (?:spent|bought|purchased|paid|invested|saved|deposited|withdrew)",
        r"(?:money|finances|budget|savings|debt|loan|credit|investment) (?:is|are|has been|situation)",
        r"i(?:'m| am) (?:saving|investing|budgeting|in debt|broke|struggling financially)",
        r"(?:financial|money) (?:stress|problem|issue|goal|plan)",
        r"i (?:got|received) (?:my )?salary",
    ]),

    # ── conflict (must be before relationship) ────────────
    ("conflict", [
        r"i (?:had|have) (?:a fight|an argument|a disagreement|a conflict|a falling out) with",
        r"(?:fight|argument|disagreement|tension|conflict|issue) (?:with|between)",
        r"(?:my|a) (?:relationship|friendship|bond) (?:with .+ )?(?:is|has been) (?:strained|tense|difficult|rocky|broken)",
        r"(?:frustrated|angry|upset) (?:with|at) (?:my|a)",
        r"(?:things are|it's been) (?:tense|difficult|awkward|weird) (?:with|between)",
        r"i had a (?:big |huge |terrible )?(?:fight|argument|disagreement|falling out) with",
        r"(?:fight|argument|conflict) with my (?:friend|mom|dad|brother|sister|partner|colleague|boss)",
    ]),

    # ── social_event (must be before experience) ──────────
    ("social_event", [
        r"(?:birthday party|wedding|reunion|dinner party|get-together)",
        r"we (?:celebrated|had a party|threw a party|organized|attended)",
        r"(?:family|friends|team|colleagues) (?:dinner|lunch|outing|gathering|celebration|reunion)",
        r"i (?:attended|went to|hosted|organized) (?:a|the|my) (?:party|wedding|birthday|celebration|event|gathering)",
        r"(?:attended|went to) (?:my |a |the )?(?:friend's|colleague's|family) (?:birthday|party|wedding|celebration)",
    ]),

    # ── gratitude (must be before emotion_log) ────────────
    ("gratitude", [
        r"i(?:'m| am) (?:grateful|thankful|appreciative) (?:for|that|to)",
        r"i (?:appreciate|value|cherish|treasure)",
        r"(?:grateful|thankful|blessed) (?:for|to have|that)",
        r"today i (?:realized|noticed) how (?:lucky|fortunate|blessed)",
        r"i(?:'m| am) (?:so |really |truly )?(?:grateful|thankful|blessed)",
    ]),

    # ── experience ────────────────────────────────────────
    ("experience", [
        r"i (?:traveled|went|visited|attended|saw|watched|experienced|did|had)\b",
        r"(?:last|this|yesterday|on \w+) i (?:went|traveled|visited|attended)",
        r"i (?:was at|was in|spent time at)",
        r"(?:trip|journey|visit|tour|vacation|holiday) (?:to|in|at)",
    ]),

    # ── achievement ───────────────────────────────────────
    ("achievement", [
        r"i (?:got|received|earned|won|passed|completed|finished|launched|published|shipped|achieved|accomplished)",
        r"i (?:was promoted|got promoted|got accepted|got selected)",
        r"(?:milestone|achievement|accomplishment|success|proud of)",
        r"i (?:finally|just) (?:finished|completed|launched|published)",
    ]),

    # ── future_plan ───────────────────────────────────────
    ("future_plan", [
        r"(?:tomorrow|next week|next month|next year|soon|upcoming) i(?:'m| am| will| plan)",
        r"i(?:'m| am) (?:planning|going to|about to|thinking of)",
        r"i will (?:be|go|do|attend|visit|travel|start|try)",
        r"(?:planning|plan) to (?:go|visit|travel|attend|start)",
    ]),

    # ── emotion_log ───────────────────────────────────────
    ("emotion_log", [
        r"i(?:'m| am| feel| felt) (?:feeling |really |so |very |quite )?(?:happy|sad|stressed|anxious|excited|angry|frustrated|overwhelmed|lonely|depressed|proud|scared|nervous|hopeful|exhausted|tired|bored|confused|hurt|disappointed|relieved|content|joyful|melancholy|numb)",
        r"i(?:'m| am) (?:really |so |very )?(?:stressed|anxious|overwhelmed|sad|depressed|lonely|scared|nervous|excited|happy|tired|exhausted|frustrated|angry|bored|confused|hurt|disappointed|relieved|content|proud)",
        r"(?:today|this week|lately|recently) (?:has been|was|is) (?:tough|hard|great|amazing|terrible|rough|wonderful|difficult)",
        r"i(?:'ve| have) been feeling",
        r"my (?:mood|emotions|feelings) (?:are|have been|is)",
        r"feeling (?:really |so |very )?(?:stressed|anxious|overwhelmed|sad|happy|tired|excited|frustrated|lonely|scared|nervous|proud|hurt|disappointed|relieved|content)",
    ]),

    # ── relationship ──────────────────────────────────────
    ("relationship", [
        r"my (?:friend|best friend|mom|dad|mother|father|sister|brother|wife|husband|partner|girlfriend|boyfriend|colleague|manager|boss|mentor|cousin|aunt|uncle|grandma|grandpa)\b",
        r"(?:called|texted|met|visited|talked to|spoke with|had dinner with|hung out with) (?:my|a friend|an old friend)",
        r"(?:my|a) (?:friend|family member|colleague) (?:said|told|asked|helped|supported|hurt|disappointed)",
    ]),

    # ── opinion ───────────────────────────────────────────
    ("opinion", [
        r"i (?:think|believe|feel that|reckon|consider|find that|am convinced)",
        r"in my (?:opinion|view|experience)",
        r"i (?:strongly|firmly|genuinely) (?:believe|think|feel)",
        r"(?:my opinion|my view|my perspective|my take) (?:on|is|about)",
        r"i (?:don't|do not) (?:like|agree|think|believe|support)",
    ]),

    # ── learning ──────────────────────────────────────────
    ("learning", [
        r"i(?:'m| am) (?:learning|studying|reading|taking a course|watching a tutorial)",
        r"i (?:finished|completed|started) (?:reading|a book|a course|a tutorial|a class)",
        r"i (?:read|studied|learned|discovered|understood)",
        r"(?:book|course|tutorial|class|lecture|workshop|seminar) (?:about|on|called)",
    ]),

    # ── goal ──────────────────────────────────────────────
    ("goal", [
        r"my (?:long.term |life |career |personal )?goal (?:is|has been|was)",
        r"i(?:'m| am) working (?:towards|toward|on achieving)",
        r"i (?:aspire|aim|strive) to",
        r"(?:someday|one day|eventually|in the future) i (?:want|hope|plan) to (?:become|be|achieve|build|create)",
        r"my (?:ambition|aspiration|vision) (?:is|has always been)",
    ]),

    # ── habit ─────────────────────────────────────────────
    ("habit", [
        r"i(?:'ve| have) been (?:doing|practicing|maintaining|keeping up with) .+ (?:every day|daily|every morning|every night|consistently|for \d+ (?:days|weeks))",
        r"i(?:'m| am) (?:trying to|working on) (?:building|developing|forming|breaking|quitting)",
        r"(?:every morning|every night|every day|daily) i",
        r"i(?:'ve| have) (?:kept up|maintained|stuck to) my",
        r"(?:streak|routine|habit|ritual|practice) (?:of|for|with)",
        r"i(?:'ve| have) been (?:meditating|journaling|waking up|going to bed|reading|exercising) (?:every|daily|each)",
        r"for \d+ (?:days|weeks|months) i(?:'ve| have) been",
    ]),

    # ── decision ──────────────────────────────────────────
    ("decision", [
        r"i (?:decided|chose|made a decision|made up my mind|resolved) to",
        r"i(?:'m| am) (?:torn|conflicted|undecided) (?:between|about|on)",
        r"(?:big|important|difficult|tough|hard) decision",
        r"i (?:finally|ultimately|eventually) (?:decided|chose|picked|went with)",
        r"should i (?:or|vs\.?)",
    ]),

    # ── dream_aspiration ──────────────────────────────────
    ("dream_aspiration", [
        r"i(?:'ve| have) always (?:wanted|dreamed|wished) to",
        r"(?:my dream|my wish|my fantasy|my vision) (?:is|has always been|would be)",
        r"(?:wouldn't it be|imagine if|what if) (?:i could|i was|i had)",
        r"i (?:wish|hope|dream) (?:i could|i was|i had|someday)",
        r"(?:bucket list|life goal|dream of)",
    ]),

    # ── reflection ────────────────────────────────────────
    ("reflection", [
        r"i (?:realized|noticed|understood|discovered|recognized) (?:that )?i(?:'ve| have| am| was)",
        r"(?:looking back|in retrospect|thinking about it|reflecting on)",
        r"i(?:'ve| have) (?:learned|grown|changed|evolved|matured)",
        r"i (?:understand|see|know) now (?:that|why|how)",
        r"(?:lesson|insight|realization|epiphany|self-awareness)",
    ]),

    # ── creative_work ─────────────────────────────────────
    ("creative_work", [
        r"i (?:wrote|painted|drew|designed|composed|built|coded|created|made|crafted|published|recorded)",
        r"(?:my|the) (?:novel|book|painting|drawing|song|music|app|project|design|artwork|blog|article|poem)",
        r"i(?:'m| am) (?:working on|creating|building|writing|designing|composing)",
        r"(?:creative|artistic|side project|passion project|indie|freelance) (?:work|project|piece)",
    ]),
]

# ── Date extraction patterns ───────────────────────────────

DATE_PATTERNS = [
    # Explicit dates: "March 23", "23rd March", "March 23, 2026"
    (r"(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(\d{4}))?",
     "month_day"),
    (r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:,?\s*(\d{4}))?",
     "day_month"),
    # Relative: yesterday, today, last week, etc.
    (r"\byesterday\b",   "yesterday"),
    (r"\btoday\b",       "today"),
    (r"\blast week\b",   "last_week"),
    (r"\blast month\b",  "last_month"),
    (r"\btomorrow\b",    "tomorrow"),
    (r"\bnext week\b",   "next_week"),
    (r"\bnext month\b",  "next_month"),
    # ISO: 2026-03-23
    (r"(\d{4})-(\d{2})-(\d{2})", "iso"),
]

MONTH_MAP = {
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12
}


def extract_event_date(text: str) -> Optional[date]:
    """
    Extract the actual event date from a message.
    Returns None if no date found.
    """
    text_lower = text.lower()
    today = date.today()

    for pattern, dtype in DATE_PATTERNS:
        m = re.search(pattern, text_lower)
        if not m:
            continue

        try:
            if dtype == "yesterday":
                return today - timedelta(days=1)
            if dtype == "today":
                return today
            if dtype == "tomorrow":
                return today + timedelta(days=1)
            if dtype == "last_week":
                return today - timedelta(weeks=1)
            if dtype == "last_month":
                return (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            if dtype == "next_week":
                return today + timedelta(weeks=1)
            if dtype == "next_month":
                return (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            if dtype == "iso":
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if dtype == "month_day":
                month_str = re.search(
                    r"(january|february|march|april|may|june|july|august|september|october|november|december)",
                    text_lower
                ).group(1)
                month = MONTH_MAP[month_str]
                day   = int(m.group(1))
                year  = int(m.group(2)) if m.group(2) else today.year
                return date(year, month, day)
            if dtype == "day_month":
                day = int(m.group(1))
                month_str = re.search(
                    r"(january|february|march|april|may|june|july|august|september|october|november|december)",
                    text_lower
                ).group(1)
                month = MONTH_MAP[month_str]
                year  = today.year
                return date(year, month, day)
        except Exception:
            continue

    return None


def classify_collection(text: str) -> str:
    """
    Classify a user message into one of 19 typed collections.
    Returns the collection name string.
    """
    text_lower = text.lower()

    for collection, patterns in COLLECTION_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.debug(f"[Classifier] '{text[:50]}' → {collection}")
                return collection

    logger.debug(f"[Classifier] '{text[:50]}' → conversation (fallback)")
    return "conversation"


def classify_and_extract(text: str) -> dict:
    """
    Classify message into collection AND extract event_date.

    Returns:
        {
          "collection" : str,
          "event_date" : date | None,
          "importance" : int (1-10)
        }
    """
    collection = classify_collection(text)
    event_date = extract_event_date(text)

    # Importance scoring by collection type
    importance_map = {
        "achievement"     : 9,
        "experience"      : 8,
        "decision"        : 8,
        "conflict"        : 7,
        "reflection"      : 7,
        "goal"            : 7,
        "social_event"    : 6,
        "relationship"    : 6,
        "creative_work"   : 6,
        "future_plan"     : 6,
        "emotion_log"     : 5,
        "health"          : 5,
        "habit"           : 5,
        "financial"       : 5,
        "learning"        : 5,
        "gratitude"       : 5,
        "dream_aspiration": 4,
        "opinion"         : 4,
        "conversation"    : 3,
    }

    return {
        "collection" : collection,
        "event_date" : event_date,
        "importance" : importance_map.get(collection, 5),
    }
