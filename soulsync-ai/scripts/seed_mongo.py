"""
SoulSync AI â€” MongoDB Seed Script (v2)
Rich 1-year data for 10 users with:
  - Realistic varied messages covering all 32 life collections
  - Hindi/Hinglish messages for language detection testing
  - Personal facts, family, friends, opinions, life events
  - 52 weekly mood logs with realistic patterns
  - 6 tasks per user (mixed priority/status)
  - Activities with proper emotion/activity extraction
  - FAISS vector embeddings

Run: python soulsync-ai/scripts/seed_mongo.py
"""

import asyncio, sys, os, uuid, random
from datetime import datetime, timedelta, date
from passlib.context import CryptContext

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB",  "soulsync_db")
pwd_ctx     = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)


# -- 10 Users with rich profiles ---------------------------
USERS = [
    {
        "name": "Rohit Sharma", "email": "rohit@soulsync.ai", "password": "rohit123",
        "user_id": "rohit_seed", "age": "24", "job": "Software Engineer",
        "location": "Mumbai, India",
        "goal": "Become a senior engineer and launch a startup",
        "hobby": "Guitar and tech blogs",
        "friends": ["Arjun", "Priya", "Neha"],
        "family": {"mom": "March 12", "dad": "July 8", "sister": "November 3"},
        "personality": "ambitious, sometimes stressed about deadlines, loves coding",
        "opinions": {
            "remote_work": "I think remote work is the future. I am more productive at home.",
            "ai": "AI will change everything. I want to build AI-powered products.",
            "social_media": "Social media is a double-edged sword. Useful but addictive.",
        },
        "key_events": [
            ("Got promoted to Senior Engineer", "2025-04-15", "achievement"),
            ("Launched my first open source project", "2025-07-20", "achievement"),
            ("Had a big fight with Arjun over money", "2025-03-10", "conflict"),
            ("Started learning machine learning", "2025-01-15", "learning"),
            ("Ran my first 5K", "2025-09-05", "milestone"),
        ],
        "hinglish_messages": [
            "Aaj bahut thaka hua hoon. Office mein bahut kaam tha.",
            "Mera goal hai senior engineer banna aur apna startup launch karna.",
            "Arjun se aaj baat hui. Bahut achha laga.",
            "Gym skip kar diya aaj. Kal pakka jaunga.",
            "Mujhe coding bahut pasand hai. Yeh meri life hai.",
        ],
    },
    {
        "name": "Aisha Khan", "email": "aisha@soulsync.ai", "password": "aisha123",
        "user_id": "aisha_seed", "age": "27", "job": "UX Designer",
        "location": "Bangalore, India",
        "goal": "Design products that improve people's lives",
        "hobby": "Painting and yoga",
        "friends": ["Zara", "Meera", "Riya"],
        "family": {"mom": "April 20", "dad": "September 5", "brother": "January 15"},
        "personality": "creative, empathetic, anxious before presentations",
        "opinions": {
            "design": "Good design is invisible. It should feel natural.",
            "work_life_balance": "I believe in working smart, not just hard.",
            "mental_health": "Mental health is just as important as physical health.",
        },
        "key_events": [
            ("Won best design award at company", "2025-06-10", "achievement"),
            ("Had a panic attack before big presentation", "2025-02-20", "mental_health"),
            ("Started therapy sessions", "2025-03-01", "mental_health"),
            ("Traveled to Goa with friends", "2025-05-15", "experience"),
            ("Completed 30-day yoga challenge", "2025-08-30", "milestone"),
        ],
        "hinglish_messages": [
            "Aaj presentation se pehle bahut nervous thi. Par sab theek ho gaya.",
            "Yoga ne meri life badal di. Roz subah karna chahiye.",
            "Zara se baat hui. Woh bhi stressed hai apni job se.",
            "Mera dream hai apna design studio kholna.",
            "Painting karna mujhe bahut peaceful feel karata hai.",
        ],
    },
    {
        "name": "Marcus Johnson", "email": "marcus@soulsync.ai", "password": "marcus123",
        "user_id": "marcus_seed", "age": "31", "job": "Product Manager",
        "location": "Lagos, Nigeria",
        "goal": "Build a product used by 1 million people",
        "hobby": "Basketball and podcasting",
        "friends": ["Tunde", "Emeka", "Chidi"],
        "family": {"mom": "February 14", "dad": "October 22", "wife": "June 30"},
        "personality": "strategic, driven, loves data and metrics",
        "opinions": {
            "startups": "Execution beats ideas every time.",
            "africa_tech": "Africa is the next big tech frontier.",
            "leadership": "Great leaders listen more than they speak.",
        },
        "key_events": [
            ("Product hit 100k users", "2025-08-01", "achievement"),
            ("Wife's birthday celebration", "2025-06-30", "social_event"),
            ("Lost a major client deal", "2025-04-05", "failure_setback"),
            ("Launched podcast episode 50", "2025-10-15", "milestone"),
            ("Hired first team member", "2025-02-28", "work_career"),
        ],
        "hinglish_messages": [],
    },
    {
        "name": "Priya Patel", "email": "priya@soulsync.ai", "password": "priya123",
        "user_id": "priya_seed", "age": "22", "job": "Medical Student",
        "location": "Ahmedabad, India",
        "goal": "Become a cardiologist and help underserved communities",
        "hobby": "Cooking and classical dance",
        "friends": ["Sneha", "Kavya", "Ananya"],
        "family": {"mom": "May 18", "dad": "December 1", "brother": "August 25"},
        "personality": "hardworking, sleep-deprived, passionate about medicine",
        "opinions": {
            "healthcare": "Healthcare should be accessible to everyone, not just the rich.",
            "studying": "Consistency beats cramming every time.",
            "burnout": "Medical students need better mental health support.",
        },
        "key_events": [
            ("Passed cardiology exam with distinction", "2025-05-20", "achievement"),
            ("Volunteered at rural health camp", "2025-07-10", "experience"),
            ("Failed anatomy practical", "2025-02-15", "failure_setback"),
            ("Started classical dance again after 2 years", "2025-09-01", "milestone"),
            ("Mom's birthday surprise party", "2025-05-18", "social_event"),
        ],
        "hinglish_messages": [
            "Aaj cardiology exam tha. Bahut mushkil tha par pass ho gayi.",
            "Raat bhar padhai ki. Subah 4 baje soyi.",
            "Sneha ke saath hospital mein volunteer kiya. Bahut achha experience tha.",
            "Mera sapna hai cardiologist banna aur garib logon ki madad karna.",
            "Aaj dance practice ki. Bahut dino baad. Bahut achha laga.",
        ],
    },
    {
        "name": "Sam Rivera", "email": "sam@soulsync.ai", "password": "sam12345",
        "user_id": "sam_seed", "age": "29", "job": "Freelance Writer",
        "location": "Mexico City, Mexico",
        "goal": "Publish first novel and build a sustainable writing career",
        "hobby": "Hiking and photography",
        "friends": ["Carlos", "Sofia", "Diego"],
        "family": {"mom": "March 28", "dad": "July 4", "sister": "October 10"},
        "personality": "creative, procrastinates sometimes, loves nature",
        "opinions": {
            "writing": "Every story worth telling has already been told. The magic is in how you tell it.",
            "nature": "Nature is the best therapist.",
            "freelancing": "Freedom comes with discipline.",
        },
        "key_events": [
            ("Finished first draft of novel", "2025-09-30", "achievement"),
            ("Hiked Teotihuacan pyramids", "2025-04-20", "experience"),
            ("Got rejected by 3 publishers", "2025-06-15", "failure_setback"),
            ("Published article in major magazine", "2025-11-05", "achievement"),
            ("Sister's wedding", "2025-10-10", "social_event"),
        ],
        "hinglish_messages": [],
    },
    {
        "name": "Elena Rodriguez", "email": "elena@soulsync.ai", "password": "elena123",
        "user_id": "elena_seed", "age": "30", "job": "Marketing Manager",
        "location": "Barcelona, Spain",
        "goal": "Launch her own digital marketing agency by 2027",
        "hobby": "Photography and travel blogging",
        "friends": ["Sofia", "Carlos", "Maria"],
        "family": {"mom": "March 15", "dad": "July 22", "sister": "November 8"},
        "personality": "ambitious, social, loves travel and new experiences",
        "opinions": {
            "marketing": "Authentic storytelling beats paid ads every time.",
            "travel": "Travel is the only thing you buy that makes you richer.",
            "entrepreneurship": "The best time to start was yesterday. The second best is now.",
        },
        "key_events": [
            ("Got promoted to Marketing Manager", "2025-04-01", "achievement"),
            ("Traveled to Japan for 2 weeks", "2025-06-15", "experience"),
            ("Spoke at marketing conference", "2025-10-20", "achievement"),
            ("Mom's birthday celebration in Barcelona", "2025-03-15", "social_event"),
            ("Started agency planning", "2025-11-01", "goal"),
        ],
        "hinglish_messages": [],
    },
    {
        "name": "David Chen", "email": "david@soulsync.ai", "password": "david123",
        "user_id": "david_seed", "age": "35", "job": "Data Scientist",
        "location": "Toronto, Canada",
        "goal": "Publish research in AI ethics and build tools for social good",
        "hobby": "Chess and reading philosophy",
        "friends": ["James", "Lisa", "Kevin"],
        "family": {"wife": "April 18", "son": "September 5", "anniversary": "May 20"},
        "personality": "analytical, thoughtful, cares deeply about ethics",
        "opinions": {
            "ai_ethics": "AI without ethics is just a powerful tool for harm.",
            "data_privacy": "Data privacy is a fundamental human right.",
            "parenting": "The best thing you can give your child is your time.",
        },
        "key_events": [
            ("AI ethics paper accepted by journal", "2025-09-15", "achievement"),
            ("Son turned 3", "2025-09-05", "milestone"),
            ("5th wedding anniversary at Niagara Falls", "2025-05-20", "social_event"),
            ("Gave TEDx talk on AI ethics", "2025-07-08", "achievement"),
            ("Started chess club at son's school", "2025-10-01", "experience"),
        ],
        "hinglish_messages": [],
    },
    {
        "name": "Fatima Al-Mansoori", "email": "fatima@soulsync.ai", "password": "fatima123",
        "user_id": "fatima_seed", "age": "28", "job": "Civil Engineer",
        "location": "Dubai, UAE",
        "goal": "Design sustainable infrastructure for developing countries",
        "hobby": "Calligraphy and volunteering",
        "friends": ["Layla", "Ahmed", "Noor"],
        "family": {"mom": "February 10", "dad": "August 14", "brother": "December 3"},
        "personality": "disciplined, compassionate, driven by purpose",
        "opinions": {
            "sustainability": "We are borrowing the earth from our children.",
            "volunteering": "Service to others is the rent you pay for your room here on earth.",
            "engineering": "Engineering is about solving real problems for real people.",
        },
        "key_events": [
            ("Led first infrastructure project — water treatment plant", "2025-04-10", "achievement"),
            ("Volunteered at refugee camp", "2025-06-20", "experience"),
            ("City council approved sustainable design proposal", "2025-10-05", "achievement"),
            ("Dad's birthday celebration", "2025-08-14", "social_event"),
            ("Completed calligraphy exhibition", "2025-12-01", "creative_work"),
        ],
        "hinglish_messages": [],
    },
    {
        "name": "Jake Morrison", "email": "jake@soulsync.ai", "password": "jake1234",
        "user_id": "jake_seed", "age": "33", "job": "High School Teacher",
        "location": "Portland, Oregon, USA",
        "goal": "Write a book about teaching methods and inspire educators",
        "hobby": "Running marathons and playing piano",
        "friends": ["Tom", "Sarah", "Mike"],
        "family": {"mom": "March 8", "dad": "October 12", "girlfriend": "June 30"},
        "personality": "patient, inspiring, loves connecting with students",
        "opinions": {
            "education": "Education is not filling a bucket but lighting a fire.",
            "running": "Running taught me that the only limits are the ones you set yourself.",
            "teaching": "The best teachers are the ones who never stop learning.",
        },
        "key_events": [
            ("Student told him he changed his life", "2025-04-22", "achievement"),
            ("Ran first marathon — 4h 12min", "2025-08-15", "milestone"),
            ("Dad's 65th birthday party", "2025-10-12", "social_event"),
            ("Started writing book outline", "2025-11-01", "creative_work"),
            ("Girlfriend's birthday surprise", "2025-06-30", "social_event"),
        ],
        "hinglish_messages": [],
    },
    {
        "name": "Yuki Tanaka", "email": "yuki@soulsync.ai", "password": "yuki1234",
        "user_id": "yuki_seed", "age": "26", "job": "Indie Game Developer",
        "location": "Kyoto, Japan",
        "goal": "Create an indie game that tells a meaningful story",
        "hobby": "Anime, manga, and pixel art",
        "friends": ["Kenji", "Hana", "Ryo"],
        "family": {"mom": "April 5", "dad": "September 18", "grandma": "January 20"},
        "personality": "creative, introverted, passionate about storytelling",
        "opinions": {
            "games": "Games are the most powerful storytelling medium ever created.",
            "corporate_work": "Corporate game dev kills creativity. Indie is the soul of gaming.",
            "japan": "Japan has the perfect balance of tradition and innovation.",
        },
        "key_events": [
            ("Quit corporate job to work on indie game full-time", "2025-04-01", "decision"),
            ("Game prototype loved by friends", "2025-07-15", "achievement"),
            ("Hit 10,000 wishlists on Steam", "2025-11-20", "milestone"),
            ("Grandma's 80th birthday", "2025-01-20", "social_event"),
            ("Attended Tokyo Game Show", "2025-09-25", "experience"),
        ],
        "hinglish_messages": [],
    },
]


