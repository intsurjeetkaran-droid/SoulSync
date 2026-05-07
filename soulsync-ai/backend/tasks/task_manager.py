"""
SoulSync AI - Task Manager (MongoDB)
=====================================

Complete task CRUD (Create, Read, Update, Delete) operations backed by MongoDB.
This module handles all task-related operations including auto-detection from
user messages, manual task creation, and task lifecycle management.

Task Lifecycle:
    1. Created (pending) → User can manually create or AI auto-detects from chat
    2. Active (pending) → Task appears in user's task list
    3. Completed → User marks task as done, it moves to completed status
    4. Deleted → Task is removed from the system

Task Sources:
    - "manual": User explicitly creates a task
    - "auto": AI automatically detects and creates task from user message

Priority Levels:
    - high: Urgent tasks that need immediate attention
    - medium: Normal priority tasks (default)
    - low: Tasks that can be done when convenient

Usage:
    >>> from backend.tasks.task_manager import create_task, get_tasks, complete_task
    >>> task = create_task("user123", "Buy groceries", due_date="tomorrow", priority="high")
    >>> tasks = get_tasks("user123", status="pending")
    >>> complete_task(task["task_id"], "user123")
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any

from backend.tasks.task_detector import detect_tasks

logger = logging.getLogger("soulsync.task_manager")

# ─── Helper Functions ────────────────────────────────────────────────────

def _run(coro):
    """
    Execute an async coroutine synchronously.
    
    This helper handles the sync/async boundary for MongoDB operations.
    See personal_info.py for detailed explanation of this pattern.
    
    Args:
        coro: An async coroutine to execute
        
    Returns:
        The result of the coroutine
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _db():
    """
    Get the MongoDB database connection.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    from backend.db.mongo.connection import get_mongo_db
    return get_mongo_db()


def _serialize(doc: dict) -> Dict[str, Any]:
    """
    Convert MongoDB document to standardized task dictionary.
    
    Args:
        doc: Raw MongoDB document
        
    Returns:
        Standardized task dictionary with consistent field names
    """
    if not doc:
        return {}
    return {
        "id": doc.get("task_id", str(doc.get("_id", ""))),
        "task_id": doc.get("task_id", ""),
        "user_id": doc.get("user_id"),
        "title": doc.get("title"),
        "due_date": doc.get("due_date"),
        "priority": doc.get("priority", "medium"),
        "status": doc.get("status", "pending"),
        "source": doc.get("source", "manual"),
        "created_at": str(doc.get("created_at", "")),
    }


# ─── Create Task ─────────────────────────────────────────────────────────

def create_task(
    user_id: str,
    title: str,
    due_date: str = None,
    priority: str = "medium",
    source: str = "manual"
) -> Dict[str, Any]:
    """
    Create a new task for a user.
    
    Args:
        user_id: Unique user identifier
        title: Task description/title
        due_date: When the task should be completed (e.g., "tomorrow", "Friday", "2025-06-15")
        priority: Task priority level - "high", "medium", or "low"
        source: Task origin - "manual" (user-created) or "auto" (AI-detected)
        
    Returns:
        Created task dictionary with all fields including generated task_id
        
    Example:
        >>> task = create_task("user123", "Call dentist", due_date="tomorrow", priority="high")
        >>> print(task["task_id"])  # UUID string
    """
    async def _run_inner():
        db = _db()
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        doc = {
            "task_id": task_id,
            "user_id": user_id,
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "source": source,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.tasks.insert_one(doc)
        logger.info(f"[TaskMgr] Created task: user={user_id} | title='{title}' | priority={priority}")
        return _serialize(doc)
    
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.error(f"[TaskMgr] create_task failed: {e}")
        raise


# ─── Get Tasks ───────────────────────────────────────────────────────────

def get_tasks(user_id: str, status: str = None) -> List[Dict[str, Any]]:
    """
    Retrieve tasks for a user, optionally filtered by status.
    
    Tasks are sorted by priority (high → medium → low) then by creation date.
    
    Args:
        user_id: Unique user identifier
        status: Optional status filter - "pending" or "completed"
        
    Returns:
        List of task dictionaries, sorted by priority
        
    Example:
        >>> pending = get_tasks("user123", status="pending")
        >>> all_tasks = get_tasks("user123")
    """
    async def _run_inner() -> List[Dict[str, Any]]:
        db = _db()
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        cursor = db.tasks.find(query).sort("created_at", -1)
        docs = [_serialize(doc) async for doc in cursor]
        
        # Sort by priority (high first, then medium, then low)
        priority_order = {"high": 1, "medium": 2, "low": 3}
        docs.sort(key=lambda d: priority_order.get(d.get("priority", "medium"), 2))
        
        return docs
    
    try:
        tasks = _run(_run_inner())
        logger.debug(f"[TaskMgr] Retrieved {len(tasks)} tasks for user={user_id}")
        return tasks
    except Exception as e:
        logger.error(f"[TaskMgr] get_tasks failed: {e}")
        return []


# ─── Complete Task ───────────────────────────────────────────────────────

def complete_task(task_id: str, user_id: str) -> Dict[str, Any]:
    """
    Mark a task as completed.
    
    Args:
        task_id: Task identifier (can be string UUID or legacy int ID)
        user_id: Unique user identifier (for security check)
        
    Returns:
        Updated task dictionary, or empty dict if task not found
        
    Example:
        >>> result = complete_task("abc-123-def", "user123")
        >>> if result:
        ...     print(f"Completed: {result['title']}")
    """
    async def _run_inner():
        db = _db()
        task_id_str = str(task_id)
        now = datetime.utcnow()
        
        result = await db.tasks.find_one_and_update(
            {"$or": [{"task_id": task_id_str}, {"task_id": task_id}], "user_id": user_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": now,
                    "updated_at": now,
                }
            },
            return_document=True,
        )
        
        if result:
            logger.info(f"[TaskMgr] Completed task: user={user_id} | task_id={task_id_str}")
        else:
            logger.warning(f"[TaskMgr] Task not found for completion: user={user_id} | task_id={task_id_str}")
        
        return _serialize(result) if result else {}
    
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.error(f"[TaskMgr] complete_task failed: {e}")
        return {}


# ─── Delete Task ─────────────────────────────────────────────────────────

def delete_task(task_id: str, user_id: str) -> bool:
    """
    Permanently delete a task.
    
    Args:
        task_id: Task identifier (can be string UUID or legacy int ID)
        user_id: Unique user identifier (for security check)
        
    Returns:
        True if task was deleted, False if not found
        
    Example:
        >>> if delete_task("abc-123-def", "user123"):
        ...     print("Task deleted successfully")
    """
    async def _run_inner() -> bool:
        db = _db()
        task_id_str = str(task_id)
        
        result = await db.tasks.delete_one(
            {"$or": [{"task_id": task_id_str}, {"task_id": task_id}], "user_id": user_id}
        )
        
        if result.deleted_count > 0:
            logger.info(f"[TaskMgr] Deleted task: user={user_id} | task_id={task_id_str}")
            return True
        else:
            logger.warning(f"[TaskMgr] Task not found for deletion: user={user_id} | task_id={task_id_str}")
            return False
    
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.error(f"[TaskMgr] delete_task failed: {e}")
        return False


# ─── Auto-Create Tasks from Chat ─────────────────────────────────────────

def auto_create_tasks(user_id: str, message: str) -> List[Dict[str, Any]]:
    """
    Detect and create tasks from a user message.
    
    This function uses the task detector to identify task-related content
    in user messages and automatically creates corresponding tasks.
    
    Args:
        user_id: Unique user identifier
        message: User's message text to analyze
        
    Returns:
        List of created task dictionaries (may be empty if no tasks detected)
        
    Example:
        >>> tasks = auto_create_tasks("user123", "Remind me to call doctor tomorrow")
        >>> print(f"Created {len(tasks)} tasks")
    """
    detected = detect_tasks(message)
    created = []
    
    for task_data in detected:
        try:
            task = create_task(
                user_id=user_id,
                title=task_data["title"],
                due_date=task_data.get("due_date"),
                priority=task_data.get("priority", "medium"),
                source="auto",  # Mark as AI-detected
            )
            created.append(task)
        except Exception as e:
            logger.error(f"[TaskMgr] Failed to auto-create task: {e}")
    
    if created:
        logger.info(f"[TaskMgr] Auto-created {len(created)} tasks from message: user={user_id}")
    
    return created


# ─── Task Summary ────────────────────────────────────────────────────────

def get_task_summary(user_id: str) -> Dict[str, int]:
    """
    Get a summary of user's task statistics.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        Dictionary with task counts:
        - total: Total number of tasks
        - pending: Number of pending tasks
        - completed: Number of completed tasks
        - high_priority_pending: Number of high-priority pending tasks
        
    Example:
        >>> summary = get_task_summary("user123")
        >>> print(f"You have {summary['pending']} pending tasks")
    """
    all_tasks = get_tasks(user_id)
    pending = [t for t in all_tasks if t["status"] == "pending"]
    completed = [t for t in all_tasks if t["status"] == "completed"]
    high_pri = [t for t in pending if t["priority"] == "high"]
    
    summary = {
        "total": len(all_tasks),
        "pending": len(pending),
        "completed": len(completed),
        "high_priority_pending": len(high_pri),
    }
    
    logger.debug(f"[TaskMgr] Summary for user={user_id}: {summary}")
    return summary


# ─── Update Task Priority ────────────────────────────────────────────────

def update_task_priority(task_id: str, user_id: str, priority: str) -> bool:
    """
    Update the priority level of a task.
    
    Args:
        task_id: Task identifier
        user_id: Unique user identifier
        priority: New priority level - "high", "medium", or "low"
        
    Returns:
        True if updated successfully, False otherwise
    """
    if priority not in ("high", "medium", "low"):
        logger.warning(f"[TaskMgr] Invalid priority: {priority}")
        return False
    
    async def _run_inner() -> bool:
        db = _db()
        task_id_str = str(task_id)
        now = datetime.utcnow()
        
        result = await db.tasks.update_one(
            {"$or": [{"task_id": task_id_str}, {"task_id": task_id}], "user_id": user_id},
            {"$set": {"priority": priority, "updated_at": now}}
        )
        
        if result.modified_count > 0:
            logger.info(f"[TaskMgr] Updated priority: user={user_id} | task_id={task_id_str} | priority={priority}")
            return True
        else:
            logger.warning(f"[TaskMgr] Task not found for priority update: user={user_id} | task_id={task_id_str}")
            return False
    
    try:
        return _run(_run_inner())
    except Exception as e:
        logger.error(f"[TaskMgr] update_task_priority failed: {e}")
        return False