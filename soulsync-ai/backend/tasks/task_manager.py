"""
SoulSync AI - Task Manager
Handles all task CRUD operations with PostgreSQL.

Operations:
  create_task    : add a new task
  get_tasks      : fetch tasks for a user
  complete_task  : mark task as done
  delete_task    : remove a task
  auto_create    : detect + create tasks from chat message
"""

from backend.memory.database      import get_connection, get_cursor
from backend.memory.memory_manager import ensure_user_exists
from backend.tasks.task_detector   import detect_tasks


# ─── Create Task ──────────────────────────────────────────

def create_task(user_id: str, title: str,
                due_date: str = None, priority: str = "medium",
                source: str = "manual") -> dict:
    """
    Create a new task for a user.

    Returns the created task as a dict.
    """
    ensure_user_exists(user_id)

    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            INSERT INTO tasks (user_id, title, due_date, priority, status, source)
            VALUES (%s, %s, %s, %s, 'pending', %s)
            RETURNING id, user_id, title, due_date, priority, status, source, created_at;
            """,
            (user_id, title, due_date, priority, source)
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)
    finally:
        cur.close()
        conn.close()


# ─── Get Tasks ────────────────────────────────────────────

def get_tasks(user_id: str, status: str = None) -> list:
    """
    Fetch tasks for a user.

    Args:
        user_id : unique user identifier
        status  : filter by 'pending' or 'completed' (None = all)

    Returns list of task dicts.
    """
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        if status:
            cur.execute(
                """
                SELECT id, user_id, title, due_date, priority,
                       status, source, created_at
                FROM tasks
                WHERE user_id = %s AND status = %s
                ORDER BY
                    CASE priority
                        WHEN 'high'   THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low'    THEN 3
                    END,
                    created_at DESC;
                """,
                (user_id, status)
            )
        else:
            cur.execute(
                """
                SELECT id, user_id, title, due_date, priority,
                       status, source, created_at
                FROM tasks
                WHERE user_id = %s
                ORDER BY
                    CASE priority
                        WHEN 'high'   THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low'    THEN 3
                    END,
                    created_at DESC;
                """,
                (user_id,)
            )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        cur.close()
        conn.close()


# ─── Complete Task ────────────────────────────────────────

def complete_task(task_id: int, user_id: str) -> dict:
    """Mark a task as completed."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            UPDATE tasks
            SET status = 'completed'
            WHERE id = %s AND user_id = %s
            RETURNING id, title, status;
            """,
            (task_id, user_id)
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row) if row else {}
    finally:
        cur.close()
        conn.close()


# ─── Delete Task ──────────────────────────────────────────

def delete_task(task_id: int, user_id: str) -> bool:
    """Delete a task. Returns True if deleted."""
    conn = get_connection()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            "DELETE FROM tasks WHERE id = %s AND user_id = %s;",
            (task_id, user_id)
        )
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        cur.close()
        conn.close()


# ─── Auto-Create from Chat ────────────────────────────────

def auto_create_tasks(user_id: str, message: str) -> list:
    """
    Detect and create tasks from a chat message automatically.

    Returns list of created task dicts.
    """
    detected = detect_tasks(message)
    created  = []

    for task_data in detected:
        task = create_task(
            user_id  = user_id,
            title    = task_data["title"],
            due_date = task_data.get("due_date"),
            priority = task_data.get("priority", "medium"),
            source   = "auto"
        )
        created.append(task)

    return created


# ─── Task Summary ─────────────────────────────────────────

def get_task_summary(user_id: str) -> dict:
    """Return task counts by status."""
    all_tasks = get_tasks(user_id)
    pending   = [t for t in all_tasks if t["status"] == "pending"]
    completed = [t for t in all_tasks if t["status"] == "completed"]
    high_pri  = [t for t in pending   if t["priority"] == "high"]

    return {
        "total"    : len(all_tasks),
        "pending"  : len(pending),
        "completed": len(completed),
        "high_priority_pending": len(high_pri),
    }
