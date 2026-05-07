"""
SoulSync AI - Collection Classifier
32 collections covering every dimension of human life.
"""

import re
import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger("soulsync.collection_classifier")

ALL_COLLECTIONS = [
    "identity_fact",
    "personality_trait",
    "belief_value",
    "self_reflection",
    "emotion_log",
    "mental_health",
    "gratitude",
    "fear_worry",
    "relationship",
    "conflict",
    "social_event",
    "loss_grief",
    "experience",
    "achievement",
    "failure_setback",
    "decision",
    "goal",
    "future_plan",
    "dream_aspiration",
    "habit",
    "health",
    "work_career",
    "financial",
    "learning",
    "creative_work",
    "opinion",
    "life_lesson",
    "milestone",
    "surprise",
    "humor_fun",
    "personal_fact",
    "conversation",
]


COLLECTION_PATTERNS = [

    # ── IDENTITY & SELF ───────────────────────────────────

    ("identity_fact", [
        r"my name is|i am called|call me|i go by",
        r"i(?:'m| am) \d+ years old|my age is",
        r"i(?:'m| am) (?:from|based in|living in|located in)",
        r"i work (?:as|at|for)|my job is|my profession is",
        r"my (?:email|phone|address|birthday|nationality|ethnicity) is",
    ]),

    ("personality_trait", [
        r"i(?:'m| am) (?:an? )?(?:introvert|extrovert|ambivert|empath|perfectionist|overthinker|people.pleaser)",
        r"i (?:tend to|always|usually|often|naturally) (?:overthink|procrastinate|avoid|seek|need)",
        r"(?:my personality|my character|my nature|who i am) (?:is|makes me|means)",
        r"i(?:'ve| have) always been (?:the kind of person|someone who|a person who)",
        r"(?:people say|others say|i know) i(?:'m| am) (?:very|quite|really|too) \w+",
    ]),

    ("belief_value", [
        r"i (?:believe in|value|stand for|am committed to|live by|follow)",
        r"(?:my faith|my religion|my spirituality|my values|my principles|my ethics)",
        r"(?:god|allah|jesus|buddha|universe|karma|spirituality|religion|faith|prayer)",
        r"(?:morally|ethically|philosophically) i (?:believe|think|feel|stand)",
        r"(?:my core belief|my worldview|my philosophy|my principles) (?:is|are)",
    ]),

    ("self_reflection", [
        r"(?:looking back|in retrospect|reflecting on|thinking about it now)",
        r"i (?:realized|noticed|understood|discovered|recognized|accepted) (?:that )?i",
        r"i(?:'ve| have) (?:learned|grown|changed|evolved|matured|improved)",
        r"i (?:understand|see|know) now (?:that|why|how|what)",
        r"(?:lesson|insight|realization|epiphany|self.awareness|growth moment)",
        r"i need to (?:work on|improve|change|accept|let go of)",
    ]),

    # ── EMOTIONS & MENTAL HEALTH ──────────────────────────

    ("mental_health", [
        r"(?:anxiety|depression|panic attack|mental health|therapy|therapist|counseling|psychiatrist|burnout|breakdown)",
        r"i(?:'m| am) (?:seeing|going to) (?:a therapist|therapy|counseling)",
        r"i(?:'ve| have) been (?:struggling|dealing) with (?:anxiety|depression|mental)",
        r"(?:suicidal|self.harm|eating disorder|ocd|ptsd|bipolar)",
        r"(?:mental|emotional) (?:health|breakdown|crisis|exhaustion|burnout)",
    ]),

    ("fear_worry", [
        r"i(?:'m| am) (?:scared|afraid|terrified|worried|nervous|anxious) (?:about|of|that)",
        r"i am (?:really |so |very )?(?:scared|afraid|terrified|worried|nervous|anxious)",
        r"i am scared of",
        r"i am (?:scared|afraid|worried|anxious|nervous|terrified)",
        r"feeling (?:really |so |very )?(?:scared|afraid|terrified|worried|nervous|anxious)",
        r"(?:scared of|afraid of|worried about|anxious about) (?:losing|failing|not|the)",
        r"(?:what if|i keep thinking|i can't stop worrying|worst case scenario)",
        r"(?:fear|phobia|nightmare|dread|dreading|apprehensive) (?:of|about)",
        r"(?:keeps me up at night|can't sleep because|overthinking about)",
        r"i(?:'m| am) (?:terrified|petrified|dreading|dreading) (?:of|about|that)",
    ]),

    ("emotion_log", [
        r"i(?:'m| am| feel| felt) (?:feeling |really |so |very |quite )?(?:happy|sad|stressed|excited|angry|frustrated|overwhelmed|lonely|proud|hopeful|exhausted|tired|bored|confused|hurt|disappointed|relieved|content|joyful|melancholy|numb|empty|lost)",
        r"(?:today|this week|lately|recently) (?:has been|was|is) (?:tough|hard|great|amazing|terrible|rough|wonderful|difficult|emotional)",
        r"i(?:'ve| have) been feeling (?:really |so |very )?",
        r"my (?:mood|emotions|feelings) (?:are|have been|is)",
    ]),

    ("gratitude", [
        r"i(?:'m| am) (?:grateful|thankful|appreciative|blessed) (?:for|that|to)",
        r"i (?:appreciate|value|cherish|treasure|am thankful for)",
        r"(?:grateful|thankful|blessed) (?:for|to have|that|because)",
        r"today i (?:realized|noticed) how (?:lucky|fortunate|blessed)",
        r"(?:counting my blessings|silver lining|bright side|good things in my life)",
    ]),

    # ── RELATIONSHIPS & SOCIAL ────────────────────────────

    ("loss_grief", [
        r"(?:passed away|died|death|funeral|mourning|grieving|grief|lost (?:my|a))",
        r"(?:my|a) (?:friend|family|mom|dad|grandma|grandpa|pet|dog|cat) (?:passed|died|is gone)",
        r"(?:breakup|broke up|ended|separation|divorce|left me|dumped)",
        r"i(?:'m| am) (?:grieving|mourning|heartbroken|devastated) (?:over|about|because)",
        r"(?:miss|missing) (?:them|him|her|my) (?:so much|terribly|deeply)",
    ]),

    ("conflict", [
        r"i (?:had|have) (?:a fight|an argument|a disagreement|a conflict|a falling out) with",
        r"(?:fight|argument|disagreement|tension|conflict|issue) (?:with|between)",
        r"(?:frustrated|angry|upset|annoyed|irritated) (?:with|at) (?:my|a|the)",
        r"(?:things are|it's been) (?:tense|difficult|awkward|weird|strained) (?:with|between)",
        r"i had a (?:big|huge|terrible|bad) (?:fight|argument|disagreement|falling out) with",
    ]),

    ("social_event", [
        r"(?:birthday party|wedding|reunion|dinner party|get.together|hangout|meetup)",
        r"we (?:celebrated|had a party|threw a party|organized|attended|went out)",
        r"(?:family|friends|team|colleagues) (?:dinner|lunch|outing|gathering|celebration|reunion)",
        r"i (?:attended|went to|hosted|organized) (?:a|the|my) (?:party|wedding|birthday|celebration|event|gathering)",
    ]),

    ("relationship", [
        r"my (?:friend|best friend|mom|dad|mother|father|sister|brother|wife|husband|partner|girlfriend|boyfriend|colleague|manager|boss|mentor|cousin|aunt|uncle|grandma|grandpa)\b",
        r"(?:called|texted|met|visited|talked to|spoke with|had dinner with|hung out with)",
        r"(?:my|a) (?:friend|family member|colleague) (?:said|told|asked|helped|supported|hurt)",
    ]),

    # ── HEALTH & BODY ─────────────────────────────────────

    ("health", [
        r"i (?:went to the gym|worked out|exercised|ran|jogged|cycled|swam|did yoga|meditated|hit the gym)",
        r"i (?:skipped|missed) (?:gym|workout|exercise|run|yoga)",
        r"i(?:'m| am) (?:sick|ill|unwell|not feeling well|under the weather|recovering)",
        r"(?:doctor|physician|hospital|clinic|appointment|diagnosis|prescription|medicine)",
        r"(?:sleep|diet|nutrition|fitness|weight|health|calories|steps|water intake)",
        r"i (?:started|stopped|quit) (?:eating|drinking|smoking|exercising|sleeping)",
        r"(?:gym|workout|exercise|run|jog|yoga|meditation) (?:this morning|today|yesterday|this week)",
    ]),

    ("decision", [
        r"i (?:decided|chose|made a decision|made up my mind|resolved|committed) to",
        r"i(?:'m| am) (?:torn|conflicted|undecided|on the fence) (?:between|about|on)",
        r"(?:big|important|difficult|tough|hard|life.changing) decision",
        r"i (?:finally|ultimately|eventually) (?:decided|chose|picked|went with|settled on)",
        r"i decided to (?:quit|leave|resign|move|change|switch|start|stop|end)",
    ]),

    # ── LIFE EVENTS & EXPERIENCES ─────────────────────────

    ("achievement", [
        r"i (?:got|received|earned|won|passed|completed|finished|launched|published|shipped|achieved|accomplished)",
        r"i (?:was promoted|got promoted|got accepted|got selected|got hired)",
        r"(?:milestone|achievement|accomplishment|success|proud of|nailed it|crushed it)",
        r"i (?:finally|just) (?:finished|completed|launched|published|shipped|passed)",
        r"i (?:got|received) (?:my )?(?:promotion|raise|award|certificate|degree|offer letter)",
    ]),

    ("failure_setback", [
        r"i (?:failed|didn't pass|got rejected|lost|missed|couldn't|wasn't able to)",
        r"(?:rejection|failure|setback|disappointment|didn't work out|fell through)",
        r"i (?:was rejected|got rejected|didn't get|wasn't selected|didn't make it)",
        r"(?:things didn't|it didn't|plans fell|everything went) (?:work out|go as planned|wrong)",
        r"(?:failed|flopped|bombed|tanked|crashed) (?:my|the|an|a)",
    ]),

    # ── WORK & CAREER ─────────────────────────────────────

    ("work_career", [
        r"(?:at work|my boss|my manager|my team|my colleague|my client|my project)",
        r"i (?:got fired|quit my job|resigned|was laid off)",
        r"(?:meeting|presentation|deadline|sprint|standup|review|appraisal|interview)",
        r"(?:work|office|career|professional) (?:stress|pressure|challenge|win|loss|update)",
        r"i (?:started|joined|left|switched) (?:a new job|the company|the team)",
        r"(?:my startup|my business|my company|my side hustle|freelance project)",
        r"(?:work|office|job) (?:is|was|has been) (?:stressful|busy|hectic|great|terrible|overwhelming)",
    ]),

    ("milestone", [
        r"(?:birthday|anniversary|graduation|wedding day|first day|last day|retirement)",
        r"(?:turned|turning) \d+ (?:today|yesterday|this week)",
        r"(?:my|our) \d+(?:st|nd|rd|th)? (?:anniversary|birthday|year)",
        r"(?:first time|for the first time|never done this before|milestone)",
        r"(?:100th|50th|10th|5th|1st|2nd|3rd) (?:day|week|month|year|time)",
    ]),

    ("experience", [
        r"i (?:traveled|went|visited|attended|saw|watched|experienced|did|had)\b",
        r"(?:last|this|yesterday) i (?:went|traveled|visited|attended)",
        r"i (?:was at|was in|spent time at|explored|discovered)",
        r"(?:trip|journey|visit|tour|vacation|holiday|adventure|road trip) (?:to|in|at)",
    ]),

    ("surprise", [
        r"(?:surprisingly|unexpectedly|out of nowhere|randomly|suddenly|to my surprise)",
        r"i (?:was surprised|got surprised|couldn't believe|was shocked|was amazed)",
        r"(?:unexpected|surprise|shocking|unbelievable|out of the blue)",
        r"(?:never expected|didn't expect|didn't see coming|caught me off guard)",
    ]),

    # ── GOALS & FUTURE ────────────────────────────────────

    ("goal", [
        r"my (?:long.term|life|career|personal|main|biggest) goal (?:is|has been|was)",
        r"my goal is to",
        r"i(?:'m| am) working (?:towards|toward|on achieving|on reaching)",
        r"i (?:aspire|aim|strive|want) to (?:become|be|achieve|build|create|reach)",
        r"(?:someday|one day|eventually|in the future) i (?:want|hope|plan) to",
        r"my (?:ambition|aspiration|vision|mission) (?:is|has always been)",
    ]),

    ("future_plan", [
        r"(?:tomorrow|next week|next month|next year|soon|upcoming) i(?:'m| am| will| plan)",
        r"i(?:'m| am) (?:planning|going to|about to|thinking of|considering)",
        r"i will (?:be|go|do|attend|visit|travel|start|try|apply|submit)",
        r"(?:planning|plan) to (?:go|visit|travel|attend|start|apply|move)",
    ]),

    ("dream_aspiration", [
        r"i(?:'ve| have) always (?:wanted|dreamed|wished) to",
        r"(?:my dream|my wish|my fantasy|my vision|my bucket list) (?:is|has always been|would be)",
        r"(?:wouldn't it be|imagine if|what if) (?:i could|i was|i had)",
        r"i (?:wish|hope|dream) (?:i could|i was|i had|someday|one day)",
        r"(?:bucket list|life goal|dream of|always dreamed)",
    ]),

    ("habit", [
        r"i(?:'ve| have) been (?:doing|practicing|maintaining|keeping up with) .+ (?:every day|daily|every morning|every night|consistently)",
        r"i(?:'m| am) (?:trying to|working on) (?:building|developing|forming|breaking|quitting)",
        r"(?:every morning|every night|every day|daily|each day) i",
        r"(?:streak|routine|habit|ritual|practice|discipline) (?:of|for|with)",
        r"for \d+ (?:days|weeks|months) i(?:'ve| have) been",
        r"i have been (?:meditating|journaling|waking up|going to bed|reading|exercising|running|working out) (?:every|daily|each|for \d+)",
    ]),

    # ── FINANCIAL ─────────────────────────────────────────

    ("financial", [
        r"i (?:got|received) (?:my )?(?:salary|paycheck|bonus|raise|payment|refund|stipend)",
        r"i (?:spent|bought|purchased|paid|invested|saved|deposited|withdrew|transferred)",
        r"(?:money|finances|budget|savings|debt|loan|credit|investment|expense) (?:is|are|has been)",
        r"i(?:'m| am) (?:saving|investing|budgeting|in debt|broke|struggling financially)",
        r"(?:financial|money) (?:stress|problem|issue|goal|plan|freedom|independence)",
        r"(?:rent|mortgage|emi|bill|tax|insurance|subscription) (?:is|was|due|paid)",
    ]),

    # ── LEARNING & GROWTH ─────────────────────────────────

    ("life_lesson", [
        r"(?:the lesson|what i learned|what this taught me|the takeaway|the moral)",
        r"(?:advice|wisdom|tip|reminder) (?:to myself|for anyone|i wish i knew)",
        r"if i could (?:go back|tell my younger self|do it again)",
        r"(?:never again|from now on|i promise myself|i swore|i vowed)",
        r"(?:hard way|painful lesson|learned the hard way|mistake taught me)",
        r"(?:trust takes|life taught|experience showed|i now know) (?:me |that |years)",
        r"i learned the hard way",
        r"(?:years to build|years to earn|years to gain)",
    ]),

    ("learning", [
        r"i(?:'m| am) (?:learning|studying|reading|taking a course|watching a tutorial|practicing)",
        r"i (?:finished|completed|started) (?:reading|a book|a course|a tutorial|a class|a workshop)",
        r"i (?:read|studied|learned|discovered|understood|figured out)",
        r"(?:book|course|tutorial|class|lecture|workshop|seminar|podcast) (?:about|on|called|titled)",
    ]),

    ("creative_work", [
        r"i (?:wrote|painted|drew|designed|composed|built|coded|created|made|crafted|published|recorded|filmed)",
        r"(?:my|the) (?:novel|book|painting|drawing|song|music|app|project|design|artwork|blog|article|poem|game|film)",
        r"i(?:'m| am) (?:working on|creating|building|writing|designing|composing|developing)",
        r"(?:creative|artistic|side project|passion project|indie|freelance) (?:work|project|piece)",
    ]),

    # ── OPINIONS & THOUGHTS ───────────────────────────────

    ("opinion", [
        r"i (?:think|believe|feel that|reckon|consider|find that|am convinced)",
        r"in my (?:opinion|view|experience|perspective)",
        r"i (?:strongly|firmly|genuinely|honestly) (?:believe|think|feel|disagree|agree)",
        r"(?:my opinion|my view|my perspective|my take|my stance) (?:on|is|about)",
        r"i (?:don't|do not) (?:like|agree|think|believe|support|approve of)",
    ]),

    # ── SPECIAL MOMENTS ───────────────────────────────────

    ("humor_fun", [
        r"(?:lol|lmao|haha|hehe|funny|hilarious|laughed|cracked up|burst out laughing)",
        r"(?:joke|prank|meme|comedy|stand.up|funny moment|embarrassing moment)",
        r"(?:we laughed|couldn't stop laughing|had a good laugh|so funny)",
        r"(?:silly|goofy|ridiculous|absurd|ironic|sarcastic) (?:moment|thing|situation)",
    ]),

    ("personal_fact", [
        r"my (?:name|age|birthday|nationality|hometown|city|country|language|religion|ethnicity) is",
        r"i (?:identify as|consider myself|see myself as)",
    ]),
]

