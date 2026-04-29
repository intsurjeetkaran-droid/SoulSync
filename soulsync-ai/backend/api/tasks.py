"""
SoulSync AI - Tasks API Router
Endpoints:
  POST /tasks              : create a task manually
  GET  /tasks/{user_id}    : get all tasks for user
  PUT  /tasks/{id}/complete: mark task as done
  DELETE /tasks/{id}       : delete a task
  POST /tasks/auto-detect  : detect + create tasks from text
  GET  /tasks/{user_id}/summary : task summary
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.tasks.task_manager import (
    create_task, get_tasks, complete_task,
    delete_task, auto_create_tasks, get_task_summary
)

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    user_id  : str
    title    : str
    due_date : Optional[str] = None
    priority : str = "medium"


class AutoDetectRequest(BaseModel):
    user_id : str
    message : str


# ─── POST /tasks ──────────────────────────────────────────

@router.post("/tasks")
async def create_task_endpoint(request: CreateTaskRequest):
    """Create a task manually."""
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    try:
        task = create_task(
            user_id  = request.user_id,
            title    = request.title,
            due_date = request.due_date,
            priority = request.priority,
            source   = "manual"
        )
        return {"status": "created", "task": task}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /tasks/{user_id} ─────────────────────────────────

@router.get("/tasks/{user_id}")
async def get_tasks_endpoint(user_id: str, status: Optional[str] = None):
    """Get all tasks for a user. Optional ?status=pending|completed"""
    try:
        tasks   = get_tasks(user_id, status=status)
        summary = get_task_summary(user_id)
        return {
            "user_id": user_id,
            "summary": summary,
            "tasks"  : tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── PUT /tasks/{id}/complete ─────────────────────────────

@router.put("/tasks/{task_id}/complete")
async def complete_task_endpoint(task_id: int, user_id: str):
    """Mark a task as completed."""
    try:
        result = complete_task(task_id, user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found.")
        return {"status": "completed", "task": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── DELETE /tasks/{id} ───────────────────────────────────

@router.delete("/tasks/{task_id}")
async def delete_task_endpoint(task_id: int, user_id: str):
    """Delete a task."""
    try:
        deleted = delete_task(task_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Task not found.")
        return {"status": "deleted", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST /tasks/auto-detect ──────────────────────────────

@router.post("/tasks/auto-detect")
async def auto_detect_tasks(request: AutoDetectRequest):
    """
    Detect and create tasks from a natural language message.
    Example: "I need to finish my report by Friday"
    """
    try:
        tasks = auto_create_tasks(request.user_id, request.message)
        return {
            "user_id"       : request.user_id,
            "message"       : request.message,
            "tasks_created" : len(tasks),
            "tasks"         : tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
