"""
SoulSync AI — MongoDB Seed Script
Seeds 10 rich users with 1 year of realistic data:
  - User profile + personal facts
  - ~600 messages (conversations) spread across 12 months
  - 52 weekly mood logs
  - 4 tasks (mixed priority/status)
  - Activities extracted from messages
  - FAISS vector embeddings

Run from project root:
    python soulsync-ai/scripts/seed_mongo.py
"""

import asyncio
import sys
import os
import uuid
import random
from datetime import datetime, timedelta, date
from passlib.context import CryptContext

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB",  "soulsync_db")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)

# ── 10 Users ──────────────────────────────────────────────

USERS = [
    {
        "name": "Rohit Sharma", "email": "rohit@soulsync.ai", "password": "rohit123",
        "user_id": "rohit_seed", "age": "24", "job": "Software Engineer",
        "location": "Mumbai, India", "goal": "Become a senior engineer and launch a startup",
        "hobby": "Guitar and tech blogs",
        "friends": ["Arjun", "Priya", "Neha"],
        "family": {"mom": "March 12", "dad": "July 8", "sister": "November 3"},
        "personality": "ambitious, sometimes stressed about deadlines, loves coding",
    },
    {
        "name": "Aisha Khan", "email": "aisha@soulsync.ai", "password": "aisha123",
        "user_id": "aisha_seed", "age": "27", "job": "UX Designer",
        "location": "Bangalore, India", "goal": "Design products that improve people's lives",
        "hobby": "Painting and yoga",
        "friends": ["Zara", "Meera", "Riya"],
        "family": {"mom": "April 20", "dad": "September 5", "brother": "January 15"},
        "personality": "creative, empathetic, anxious before presentations",
    },
    {
        "name": "Marcus Johnson", "email": "marcus@soulsync.ai", "password": "marcus123",
        "user_id": "marcus_seed", "age": "31", "job": "Product Manager",
        "location": "Lagos, Nigeria", "goal": "Build a product used by 1 million people",
        "hobby": "Basketball and podcasting",
        "friends": ["Tunde", "Emeka", "Chidi"],
        "family": {"mom": "February 14", "dad": "October 22", "wife": "June 30"},
        "personality": "strategic, driven, loves data and metrics",
    },
    {
        "name": "Priya Patel", "email": "priya@soulsync.ai", "password": "priya123",
        "user_id": "priya_seed", "age": "22", "job": "Medical Student",
        "location": "Ahmedabad, India", "goal": "Become a cardiologist and help underserved communities",
        "hobby": "Cooking and classical dance",
        "friends": ["Sneha", "Kavya", "Ananya"],
        "family": {"mom": "May 18", "dad": "December 1", "brother": "August 25"},
        "personality": "hardworking, sleep-deprived, passionate about medicine",
    },
    {
        "name": "Sam Rivera", "email": "sam@soulsync.ai", "password": "sam12345",
        "user_id": "sam_seed", "age": "29", "job": "Freelance Writer",
        "location": "Mexico City, Mexico", "goal": "Publish first novel and build a sustainable writing career",
        "hobby": "Hiking and photography",
        "friends": ["Carlos", "Sofia", "Diego"],
        "family": {"mom": "March 28", "dad": "July 4", "sister": "October 10"},
        "personality": "creative, procrastinates sometimes, loves nature",
    },
    {
        "name": "Elena Rodriguez", "email": "elena@soulsync.ai", "password": "elena123",
        "user_id": "elena_seed", "age": "30", "job": "Marketing Manager",
        "location": "Barcelona, Spain", "goal": "Launch her own digital marketing agency by 2027",
        "hobby": "Photography and travel blogging",
        "friends": ["Sofia", "Carlos", "Maria"],
        "family": {"mom": "March 15", "dad": "July 22", "sister": "November 8"},
        "personality": "ambitious, social, loves travel and new experiences",
    },
    {
        "name": "David Chen", "email": "david@soulsync.ai", "password": "david123",
        "user_id": "david_seed", "age": "35", "job": "Data Scientist",
        "location": "Toronto, Canada", "goal": "Publish research in AI ethics and build tools for social good",
        "hobby": "Chess and reading philosophy",
        "friends": ["James", "Lisa", "Kevin"],
        "family": {"wife": "April 18", "son": "September 5", "anniversary": "May 20"},
        "personality": "analytical, thoughtful, cares deeply about ethics",
    },
    {
        "name": "Fatima Al-Mansoori", "email": "fatima@soulsync.ai", "password": "fatima123",
        "user_id": "fatima_seed", "age": "28", "job": "Civil Engineer",
        "location": "Dubai, UAE", "goal": "Design sustainable infrastructure for developing countries",
        "hobby": "Calligraphy and volunteering",
        "friends": ["Layla", "Ahmed", "Noor"],
        "family": {"mom": "February 10", "dad": "August 14", "brother": "December 3"},
        "personality": "disciplined, compassionate, driven by purpose",
    },
    {
        "name": "Jake Morrison", "email": "jake@soulsync.ai", "password": "jake1234",
        "user_id": "jake_seed", "age": "33", "job": "High School Teacher",
        "location": "Portland, Oregon, USA", "goal": "Write a book about teaching methods and inspire educators",
        "hobby": "Running marathons and playing piano",
        "friends": ["Tom", "Sarah", "Mike"],
        "family": {"mom": "March 8", "dad": "October 12", "girlfriend": "June 30"},
        "personality": "patient, inspiring, loves connecting with students",
    },
    {
        "name": "Yuki Tanaka", "email": "yuki@soulsync.ai", "password": "yuki1234",
        "user_id": "yuki_seed", "age": "26", "job": "Indie Game Developer",
        "location": "Kyoto, Japan", "goal": "Create an indie game that tells a meaningful story",
        "hobby": "Anime, manga, and pixel art",
        "friends": ["Kenji", "Hana", "Ryo"],
        "family": {"mom": "April 5", "dad": "September 18", "grandma": "January 20"},
        "personality": "creative, introverted, passionate about storytelling",
    },
]

