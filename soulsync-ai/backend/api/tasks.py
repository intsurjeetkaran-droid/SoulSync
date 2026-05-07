"""
SoulSync AI - Tasks API Router
================================

Complete task management API with CRUD operations and AI-powered task detection.
Tasks can be created manually or automatically detected from natural language messages.

Endpoints:
    POST /tasks                  - Create a task manually
    GET  /tasks/{user_id}        - Get all tasks for user with summary
    PUT  /tasks/{id}/complete    - Mark task as done
    DELETE /tasks/{id}           - Delete a task
    POST /tasks/auto-detect      - Detect + create tasks from text
    GET  /tasks/{user_id}/summary - Get task statistics

Task Features:
    - Manual task creation with priority levels (high/medium/low)
    - Auto-detection from natural language (English, Hindi, Hinglish)
    - Task completion tracking with timestamps
    - Task summary statistics

Usage:
    # Create task
    POST /api/v1/tasks
    {"user_id": "user123", "title": "Buy groceries", "due_date": "tomorrow", "priority": "high"}
    
    # Auto-detect tasks
    POST /api/v1/tasks/auto-detect
    {"user_id": "user123", "message": "Remind me to call doctor tomorrow"}
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.tasks.task_manager import (
    create_task, get_tasks, complete_task,
    delete_task, auto_create_tasks, get_task_summary
)

logger = logging.getLogger("soulsync.api.tasks")
router = APIRouter()


# ─── Request/Response Schemas ────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    """Request schema for creating a new task."""
    user_id: str
    title: str
    due_date: Optional[str] = None
    priority: str = "medium"


class AutoDetectRequest(BaseModel):
    """Request schema for auto-detecting tasks from text."""
    user_id: str
    message: str


# ─── POST /tasks ─────────────────────────────────────────────────────────

@router.post("/tasks")
async def create_task_endpoint(request: CreateTaskRequest):
    """
    Create a task manually.
    
    Args:
        request: CreateTaskRequest with user_id, title, due_date, priority
        
    Returns:
        Created task with status
        
    Raises:
        HTTPException(400): If title is empty
        HTTPException(500): If creation fails
    """
    if not request.title.strip():
        logger.warning(f"[Tasks API] Empty title from user={request.user_id}")
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    
    try:
        task = create_task(
            user_id=request.user_id,
            title=request.title,
            due_date=request.due_date,
            priority=request.priority,
            source="manual"
        )
        logger.info(f"[Tasks API] Created task: user={request.user_id} | title='{request.title}'")
        
        return {"status": "created", "task": task}
    except Exception as e:
        logger.error(f"[Tasks API] Create failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /tasks/{user_id} ────────────────────────────────────────────────

@router.get("/tasks/{user_id}")
async def get_tasks_endpoint(user_id: str, status: Optional[str] = None):
    """
    Get all tasks for a user with summary statistics.
    
    Args:
        user_id: Unique user identifier
        status: Optional filter by status (pending/completed)
        
    Returns:
        Tasks list with summary statistics
        
    Raises:
        HTTPException(500): If retrieval fails
    """
    try:
        tasks = get_tasks(user_id, status=status)
        summary = get_task_summary(user_id)
        logger.debug(f"[Tasks API] Retrieved {len(tasks)} tasks for user={user_id}")
        
        return {
            "user_id": user_id,
            "summary": summary,
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"[Tasks API] Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── PUT /tasks/{id}/complete ────────────────────────────────────────────

@router.put("/tasks/{task_id}/complete")
async def complete_task_endpoint(task_id: int, user_id: str):
    """
    Mark a task as completed.
    
    Args:
        task_id: Task identifier
        user_id: Unique user identifier
        
    Returns:
        Completed task with status
        
    Raises:
        HTTPException(404): If task not found
        HTTPException(500): If completion fails
    """
    try:
        result = complete_task(task_id, user_id)
        if not result:
            logger.warning(f"[Tasks API] Task not found for completion: user={user_id} | task_id={task_id}")
            raise HTTPException(status_code=404, detail="Task not found.")
        
        logger.info(f"[Tasks API] Completed task: user={user_id} | task_id={task_id}")
        return {"status": "completed", "task": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Tasks API] Complete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── DELETE /tasks/{id} ──────────────────────────────────────────────────

@router.delete("/tasks/{task_id}")
async def delete_task_endpoint(task_id: int, user_id: str):
    """
    Delete a task permanently.
    
    Args:
        task_id: Task identifier
        user_id: Unique user identifier
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException(404): If task not found
        HTTPException(500): If deletion fails
    """
    try:
        deleted = delete_task(task_id, user_id)
        if not deleted:
            logger.warning(f"[Tasks API] Task not found for deletion: user={user_id} | task_id={task_id}")
            raise HTTPException(status_code=404, detail="Task not found.")
        
        logger.info(f"[Tasks API] Deleted task: user={user_id} | task_id={task_id}")
        return {"status": "deleted", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Tasks API] Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST /tasks/auto-detect ─────────────────────────────────────────────

@router.post("/tasks/auto-detect")
async def auto_detect_tasks(request: AutoDetectRequest):
    """
    Detect and create tasks from a natural language message.
    
    This endpoint uses AI to identify task-related content in user messages
    and automatically creates corresponding tasks. Supports English, Hindi,
    and Hinglish.
    
    Args:
        request: AutoDetectRequest with user_id and message
        
    Returns:
        List of detected and created tasks
        
    Raises:
        HTTPException(500): If detection fails
        
    Example:
        POST /api/v1/tasks/auto-detect
        {"user_id": "user123", "message": "I need to finish my report by Friday"}
    """
    try:
        tasks = auto_create_tasks(request.user_id, request.message)
        logger.info(f"[Tasks API] Auto-detected {len(tasks)} tasks from message: user={request.user_id}")
        
        return {
            "user_id": request.user_id,
            "message": request.message,
            "tasks_created": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"[Tasks API] Auto-detect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))