def get_messages_for_user(user: dict, year: int = 2025) -> list:
    name    = user["name"].split()[0]
    job     = user["job"]
    goal    = user["goal"]
    hobby   = user["hobby"]
    friends = user["friends"]
    family  = user["family"]

    base_messages = [
        f"My name is {name} and I am a {job}.",
        f"My goal is to {goal}.",
        f"I love {hobby}. It really helps me unwind.",
        f"I am {user['age']} years old and living in {user['location']}.",
        f"Had a really productive day at work today. Finished a big project.",
        f"Feeling a bit tired today. Did not sleep well last night.",
        f"Went for a long walk this morning. Feeling refreshed.",
        f"Skipped my workout today. Feeling guilty about it.",
        f"Had a great conversation with {friends[0]} today. Really needed that.",
        f"Feeling stressed about an upcoming deadline at work.",
        f"Today was one of those days where everything just clicked.",
        f"I have been procrastinating a lot lately. Need to get back on track.",
        f"Had a really tough meeting today. Feeling drained.",
        f"Cooked a new recipe today. Turned out amazing!",
        f"Feeling motivated today. Ready to tackle my goals.",
        f"Had a bad day. Nothing went as planned.",
        f"Spent the evening reading. Really needed the quiet time.",
        f"Feeling anxious about a presentation tomorrow.",
        f"Just finished a really good book. Feeling inspired.",
        f"I am feeling really happy today. Life is good.",
        f"Feeling overwhelmed with everything on my plate.",
        f"Had a moment of clarity today about what I really want in life.",
        f"Feeling grateful for the people in my life.",
        f"I have been feeling a bit lonely lately.",
        f"Today I felt really proud of myself for pushing through.",
        f"Feeling frustrated. Things are not moving as fast as I would like.",
        f"Had a really peaceful morning. Feeling centered.",
        f"Feeling excited about a new opportunity that came up.",
        f"I am feeling burnt out. Need a break.",
        f"I have been working on my goal and making progress.",
        f"Set a new personal goal today. Feeling motivated.",
        f"Reflected on my progress this month. Proud of how far I have come.",
        f"Need to be more consistent with my habits.",
        f"Started a new routine this week. Hoping it sticks.",
        f"Had a breakthrough moment with my work today.",
        f"Feeling behind on my goals. Need to refocus.",
        f"Made a small but meaningful step toward my dream today.",
        f"Had dinner with {friends[0]} and {friends[1]}. Great evening.",
        f"Caught up with {friends[2]} after a long time. Felt so good.",
        f"Had a disagreement with a colleague. Feeling unsettled.",
        f"My friend {friends[0]} is going through a tough time. Trying to support them.",
        f"Had a really meaningful conversation with {friends[1]} about life.",
        f"Feeling disconnected from people lately. Need to reach out more.",
        f"Started meditating in the mornings. Feeling calmer.",
        f"Went to the gym today. Feeling strong.",
        f"Have not been eating well lately. Need to fix that.",
        f"Got a full 8 hours of sleep last night. Feeling amazing.",
        f"My back has been hurting from sitting too long. Need to stretch more.",
        f"Feeling energetic today. Had a great workout.",
        f"Had a really challenging problem at work today. Solved it eventually.",
        f"Got positive feedback from my manager today. Feeling validated.",
        f"Working on a new project that I am really excited about.",
        f"Had back-to-back meetings all day. Exhausted.",
        f"Finally finished that report I have been working on for weeks.",
        f"Feeling underappreciated at work lately.",
        f"Spent the evening on {hobby.split()[0]}. Really enjoyed it.",
        f"Discovered something new about {hobby.split()[0]} today. Fascinating.",
        f"Have not had time for {hobby.split()[0]} lately. Missing it.",
        f"Thinking about where I want to be in 5 years.",
        f"Reflecting on my values and what truly matters to me.",
        f"Had a moment of self-doubt today. Pushed through it.",
        f"Feeling more confident in myself lately.",
        f"Wondering if I am on the right path.",
        f"Grateful for all the experiences that shaped me.",
        f"I think I need to take better care of my mental health.",
        f"Had a really good laugh with {friends[0]} today. Needed that.",
        f"Feeling scared about the future sometimes. But I know I will figure it out.",
        f"I believe in working hard and staying consistent.",
        f"Looking back, I realize how much I have grown this year.",
        f"I decided to start waking up at 6am every day. Day 3 going strong.",
        f"I got promoted today! Best day of my life.",
        f"Failed my driving test today. Feeling disappointed.",
        f"I have been dealing with anxiety lately. Trying to manage it.",
        f"My mom called today. Always makes me feel better.",
        f"I am scared of failing. But I know I have to keep trying.",
        f"I learned the hard way that consistency is everything.",
        f"I think social media is making people more anxious.",
        f"Haha my friend {friends[0]} said the funniest thing today.",
        f"I am grateful for my health, my family, and my friends.",
        f"I need to remind myself to call {friends[1]} more often.",
        f"I have been feeling really empty lately. Not sure why.",
        f"I am working on building better habits. One day at a time.",
    ]

    ai_responses = [
        f"That is wonderful to hear, {name}! It sounds like you are making great progress.",
        f"I understand how you feel. It is completely normal to have days like that.",
        f"You have been working so hard, {name}. Remember to take care of yourself too.",
        f"That is a really meaningful reflection. I am glad you shared that with me.",
        f"It sounds like you are going through a lot right now. I am here for you.",
        f"That is impressive! You should be proud of yourself.",
        f"I remember you mentioned feeling this way before. You always find your way through.",
        f"Your dedication really shows. Keep going!",
        f"It is okay to have off days. What matters is that you keep showing up.",
        f"That sounds like a really fulfilling experience. Tell me more!",
        f"I can hear the excitement in your words. This is a great opportunity!",
        f"You have come so far, {name}. Do not forget to celebrate your progress.",
        f"That is a tough situation. How are you planning to handle it?",
        f"Your resilience is inspiring. You always find a way forward.",
        f"I am glad you had that conversation. Connection is so important.",
        f"Rest is productive too. Your body and mind need recovery time.",
        f"That is a great insight. Self-awareness is the first step to growth.",
        f"I have noticed you have been mentioning stress a lot lately. Let us talk about it.",
        f"Your passion really comes through in everything you share.",
        f"That is a beautiful way to look at it. I love your perspective.",
        f"I am always here for you, {name}. You are not alone in this.",
        f"That sounds really hard. How are you feeling right now?",
        f"You are stronger than you think. I have seen how you handle challenges.",
        f"That is such a big achievement! How does it feel?",
        f"I think taking a break is exactly what you need right now.",
    ]

    messages = []
    start_date = datetime(year, 1, 1)

    for i in range(600):
        days_offset  = random.randint(0, 364)
        hours_offset = random.randint(7, 23)
        mins_offset  = random.randint(0, 59)
        msg_date = start_date + timedelta(days=days_offset, hours=hours_offset, minutes=mins_offset)
        messages.append({
            "user": random.choice(base_messages),
            "ai"  : random.choice(ai_responses),
            "date": msg_date,
        })

    # Add key life events
    for title, date_str, collection in user.get("key_events", []):
        try:
            event_date = datetime.strptime(date_str, "%Y-%m-%d")
            event_date = event_date.replace(hour=random.randint(9, 20), minute=random.randint(0, 59))
            messages.append({
                "user": title,
                "ai"  : f"That is amazing, {name}! Tell me more about {title.lower()}.",
                "date": event_date,
            })
        except Exception:
            pass

    # Add opinion messages
    for topic, opinion in user.get("opinions", {}).items():
        opinion_date = start_date + timedelta(days=random.randint(0, 364), hours=random.randint(9, 21))
        messages.append({
            "user": opinion,
            "ai"  : f"That is a really interesting perspective on {topic.replace('_', ' ')}, {name}. I agree that it is an important topic.",
            "date": opinion_date,
        })

    # Add Hindi/Hinglish messages
    for msg in user.get("hinglish_messages", []):
        hindi_date = start_date + timedelta(days=random.randint(0, 364), hours=random.randint(9, 21))
        messages.append({
            "user": msg,
            "ai"  : f"Main samajh sakta hoon, {name}. Aap bahut mehnat kar rahe hain.",
            "date": hindi_date,
        })

    messages.sort(key=lambda x: x["date"])
    return messages