# ── Message templates per user ────────────────────────────

def get_messages_for_user(user: dict, year: int = 2025) -> list:
    """Generate ~600 realistic messages spread across 12 months."""
    name     = user["name"].split()[0]
    job      = user["job"]
    goal     = user["goal"]
    hobby    = user["hobby"]
    location = user["location"]
    friends  = user["friends"]
    family   = user["family"]
    persona  = user["personality"]

    # Base message pool — varied, realistic, personal
    base_messages = [
        # Identity / personal facts
        f"My name is {name} and I'm a {job} based in {location}.",
        f"My goal is to {goal}.",
        f"I love {hobby}. It really helps me unwind.",
        f"I'm {user['age']} years old.",
        f"I work as a {job} and I genuinely love what I do.",

        # Daily life
        f"Had a really productive day at work today. Finished a big project.",
        f"Feeling a bit tired today. Didn't sleep well last night.",
        f"Went for a long walk this morning. Feeling refreshed.",
        f"Skipped my workout today. Feeling guilty about it.",
        f"Had a great conversation with {friends[0]} today. Really needed that.",
        f"Feeling stressed about an upcoming deadline at work.",
        f"Today was one of those days where everything just clicked.",
        f"I've been procrastinating a lot lately. Need to get back on track.",
        f"Had a really tough meeting today. Feeling drained.",
        f"Cooked a new recipe today. Turned out amazing!",
        f"Feeling motivated today. Ready to tackle my goals.",
        f"Had a bad day. Nothing went as planned.",
        f"Spent the evening reading. Really needed the quiet time.",
        f"Feeling anxious about a presentation tomorrow.",
        f"Just finished a really good book. Feeling inspired.",

        # Emotions
        f"I'm feeling really happy today. Life is good.",
        f"Feeling overwhelmed with everything on my plate.",
        f"Had a moment of clarity today about what I really want in life.",
        f"Feeling grateful for the people in my life.",
        f"I've been feeling a bit lonely lately.",
        f"Today I felt really proud of myself for pushing through.",
        f"Feeling frustrated. Things aren't moving as fast as I'd like.",
        f"Had a really peaceful morning. Feeling centered.",
        f"Feeling excited about a new opportunity that came up.",
        f"I'm feeling burnt out. Need a break.",

        # Goals & growth
        f"I've been working on {goal.split()[0:4]} and making progress.",
        f"Set a new personal goal today. Feeling motivated.",
        f"Reflected on my progress this month. Proud of how far I've come.",
        f"Need to be more consistent with my habits.",
        f"Started a new routine this week. Hoping it sticks.",
        f"Had a breakthrough moment with my work today.",
        f"Feeling behind on my goals. Need to refocus.",
        f"Made a small but meaningful step toward my dream today.",

        # Social & relationships
        f"Had dinner with {friends[0]} and {friends[1]}. Great evening.",
        f"Caught up with {friends[2]} after a long time. Felt so good.",
        f"Had a disagreement with a colleague. Feeling unsettled.",
        f"My friend {friends[0]} is going through a tough time. Trying to support them.",
        f"Had a really meaningful conversation with {friends[1]} about life.",
        f"Feeling disconnected from people lately. Need to reach out more.",

        # Health & wellness
        f"Started meditating in the mornings. Feeling calmer.",
        f"Went to the gym today. Feeling strong.",
        f"Haven't been eating well lately. Need to fix that.",
        f"Got a full 8 hours of sleep last night. Feeling amazing.",
        f"My back has been hurting from sitting too long. Need to stretch more.",
        f"Feeling energetic today. Had a great workout.",

        # Work specific
        f"Had a really challenging problem at work today. Solved it eventually.",
        f"Got positive feedback from my manager today. Feeling validated.",
        f"Working on a new project that I'm really excited about.",
        f"Had back-to-back meetings all day. Exhausted.",
        f"Finally finished that report I've been working on for weeks.",
        f"Feeling underappreciated at work lately.",

        # Hobby & interests
        f"Spent the evening on {hobby.split()[0]}. Really enjoyed it.",
        f"Discovered something new about {hobby.split()[0]} today. Fascinating.",
        f"Haven't had time for {hobby.split()[0]} lately. Missing it.",
        f"Had a really fun session with {hobby.split()[0]} today.",

        # Reflective
        f"Thinking about where I want to be in 5 years.",
        f"Reflecting on my values and what truly matters to me.",
        f"Had a moment of self-doubt today. Pushed through it.",
        f"Feeling more confident in myself lately.",
        f"Wondering if I'm on the right path.",
        f"Grateful for all the experiences that shaped me.",
    ]

    # AI responses pool
    ai_responses = [
        f"That's wonderful to hear, {name}! It sounds like you're making great progress.",
        f"I understand how you feel. It's completely normal to have days like that.",
        f"You've been working so hard, {name}. Remember to take care of yourself too.",
        f"That's a really meaningful reflection. I'm glad you shared that with me.",
        f"It sounds like you're going through a lot right now. I'm here for you.",
        f"That's impressive! You should be proud of yourself.",
        f"I remember you mentioned feeling this way before. You always find your way through.",
        f"Your dedication to {goal.split()[0:3]} really shows. Keep going!",
        f"It's okay to have off days. What matters is that you keep showing up.",
        f"That sounds like a really fulfilling experience. Tell me more!",
        f"I can hear the excitement in your words. This is a great opportunity!",
        f"You've come so far, {name}. Don't forget to celebrate your progress.",
        f"That's a tough situation. How are you planning to handle it?",
        f"Your resilience is inspiring. You always find a way forward.",
        f"I'm glad you had that conversation. Connection is so important.",
        f"Rest is productive too. Your body and mind need recovery time.",
        f"That's a great insight. Self-awareness is the first step to growth.",
        f"I've noticed you've been mentioning stress a lot lately. Let's talk about it.",
        f"Your passion for {job.lower()} really comes through in everything you share.",
        f"That's a beautiful way to look at it. I love your perspective.",
    ]

    messages = []
    start_date = datetime(year, 1, 1)

    # Spread ~600 messages across 365 days (~1.6 per day)
    total_messages = 600
    for i in range(total_messages):
        # Random date within the year
        days_offset = random.randint(0, 364)
        hours_offset = random.randint(7, 23)
        mins_offset = random.randint(0, 59)
        msg_date = start_date + timedelta(days=days_offset, hours=hours_offset, minutes=mins_offset)

        user_msg = random.choice(base_messages)
        ai_msg   = random.choice(ai_responses)

        messages.append({
            "user": user_msg,
            "ai"  : ai_msg,
            "date": msg_date,
        })

    # Sort by date
    messages.sort(key=lambda x: x["date"])
    return messages


