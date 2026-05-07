"""
SoulSync AI - Personal Info Storage (MongoDB)
==============================================

Stores and retrieves structured personal facts about users (name, goal, job, etc.).
This module provides the "memory" capability for the AI companion, allowing it to
remember important details about each user across conversations.

Data Storage:
    - All facts are stored in MongoDB 'memories' collection
    - Each fact has a key-value pair with metadata (source_text, event_date, timestamps)
    - Facts can be updated (most keys) or appended (goal, dream, aim, opinion, interest)

Supported Fact Types:
    - Basic Info: name, age, location, email, phone
    - Career: job, workplace, education, degree
    - Personal: goal, dream, aim, hobby, interest
    - Relationships: partner, mother_name, father_name, sibling_name, child_name
    - Favorites: favorite_<category> (e.g., favorite_color, favorite_movie)
    - Opinions: opinion_<topic> (e.g., opinion_politics, opinion_music)

Usage:
    >>> from backend.memory.personal_info import store_personal_info, get_fact, format_for_prompt
    >>> store_personal_info("user123", "name", "Rohit", source_text="My name is Rohit")
    >>> name = get_fact("user123", "name")  # Returns "Rohit"
    >>> context = format_for_prompt("user123")  # Returns formatted string for AI
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any

logger = logging.getLogger("soulsync.personal_info")

# ─── Configuration ──────────────────────────────────────────────────────

_APPENDABLE = {"goal", "dream", "aim", "opinion", "interest"}
"""
Set of fact keys that support multiple values over time.
For these keys, new values are appended (with unique sub-keys) rather than replacing existing ones.
This allows tracking the evolution of goals, dreams, and opinions over time.
"""

# ─── Helper Functions ────────────────────────────────────────────────────

def _run(coro):
    """
    Execute an async coroutine synchronously.
    
    This helper handles the case where we need to call async MongoDB operations
    from synchronous code. It detects if an event loop is already running
    and handles accordingly.
    
    Args:
        coro: An async coroutine to execute
        
    Returns:
        The result of the coroutine
        
    Note:
        This is a workaround for the sync/async boundary in the codebase.
        Consider migrating to fully async code in the future.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Event loop is running (e.g., in async context)
            # Use ThreadPoolExecutor to run asyncio.run in a separate thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        # No running loop, use the current one
        return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(coro)


def _db():
    """
    Get the MongoDB database connection.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


# ─── Store Personal Info ────────────────────────────────────────────────

def store_personal_info(
    user_id: str,
    key: str,
    value: str,
    source_text: str = None,
    event_date: date = None
) -> None:
    """
    Store or update a personal fact about a user.
    
    For most keys, this updates the existing value (upsert).
    For appendable keys (goal, dream, aim, opinion, interest), 
    new values are added with unique sub-keys to track evolution over time.
    
    Args:
        user_id: Unique user identifier
        key: Fact key (e.g., "name", "goal", "job")
        value: Fact value to store
        source_text: Original user message that contained this fact (for reference)
        event_date: Date when this fact became true (defaults to None)
        
    Example:
        >>> store_personal_info("user123", "name", "Rohit", 
        ...                     source_text="My name is Rohit Sharma")
        >>> store_personal_info("user123", "goal", "Become a senior engineer",
        ...                     source_text="My goal is to become a senior engineer")
    """
    async def _run_inner():
        import uuid
        import time
        
        db = _db()
        key_lower = key.lower().strip()
        now = datetime.utcnow()
        
        logger.debug(f"[PersonalInfo] Storing: user={user_id} | key={key_lower} | value={value[:50]}...")
        
        # Appendable keys get unique sub-keys to track evolution
        if key_lower in _APPENDABLE:
            # Create unique key with timestamp component
            unique_key = f"{key_lower}_{int(time.time() * 1000) % 1_000_000}"
            
            document = {
                "memory_id": str(uuid.uuid4()),
                "user_id": user_id,
                "key": unique_key,
                "value": value,
                "context": key_lower,  # Group by base key
                "source_text": source_text,
                "event_date": str(event_date) if event_date else None,
                "created_at": now,
                "updated_at": now,
            }
            
            await db.memories.insert_one(document)
            logger.info(f"[PersonalInfo] Appended {key_lower}: user={user_id} | subkey={unique_key}")
            
        else:
            # Non-appendable keys use upsert (update or insert)
            result = await db.memories.find_one_and_update(
                {"user_id": user_id, "key": key_lower},
                {
                    "$set": {
                        "value": value,
                        "source_text": source_text,
                        "event_date": str(event_date) if event_date else None,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "memory_id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "key": key_lower,
                        "context": "general",
                        "created_at": now,
                    },
                },
                upsert=True,
                return_document=True,
            )
            
            if result:
                logger.info(f"[PersonalInfo] Updated {key_lower}: user={user_id}")
            else:
                logger.info(f"[PersonalInfo] Created {key_lower}: user={user_id}")
    
    try:
        _run(_run_inner())
    except Exception as e:
        logger.error(f"[PersonalInfo] Failed to store personal info: {e}")


# ─── Get All Facts ──────────────────────────────────────────────────────

def get_all_facts(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all stored personal facts for a user.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        List of fact dictionaries with keys:
        - key: Fact key (e.g., "name", "goal_123456")
        - value: Fact value
        - context: Category/context of the fact
        - source_text: Original message (if available)
        - event_date: When the fact became true (if set)
        - created_at: When the fact was first stored
        - updated_at: When the fact was last updated
        
    Example:
        >>> facts = get_all_facts("user123")
        >>> for fact in facts:
        ...     print(f"{fact['key']}: {fact['value']}")
    """
    async def _run_inner() -> List[Dict[str, Any]]:
        db = _db()
        cursor = db.memories.find({"user_id": user_id}).sort("created_at", -1)
        docs = []
        async for doc in cursor:
            docs.append({
                "key": doc.get("key"),
                "value": doc.get("value"),
                "context": doc.get("context", "general"),
                "source_text": doc.get("source_text"),
                "event_date": doc.get("event_date"),
                "created_at": str(doc.get("created_at", "")),
                "updated_at": str(doc.get("updated_at", "")),
            })
        return docs
    
    try:
        facts = _run(_run_inner())
        logger.debug(f"[PersonalInfo] Retrieved {len(facts)} facts for user={user_id}")
        return facts
    except Exception as e:
        logger.error(f"[PersonalInfo] Failed to get all facts: {e}")
        return []