# ── Importance scores ─────────────────────────────────────

IMPORTANCE_MAP = {
    "achievement"      : 9,
    "milestone"        : 9,
    "loss_grief"       : 9,
    "failure_setback"  : 8,
    "experience"       : 8,
    "decision"         : 8,
    "conflict"         : 7,
    "self_reflection"  : 7,
    "goal"             : 7,
    "life_lesson"      : 7,
    "work_career"      : 6,
    "social_event"     : 6,
    "relationship"     : 6,
    "creative_work"    : 6,
    "future_plan"      : 6,
    "mental_health"    : 6,
    "surprise"         : 6,
    "emotion_log"      : 5,
    "health"           : 5,
    "habit"            : 5,
    "financial"        : 5,
    "learning"         : 5,
    "gratitude"        : 5,
    "belief_value"     : 5,
    "personality_trait": 5,
    "fear_worry"       : 5,
    "dream_aspiration" : 4,
    "opinion"          : 4,
    "humor_fun"        : 4,
    "identity_fact"    : 4,
    "personal_fact"    : 4,
    "conversation"     : 3,
}

# ── Date extraction ───────────────────────────────────────

MONTH_MAP = {
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12
}

DATE_PATTERNS = [
    (r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(\d{4}))?", "month_day"),
    (r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)(?:,?\s*(\d{4}))?", "day_month"),
    (r"\byesterday\b",  "yesterday"),
    (r"\btoday\b",      "today"),
    (r"\blast week\b",  "last_week"),
    (r"\blast month\b", "last_month"),
    (r"\btomorrow\b",   "tomorrow"),
    (r"\bnext week\b",  "next_week"),
    (r"\bnext month\b", "next_month"),
    (r"(\d{4})-(\d{2})-(\d{2})", "iso"),
]