# ── Seed function ─────────────────────────────────────────

async def seed_user(db, user: dict):
    name = user["name"]
    print(f"\n  Seeding {name}...")

    # ── 1. Create user ────────────────────────────────────
    hashed = pwd_ctx.hash(user["password"])
    now = datetime.utcnow()

    await db.users.delete_many({"user_id": user["user_id"]})
    await db.users.insert_one({
        "user_id"      : user["user_id"],
        "name"         : user["name"],
        "email"        : user["email"],
        "password_hash": hashed,
        "profile"      : {
            "age"     : user["age"],
            "job"     : user["job"],
            "location": user["location"],
        },
        "preferences"  : {"language": "en", "voice": "female"},
        "created_at"   : datetime(2025, 1, 1),
        "updated_at"   : now,
    })

    # ── 2. Personal facts (memories collection) ───────────
    await db.memories.delete_many({"user_id": user["user_id"]})
    facts = [
        {"key": "name",     "value": user["name"],     "context": "identity"},
        {"key": "age",      "value": user["age"],       "context": "identity"},
        {"key": "job",      "value": user["job"],       "context": "career"},
        {"key": "location", "value": user["location"],  "context": "identity"},
        {"key": "goal",     "value": user["goal"],      "context": "goal"},
        {"key": "hobby",    "value": user["hobby"],     "context": "preference"},
    ]
    # Add family birthdays
    for rel, bday in user["family"].items():
        facts.append({"key": f"family_{rel}_birthday", "value": bday, "context": "family"})
    # Add friends
    for i, friend in enumerate(user["friends"]):
        facts.append({"key": f"friend_{i+1}", "value": friend, "context": "social"})

    fact_docs = []
    for f in facts:
        fact_docs.append({
            "memory_id"  : str(uuid.uuid4()),
            "user_id"    : user["user_id"],
            "key"        : f["key"],
            "value"      : f["value"],
            "context"    : f["context"],
            "source_text": f"My {f['key'].replace('_',' ')} is {f['value']}",
            "event_date" : None,
            "created_at" : datetime(2025, 1, 1),
            "updated_at" : now,
        })
    if fact_docs:
        await db.memories.insert_many(fact_docs)
    print(f"    ✅ {len(fact_docs)} personal facts")

    # ── 3. Conversations + messages ───────────────────────
    await db.messages.delete_many({"user_id": user["user_id"]})
    await db.conversations.delete_many({"user_id": user["user_id"]})

    # One conversation per month
    conv_map = {}
    for month in range(1, 13):
        conv_id = str(uuid.uuid4())
        conv_map[month] = conv_id
        await db.conversations.insert_one({
            "conversation_id": conv_id,
            "user_id"        : user["user_id"],
            "title"          : f"{datetime(2025, month, 1).strftime('%B')} Conversations",
            "created_at"     : datetime(2025, month, 1),
            "updated_at"     : datetime(2025, month, 28),
            "message_count"  : 0,
            "last_message_at": datetime(2025, month, 28),
        })

    raw_messages = get_messages_for_user(user, year=2025)
    msg_docs = []
    emotions = ["happy", "stressed", "tired", "motivated", "neutral", "anxious", "focused", "sad"]

    for pair in raw_messages:
        month = pair["date"].month
        conv_id = conv_map[month]
        emotion = random.choice(emotions)
        importance = random.randint(3, 10)

        # User message
        msg_docs.append({
            "message_id"      : str(uuid.uuid4()),
            "conversation_id" : conv_id,
            "user_id"         : user["user_id"],
            "role"            : "user",
            "content"         : pair["user"],
            "importance_score": importance,
            "emotion"         : emotion,
            "intent"          : "normal_chat",
            "created_at"      : pair["date"],
        })
        # AI response
        msg_docs.append({
            "message_id"      : str(uuid.uuid4()),
            "conversation_id" : conv_id,
            "user_id"         : user["user_id"],
            "role"            : "assistant",
            "content"         : pair["ai"],
            "importance_score": 5,
            "emotion"         : "neutral",
            "intent"          : "normal_chat",
            "created_at"      : pair["date"] + timedelta(seconds=random.randint(2, 10)),
        })

    if msg_docs:
        await db.messages.insert_many(msg_docs)
    print(f"    ✅ {len(msg_docs)} messages ({len(raw_messages)} exchanges)")

    # ── 4. Activities ─────────────────────────────────────
    await db.activities.delete_many({"user_id": user["user_id"]})
    activity_emotions = ["happy", "stressed", "tired", "motivated", "neutral", "anxious"]
    activity_types    = ["work", "gym", "study", "sleep", "social", "hobby", "meditation"]
    statuses          = ["completed", "missed", "started", "ongoing"]
    productivities    = ["high", "medium", "low"]

    act_docs = []
    for pair in random.sample(raw_messages, min(150, len(raw_messages))):
        act_docs.append({
            "activity_id": str(uuid.uuid4()),
            "user_id"    : user["user_id"],
            "raw_text"   : pair["user"],
            "emotion"    : random.choice(activity_emotions),
            "activity"   : random.choice(activity_types),
            "status"     : random.choice(statuses),
            "productivity": random.choice(productivities),
            "summary"    : f"User {random.choice(['felt', 'mentioned', 'shared'])} {pair['user'][:60]}",
            "created_at" : pair["date"],
        })
    if act_docs:
        await db.activities.insert_many(act_docs)
    print(f"    ✅ {len(act_docs)} activities")

    # ── 5. Mood logs (52 weeks) ───────────────────────────
    await db.mood_logs.delete_many({"user_id": user["user_id"]})
    moods_pool = [
        ("happy", 8), ("motivated", 9), ("focused", 7), ("neutral", 5),
        ("tired", 3), ("stressed", 3), ("anxious", 4), ("sad", 2), ("excited", 8),
    ]
    mood_docs = []
    for week in range(52):
        log_date = datetime(2025, 1, 6) + timedelta(weeks=week)
        mood, score = random.choice(moods_pool)
        score = max(1, min(10, score + random.randint(-1, 1)))
        mood_docs.append({
            "log_id"     : str(uuid.uuid4()),
            "user_id"    : user["user_id"],
            "mood"       : mood,
            "mood_score" : score,
            "note"       : f"Weekly check-in — feeling {mood}",
            "day_of_week": log_date.strftime("%A"),
            "hour_of_day": random.randint(8, 22),
            "source"     : "auto",
            "created_at" : log_date,
        })
    await db.mood_logs.insert_many(mood_docs)
    print(f"    ✅ {len(mood_docs)} mood logs")

    # ── 6. Tasks ──────────────────────────────────────────
    await db.tasks.delete_many({"user_id": user["user_id"]})
    task_templates = [
        {"title": f"Review weekly goals",          "priority": "high",   "status": "pending",   "due": "this week"},
        {"title": f"Catch up with {user['friends'][0]}", "priority": "medium", "status": "pending",   "due": "this weekend"},
        {"title": f"Work on {user['goal'].split()[0:3]}", "priority": "high",   "status": "pending",   "due": "ongoing"},
        {"title": f"Practice {user['hobby'].split()[0]}", "priority": "low",    "status": "completed", "due": "yesterday"},
    ]
    task_docs = []
    for t in task_templates:
        title = t["title"]
        if isinstance(title, list):
            title = " ".join(title)
        task_docs.append({
            "task_id"    : str(uuid.uuid4()),
            "user_id"    : user["user_id"],
            "title"      : title,
            "due_date"   : t["due"],
            "priority"   : t["priority"],
            "status"     : t["status"],
            "source"     : "manual",
            "created_at" : datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            "updated_at" : datetime.utcnow(),
            "completed_at": datetime.utcnow() if t["status"] == "completed" else None,
        })
    await db.tasks.insert_many(task_docs)
    print(f"    ✅ {len(task_docs)} tasks")

    # ── 7. FAISS vectors ──────────────────────────────────
    try:
        from backend.retrieval.vector_store import add_memories_batch
        texts = [pair["user"] for pair in random.sample(raw_messages, min(300, len(raw_messages)))]
        add_memories_batch(user["user_id"], texts)
        print(f"    ✅ {len(texts)} FAISS vectors indexed")
    except Exception as e:
        print(f"    ⚠️  FAISS indexing skipped: {e}")

    print(f"  ✅ {name} seeded successfully!")