def get_fact(user_id: str, key: str) -> Optional[str]:
    """
    Retrieve a specific personal fact by key.
    
    Args:
        user_id: Unique user identifier
        key: Fact key to look up (e.g., "name", "job")
        
    Returns:
        The fact value if found, None otherwise
        
    Example:
        >>> name = get_fact("user123", "name")
        >>> if name:
        ...     print(f"User's name is {name}")
    """
    async def _run_inner() -> Optional[str]:
        db = _db()
        doc = await db.memories.find_one(
            {"user_id": user_id, "key": key.lower()},
            sort=[("created_at", -1)]  # Get most recent
        )
        return doc["value"] if doc else None
    
    try:
        value = _run(_run_inner())
        logger.debug(f"[PersonalInfo] Retrieved {key} for user={user_id}: {value}")
        return value
    except Exception as e:
        logger.error(f"[PersonalInfo] Failed to get fact {key}: {e}")
        return None


def get_goals_timeline(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all goals for a user in chronological order.
    
    This shows the evolution of the user's goals over time,
    useful for understanding their journey and progress.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        List of goal dictionaries sorted by creation date (oldest first)
    """
    async def _run_inner() -> List[Dict[str, Any]]:
        import re
        db = _db()
        # Match all goal-related keys: goal, goal_123456, etc.
        cursor = db.memories.find(
            {"user_id": user_id, "key": {"$regex": re.compile("^goal", re.IGNORECASE)}}
        ).sort("created_at", 1)  # Oldest first for timeline view
        
        docs = []
        async for doc in cursor:
            docs.append({
                "key": doc.get("key"),
                "value": doc.get("value"),
                "event_date": doc.get("event_date"),
                "created_at": str(doc.get("created_at", "")),
            })
        return docs
    
    try:
        goals = _run(_run_inner())
        logger.debug(f"[PersonalInfo] Retrieved {len(goals)} goals for user={user_id}")
        return goals
    except Exception as e:
        logger.error(f"[PersonalInfo] Failed to get goals timeline: {e}")
        return []


def get_facts_in_period(
    user_id: str,
    start: date,
    end: date
) -> List[Dict[str, Any]]:
    """
    Retrieve facts stored within a specific date range.
    
    Useful for monthly summaries or reviewing what was learned
    about a user during a specific period.
    
    Args:
        user_id: Unique user identifier
        start: Start date (inclusive)
        end: End date (inclusive)
        
    Returns:
        List of fact dictionaries created within the date range
    """
    async def _run_inner() -> List[Dict[str, Any]]:
        db = _db()
        cursor = db.memories.find({
            "user_id": user_id,
            "created_at": {
                "$gte": datetime.combine(start, datetime.min.time()),
                "$lte": datetime.combine(end, datetime.max.time())
            }
        }).sort("created_at", 1)
        
        docs = []
        async for doc in cursor:
            docs.append({
                "key": doc.get("key"),
                "value": doc.get("value"),
                "created_at": str(doc.get("created_at", "")),
            })
        return docs
    
    try:
        facts = _run(_run_inner())
        logger.debug(f"[PersonalInfo] Retrieved {len(facts)} facts in period for user={user_id}")
        return facts
    except Exception as e:
        logger.error(f"[PersonalInfo] Failed to get facts in period: {e}")
        return []


# ─── Format for AI Prompt ───────────────────────────────────────────────

def format_for_prompt(user_id: str) -> str:
    """
    Format all user facts into a readable string for AI context.
    
    This creates a structured summary of all known facts about the user,
    formatted as a bulleted list with labels and update timestamps.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        Formatted string suitable for injection into AI system prompt.
        Returns empty string if no facts are stored.
        
    Example Output:
        "Known facts about this user:
        - Name: Rohit (updated 2025-06-15)
        - Goal: Become a senior engineer
        - Location: Mumbai, India"
    """
    facts = get_all_facts(user_id)
    if not facts:
        logger.debug(f"[PersonalInfo] No facts to format for user={user_id}")
        return ""
    
    # Human-readable labels for common keys
    labels = {
        "name": "Name",
        "age": "Age",
        "goal": "Goal",
        "dream": "Dream",
        "aim": "Aim",
        "job": "Job",
        "workplace": "Workplace",
        "hobby": "Hobby",
        "interest": "Interest",
        "location": "Location",
        "email": "Email",
        "phone": "Phone",
        "partner": "Partner",
        "education": "Education",
        "degree": "Degree",
    }
    
    lines = []
    for f in facts:
        # Extract base key (remove numeric suffix for appendable keys)
        raw_key = f["key"].split("_")[0]
        label = labels.get(raw_key, raw_key.replace("_", " ").title())
        
        # Add update timestamp if available
        date_str = f" (updated {f['updated_at'][:10]})" if f.get("updated_at") else ""
        lines.append(f"- {label}: {f['value']}{date_str}")
    
    formatted = "Known facts about this user:\n" + "\n".join(lines)
    logger.debug(f"[PersonalInfo] Formatted {len(facts)} facts for user={user_id}")
    return formatted


# ─── Build Direct Answer ────────────────────────────────────────────────

def build_direct_answer(
    user_id: str,
    query_key: Optional[str]
) -> Optional[str]:
    """
    Build a direct answer for a personal info query.
    
    This function handles special query types and formats appropriate
    responses for the AI to use when answering questions about stored facts.
    
    Args:
        user_id: Unique user identifier
        query_key: The key being queried, or special values:
                   - "__earliest__": Return earliest memories
                   - None: Return all facts summary
                   - Specific key: Return that fact's value
                   
    Returns:
        Formatted answer string for the AI to use, or None if no data found
        
    Example:
        >>> build_direct_answer("user123", "name")
        "Your name is Rohit 😊"
        >>> build_direct_answer("user123", "__earliest__")
        "Here are the earliest things you shared with me:..."
    """
    # Special case: earliest memories
    if query_key == "__earliest__":
        from backend.memory.memory_manager import get_earliest_memories
        earliest = get_earliest_memories(user_id, limit=3)
        if not earliest:
            return None
        
        lines = [f'• [{m["created_at"][:10]}] "{m["message"]}"' for m in earliest]
        return (
            "Here are the earliest things you shared with me:\n"
            + "\n".join(lines)
            + "\n\nThese are your first memories in SoulSync. 🧠"
        )
    
    # Special case: all facts summary
    if query_key is None:
        facts = get_all_facts(user_id)
        if not facts:
            return None
        
        labels = {
            "name": "Name", "age": "Age", "goal": "Goal", "dream": "Dream",
            "aim": "Aim", "job": "Job", "hobby": "Hobby", "interest": "Interest",
            "location": "Location"
        }
        lines = []
        for f in facts:
            raw_key = f["key"].split("_")[0]
            label = labels.get(raw_key, raw_key.replace("_", " ").title())
            lines.append(f"• {label}: {f['value']}")
        
        return "Here's what I know about you:\n" + "\n".join(lines) + " 😊"
    
    # Special case: goals timeline
    if query_key == "goal":
        goals = get_goals_timeline(user_id)
        if not goals:
            return None
        
        if len(goals) == 1:
            g = goals[0]
            return f"Your goal is: {g['value']} 💪"
        
        lines = [f"• [{g.get('event_date') or g['created_at'][:10]}] {g['value']}" for g in goals]
        return "Your goals over time:\n" + "\n".join(lines) + " 💪"
    
    # Standard case: single fact lookup
    value = get_fact(user_id, query_key)
    if not value:
        return None
    
    # Pre-formatted answers for common keys
    answers = {
        "name": f"Your name is {value} 😊",
        "age": f"You are {value} years old.",
        "goal": f"Your goal is: {value} 💪",
        "dream": f"Your dream is: {value} ✨",
        "aim": f"Your aim is: {value}",
        "job": f"You work as: {value}",
        "hobby": f"Your hobby is: {value}",
        "interest": f"You enjoy: {value}",
        "location": f"You live in {value}.",
        "email": f"Your email is {value}.",
        "phone": f"Your phone number is {value}.",
    }
    
    return answers.get(
        query_key,
        f"Your {query_key.replace('_', ' ')} is: {value}"
    )