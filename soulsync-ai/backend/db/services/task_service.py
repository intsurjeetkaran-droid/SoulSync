"""
SoulSync AI - Task Service
CRUD operations for user tasks backed by MongoDB.
Includes auto-detection of tasks from chat messages.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..mongo.repository import MongoRepository

logger = logging.getLogger("soulsync.services.task")


class TaskService:
    """
    Task management service backed by MongoDB.
    """

    def __init__(self, mongo_repo: MongoRepository):
        self.mongo = mongo_repo

    # ─── Create Task ──────────────────────────────────────

    async def create_task(
        self,
        user_id: str,
        title: str,
        due_date: Optional[str] = None,
        priority: str = "medium",
        source: str = "manual",
    ) -> dict:
        """
        Create a new task for a user.

        Args:
            user_id  : unique user identifier
            title    : task description
            due_date : optional due date string (e.g. "2026-05-01")
            priority : high / medium / low
            source   : manual / auto

        Returns:
            The created task dict.
        """
        try:
            task = await self.mongo.create_task(
                user_id=user_id,
                title=title,
                due_date=due_date,
                priority=priority,
                source=source,
            )
            logger.info(f"[TaskService] Created task '{title}' for user={user_id}")
            return task
        except Exception as e:
            logger.error(f"[TaskService] create_task failed: {e}", exc_info=True)
            raise

    # ─── Get Tasks ────────────────────────────────────────

    async def get_tasks(
        self, user_id: str, status: Optional[str] = None
    ) -> list:
        """
        Fetch tasks for a user.

        Args:
            user_id : unique user identifier
            status  : 'pending' | 'completed' | None (all)

        Returns:
            List of task dicts sorted by priority.
        """
        try:
            return await self.mongo.get_tasks(user_id, status=status)
        except Exception as e:
            logger.error(f"[TaskService] get_tasks failed: {e}", exc_info=True)
            return []

    # ─── Complete Task ────────────────────────────────────

    async def complete_task(self, task_id: str, user_id: str) -> dict:
        """
        Mark a task as completed.

        Returns:
            dict with success flag and task_id.
        """
        try:
            updated = await self.mongo.complete_task(task_id=task_id, user_id=user_id)
            if updated:
                logger.info(f"[TaskService] Task {task_id} completed for user={user_id}")
                return {"success": True, "task_id": task_id, "status": "completed"}
            else:
                return {"success": False, "task_id": task_id, "error": "Task not found"}
        except Exception as e:
            logger.error(f"[TaskService] complete_task failed: {e}", exc_info=True)
            return {"success": False, "task_id": task_id, "error": str(e)}

    # ─── Delete Task ──────────────────────────────────────

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """
        Delete a task.

        Returns:
            True if deleted, False if not found.
        """
        try:
            deleted = await self.mongo.delete_task(task_id=task_id, user_id=user_id)
            if deleted:
                logger.info(f"[TaskService] Task {task_id} deleted for user={user_id}")
            return deleted
        except Exception as e:
            logger.error(f"[TaskService] delete_task failed: {e}", exc_info=True)
            return False

    # ─── Auto-Detect and Create ───────────────────────────

    async def auto_detect_and_create(
        self, user_id: str, message: str
    ) -> list:
        """
        Detect tasks from a chat message and create them automatically.

        Uses the existing task_detector module for NLP-based detection.

        Returns:
            List of created task dicts.
        """
        try:
            from backend.tasks.task_detector import detect_tasks
            detected = detect_tasks(message)
            if not detected:
                return []

            created = []
            for task_data in detected:
                task = await self.create_task(
                    user_id=user_id,
                    title=task_data["title"],
                    due_date=task_data.get("due_date"),
                    priority=task_data.get("priority", "medium"),
                    source="auto",
                )
                created.append(task)

            logger.info(
                f"[TaskService] Auto-created {len(created)} tasks for user={user_id}"
            )
            return created
        except Exception as e:
            logger.error(f"[TaskService] auto_detect_and_create failed: {e}", exc_info=True)
            return []

    # ─── Task Summary ─────────────────────────────────────

    async def get_task_summary(self, user_id: str) -> dict:
        """
        Return task counts by status and priority.

        Returns:
            dict with total, pending, completed, high_priority_pending counts.
        """
        try:
            all_tasks = await self.get_tasks(user_id)
            pending = [t for t in all_tasks if t.get("status") == "pending"]
            completed = [t for t in all_tasks if t.get("status") == "completed"]
            high_pri = [t for t in pending if t.get("priority") == "high"]

            return {
                "total": len(all_tasks),
                "pending": len(pending),
                "completed": len(completed),
                "high_priority_pending": len(high_pri),
            }
        except Exception as e:
            logger.error(f"[TaskService] get_task_summary failed: {e}", exc_info=True)
            return {"total": 0, "pending": 0, "completed": 0, "high_priority_pending": 0}