async def main():
    print("=" * 60)
    print("SoulSync AI — MongoDB Seed (10 users, 1 year of data)")
    print("=" * 60)

    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB]

    # Test connection
    try:
        await db.command("ping")
        print("✅ MongoDB connected\n")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return

    # Ensure indexes
    try:
        from pymongo import ASCENDING, DESCENDING, IndexModel
        await db.users.create_indexes([
            IndexModel([("user_id", ASCENDING)], unique=True),
            IndexModel([("email",   ASCENDING)], unique=True),
        ])
        await db.messages.create_indexes([
            IndexModel([("user_id",    ASCENDING)]),
            IndexModel([("user_id",    ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("conversation_id", ASCENDING)]),
        ])
        await db.memories.create_indexes([
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("key", ASCENDING)]),
        ])
        await db.tasks.create_indexes([
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("status", ASCENDING)]),
        ])
        await db.activities.create_indexes([IndexModel([("user_id", ASCENDING)])])
        await db.mood_logs.create_indexes([IndexModel([("user_id", ASCENDING)])])
        print("✅ Indexes created\n")
    except Exception as e:
        print(f"⚠️  Index creation: {e}\n")

    # Seed all users
    for user in USERS:
        await seed_user(db, user)

    # Final counts
    print("\n" + "=" * 60)
    print("SEED COMPLETE — Final counts:")
    print("=" * 60)
    for col in ["users", "conversations", "messages", "memories", "tasks", "activities", "mood_logs"]:
        n = await db[col].count_documents({})
        print(f"  {col:20s}: {n:,}")

    client.close()
    print("\n✅ All done! Use credentials from credentials.txt to log in.")


if __name__ == "__main__":
    asyncio.run(main())