async def seed_user(db, user: dict):
    name = user["name"]
    print(f"  Seeding {name}...")
    hashed = pwd_ctx.hash(user["password"])
    now    = datetime.utcnow()

    await db.users.delete_many({"user_id": user["user_id"]})
    await db.users.insert_one({
        "user_id"      : user["user_id"],
        "name"         : user["name"],
        "email"        : user["email"],
        "password_hash": hashed,
        "profile"      : {"age": user["age"], "job": user["job"], "location": user["location"]},
        "preferences"  : {"language": "en", "voice": "female"},
        "created_at"   : datetime(2025, 1, 1),
        "updated_at"   : now,
    })

    # Personal facts
    await db.memories.delete_many({"user_id": user["user_id"]})
    facts = [
        {"key": "name",     "value": user["name"],     "context": "identity"},
        {"key": "age",      "value": user["age"],       "context": "identity"},
        {"key": "job",      "value": user["job"],       "context": "career"},
        {"key": "location", "value": user["location"],  "context": "identity"},
        {"key": "goal",     "value": user["goal"],      "context": "goal"},
        {"key": "hobby",    "value": user["hobby"],     "context": "preference"},
        {"key": "personality", "value": user["personality"], "context": "identity"},
    ]
    for rel, bday in user["family"].items():
        facts.append({"key": f"family_{rel}_birthday", "value": bday, "context": "family"})
    for i, friend in enumerate(user["friends"]):
        facts.append({"key": f"friend_{i+1}", "value": friend, "context": "social"})
    for topic, opinion in user.get("opinions", {}).items():
        facts.append({"key": f"opinion_{topic}", "value": opinion, "context": "opinion"})

    fact_docs = [{
        "memory_id"  : str(uuid.uuid4()),
        "user_id"    : user["user_id"],
        "key"        : f["key"],
        "value"      : f["value"],
        "context"    : f["context"],
        "source_text": f"My {f['key'].replace('_',' ')} is {f['value']}",
        "event_date" : None,
        "created_at" : datetime(2025, 1, 1),
        "updated_at" : now,
    } for f in facts]
    await db.memories.insert_many(fact_docs)
    print(f"    {len(fact_docs)} personal facts")

    # Conversations + messages
    await db.messages.delete_many({"user_id": user["user_id"]})
    await db.conversations.delete_many({"user_id": user["user_id"]})
    conv_map = {}
    for month in range(1, 13):
        conv_id = str(uuid.uuid4())
        conv_map[month] = conv_id
        await db.conversations.insert_one({
            "conversation_id": conv_id,
            "user_id"        : user["user_id"],
            "title"          : f"{datetime(2025, month, 1).strftime('%B')} 2025",
            "created_at"     : datetime(2025, month, 1),
            "updated_at"     : datetime(2025, month, 28),
            "message_count"  : 0,
            "last_message_at": datetime(2025, month, 28),
        })

    raw_messages = get_messages_for_user(user, year=2025)
    emotions = ["happy","stressed","tired","motivated","neutral","anxious","focused","sad","excited","grateful"]
    msg_docs = []
    for pair in raw_messages:
        month   = pair["date"].month
        conv_id = conv_map[month]
        emotion = random.choice(emotions)
        msg_docs.append({
            "message_id"      : str(uuid.uuid4()),
            "conversation_id" : conv_id,
            "user_id"         : user["user_id"],
            "role"            : "user",
            "content"         : pair["user"],
            "importance_score": random.randint(3, 10),
            "emotion"         : emotion,
            "intent"          : "normal_chat",
            "created_at"      : pair["date"],
        })
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
    await db.messages.insert_many(msg_docs)
    print(f"    {len(msg_docs)} messages ({len(raw_messages)} exchanges)")

    # Activities
    await db.activities.delete_many({"user_id": user["user_id"]})
    activity_emotions = ["happy","stressed","tired","motivated","neutral","anxious","proud","grateful"]
    activity_types    = ["work","gym","study","sleep","social","hobby","meditation","reading","cooking","running"]
    statuses          = ["completed","missed","started","ongoing"]
    productivities    = ["high","medium","low"]
    act_docs = [{
        "activity_id" : str(uuid.uuid4()),
        "user_id"     : user["user_id"],
        "raw_text"    : pair["user"],
        "emotion"     : random.choice(activity_emotions),
        "activity"    : random.choice(activity_types),
        "status"      : random.choice(statuses),
        "productivity": random.choice(productivities),
        "summary"     : f"User mentioned: {pair['user'][:60]}",
        "created_at"  : pair["date"],
    } for pair in random.sample(raw_messages, min(150, len(raw_messages)))]
    await db.activities.insert_many(act_docs)
    print(f"    {len(act_docs)} activities")

    # Mood logs (52 weeks with realistic patterns)
    await db.mood_logs.delete_many({"user_id": user["user_id"]})
    moods_pool = [
        ("happy",8),("motivated",9),("focused",7),("content",7),("grateful",8),
        ("neutral",5),("okay",5),
        ("tired",3),("stressed",3),("anxious",4),("sad",2),("overwhelmed",3),
        ("excited",9),("proud",8),("lonely",4),("frustrated",3),
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
    print(f"    {len(mood_docs)} mood logs")

    # Tasks (6 per user)
    await db.tasks.delete_many({"user_id": user["user_id"]})
    task_templates = [
        {"title": "Review weekly goals and plan next steps",    "priority": "high",   "status": "pending",   "due": "this week"},
        {"title": f"Catch up with {user['friends'][0]}",        "priority": "medium", "status": "pending",   "due": "this weekend"},
        {"title": f"Work on {' '.join(user['goal'].split()[:4])}", "priority": "high", "status": "pending",  "due": "ongoing"},
        {"title": f"Practice {user['hobby'].split()[0]}",       "priority": "low",    "status": "completed", "due": "yesterday"},
        {"title": "Read for 30 minutes before bed",             "priority": "low",    "status": "pending",   "due": "daily"},
        {"title": "Schedule health checkup",                    "priority": "medium", "status": "pending",   "due": "next week"},
    ]
    task_docs = [{
        "task_id"     : str(uuid.uuid4()),
        "user_id"     : user["user_id"],
        "title"       : t["title"],
        "due_date"    : t["due"],
        "priority"    : t["priority"],
        "status"      : t["status"],
        "source"      : "manual",
        "created_at"  : datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        "updated_at"  : datetime.utcnow(),
        "completed_at": datetime.utcnow() if t["status"] == "completed" else None,
    } for t in task_templates]
    await db.tasks.insert_many(task_docs)
    print(f"    {len(task_docs)} tasks")

    # FAISS vectors
    try:
        from backend.retrieval.vector_store import add_memories_batch
        texts = [p["user"] for p in random.sample(raw_messages, min(300, len(raw_messages)))]
        add_memories_batch(user["user_id"], texts)
        print(f"    {len(texts)} FAISS vectors indexed")
    except Exception as e:
        print(f"    FAISS skipped: {e}")

    print(f"  Done: {name}")


async def main():
    print("=" * 60)
    print("SoulSync AI — MongoDB Seed v2 (10 users, 1 year rich data)")
    print("=" * 60)
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB]
    try:
        await db.command("ping")
        print("MongoDB connected\n")
    except Exception as e:
        print(f"MongoDB connection failed: {e}"); return

    # Clear all
    for col in ["users","conversations","messages","memories","tasks","activities","mood_logs"]:
        r = await db[col].delete_many({})
        print(f"  Cleared {col}: {r.deleted_count}")

    # Indexes
    try:
        from pymongo import ASCENDING, DESCENDING, IndexModel
        await db.users.create_indexes([IndexModel([("user_id",ASCENDING)],unique=True),IndexModel([("email",ASCENDING)],unique=True)])
        await db.messages.create_indexes([IndexModel([("user_id",ASCENDING)]),IndexModel([("user_id",ASCENDING),("created_at",DESCENDING)]),IndexModel([("conversation_id",ASCENDING)])])
        await db.memories.create_indexes([IndexModel([("user_id",ASCENDING)]),IndexModel([("user_id",ASCENDING),("key",ASCENDING)])])
        await db.tasks.create_indexes([IndexModel([("user_id",ASCENDING)]),IndexModel([("user_id",ASCENDING),("status",ASCENDING)])])
        await db.activities.create_indexes([IndexModel([("user_id",ASCENDING)])])
        await db.mood_logs.create_indexes([IndexModel([("user_id",ASCENDING)])])
        print("Indexes ready\n")
    except Exception as e:
        print(f"Index warning: {e}\n")

    for user in USERS:
        await seed_user(db, user)

    print("\n" + "=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    for col in ["users","conversations","messages","memories","tasks","activities","mood_logs"]:
        n = await db[col].count_documents({})
        print(f"  {col:20s}: {n:,}")
    client.close()
    print("\nDone! Use credentials.txt to log in.")


if __name__ == "__main__":
    asyncio.run(main())