def extract_event_date(text: str) -> Optional[date]:
    """Extract the actual event date from a message."""
    text_lower = text.lower()
    today = date.today()
    for pattern, dtype in DATE_PATTERNS:
        m = re.search(pattern, text_lower)
        if not m:
            continue
        try:
            if dtype == "yesterday":  return today - timedelta(days=1)
            if dtype == "today":      return today
            if dtype == "tomorrow":   return today + timedelta(days=1)
            if dtype == "last_week":  return today - timedelta(weeks=1)
            if dtype == "last_month": return (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            if dtype == "next_week":  return today + timedelta(weeks=1)
            if dtype == "next_month": return (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            if dtype == "iso":        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if dtype == "month_day":
                month = MONTH_MAP[m.group(1)]
                day   = int(m.group(2))
                year  = int(m.group(3)) if m.group(3) else today.year
                return date(year, month, day)
            if dtype == "day_month":
                day   = int(m.group(1))
                month = MONTH_MAP[m.group(2)]
                year  = int(m.group(3)) if m.group(3) else today.year
                return date(year, month, day)
        except Exception:
            continue
    return None


def classify_collection(text: str) -> str:
    """Classify a user message into one of 32 typed collections."""
    text_lower = text.lower()
    for collection, patterns in COLLECTION_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return collection
    return "conversation"


def classify_and_extract(text: str) -> dict:
    """
    Classify message into collection AND extract event_date and importance.

    Returns:
        {
          "collection" : str,
          "event_date" : date | None,
          "importance" : int (1-10),
          "summary"    : str,
          "extra"      : dict,
        }
    """
    collection = classify_collection(text)
    event_date = extract_event_date(text)
    return {
        "collection" : collection,
        "event_date" : event_date,
        "importance" : IMPORTANCE_MAP.get(collection, 5),
        "summary"    : "",
        "extra"      : {},
    }
