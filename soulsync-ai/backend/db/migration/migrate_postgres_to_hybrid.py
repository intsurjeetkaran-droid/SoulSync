"""
SoulSync AI - Migration Script
PostgreSQL → MongoDB (chat/memory/tasks/logs) + MySQL (wallets)

Migration Steps:
  1.  Connect to existing PostgreSQL
  2.  Connect to new MongoDB + MySQL
  3.  Migrate users         → MongoDB users collection
  4.  Migrate memories      → MongoDB messages collection
  5.  Migrate personal_info → MongoDB memories collection
  6.  Migrate tasks         → MongoDB tasks collection
  7.  Migrate activities    → MongoDB activities collection
  8.  Migrate mood_logs     → MongoDB mood_logs collection
  9.  Create wallets in MySQL for all migrated users
  10. Verify counts match

Usage:
    python -m backend.db.migration.migrate_postgres_to_hybrid

    # Dry run (no writes):
    python -m backend.db.migration.migrate_postgres_to_hybrid --dry-run

    # Migrate specific tables only:
    python -m backend.db.migration.migrate_postgres_to_hybrid --tables users,tasks

Environment variables required (same as .env):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD  (PostgreSQL)
    MONGODB_URL, MONGODB_DB                           (MongoDB)
    MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD (MySQL)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid
from datetime import datetime
from typing import Optional

# ─── Logging Setup ────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("migration.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("soulsync.migration")


# ─── PostgreSQL Connection ────────────────────────────────

def get_pg_connection():
    """Create a psycopg2 connection to the legacy PostgreSQL database."""
    import os
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from dotenv import load_dotenv

    load_dotenv()

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "soulsync_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    conn.cursor_factory = RealDictCursor
    return conn


def pg_fetch_all(conn, query: str, params=None) -> list:
    """Execute a query and return all rows as dicts."""
    with conn.cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


# ─── Migration Stats ──────────────────────────────────────

class MigrationStats:
    def __init__(self):
        self.counts: dict[str, dict] = {}

    def record(self, table: str, pg_count: int, migrated: int, skipped: int = 0):
        self.counts[table] = {
            "pg_count": pg_count,
            "migrated": migrated,
            "skipped": skipped,
            "success": migrated == pg_count - skipped,
        }

    def print_summary(self):
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        all_ok = True
        for table, stats in self.counts.items():
            status = "✅" if stats["success"] else "⚠️ "
            if not stats["success"]:
                all_ok = False
            logger.info(
                f"{status} {table:25s} | PG: {stats['pg_count']:5d} | "
                f"Migrated: {stats['migrated']:5d} | Skipped: {stats['skipped']:5d}"
            )
        logger.info("=" * 60)
        logger.info("Overall: " + ("✅ SUCCESS" if all_ok else "⚠️  PARTIAL — check logs"))
        return all_ok


# ─── Individual Migration Functions ──────────────────────

async def migrate_users(
    pg_conn,
    mongo_db,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Migrate users table → MongoDB users collection.
    Preserves user_id, name, email. Sets empty password_hash for legacy users.
    Returns (pg_count, migrated_count).
    """
    logger.info("[migrate_users] Fetching from PostgreSQL...")
    rows = pg_fetch_all(pg_conn, "SELECT * FROM users ORDER BY id ASC;")
    pg_count = len(rows)
    logger.info(f"[migrate_users] Found {pg_count} users in PostgreSQL")

    if dry_run:
        logger.info(f"[migrate_users] DRY RUN — would migrate {pg_count} users")
        return pg_count, 0

    migrated = 0
    skipped = 0
    for row in rows:
        try:
            # Check if already migrated
            existing = await mongo_db.users.find_one({"user_id": row["user_id"]})
            if existing:
                skipped += 1
                continue

            doc = {
                "user_id": row["user_id"],
                "name": row.get("name") or row["user_id"],
                "email": (row.get("email") or f"{row['user_id']}@legacy.soulsync.ai").lower(),
                "password_hash": row.get("password") or "",
                "created_at": row.get("created_at") or datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "profile": {},
                "preferences": {},
            }
            await mongo_db.users.insert_one(doc)
            migrated += 1
        except Exception as e:
            logger.warning(f"[migrate_users] Failed for user_id={row.get('user_id')}: {e}")

    logger.info(f"[migrate_users] Migrated: {migrated} | Skipped (existing): {skipped}")
    return pg_count, migrated


async def migrate_memories(
    pg_conn,
    mongo_db,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Migrate memories table → MongoDB messages collection.
    Creates a default conversation per user to hold legacy messages.
    Returns (pg_count, migrated_count).
    """
    logger.info("[migrate_memories] Fetching from PostgreSQL...")
    rows = pg_fetch_all(
        pg_conn,
        "SELECT * FROM memories ORDER BY user_id, created_at ASC;"
    )
    pg_count = len(rows)
    logger.info(f"[migrate_memories] Found {pg_count} memory rows")

    if dry_run:
        logger.info(f"[migrate_memories] DRY RUN — would migrate {pg_count} messages")
        return pg_count, 0

    # Create one "Legacy Conversation" per user
    user_conv_map: dict[str, str] = {}
    migrated = 0

    for row in rows:
        user_id = row["user_id"]
        try:
            # Get or create legacy conversation for this user
            if user_id not in user_conv_map:
                conv_id = str(uuid.uuid4())
                conv_doc = {
                    "conversation_id": conv_id,
                    "user_id": user_id,
                    "title": "Legacy Conversation (Migrated)",
                    "created_at": row.get("created_at") or datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "message_count": 0,
                    "last_message_at": row.get("created_at") or datetime.utcnow(),
                }
                await mongo_db.conversations.insert_one(conv_doc)
                user_conv_map[user_id] = conv_id

            conv_id = user_conv_map[user_id]

            msg_doc = {
                "message_id": str(uuid.uuid4()),
                "conversation_id": conv_id,
                "user_id": user_id,
                "role": row.get("role", "user"),
                "content": row.get("message", ""),
                "importance_score": row.get("importance_score", 5),
                "emotion": "neutral",
                "intent": "normal_chat",
                "created_at": row.get("created_at") or datetime.utcnow(),
            }
            await mongo_db.messages.insert_one(msg_doc)

            # Update conversation message count
            await mongo_db.conversations.update_one(
                {"conversation_id": conv_id},
                {
                    "$inc": {"message_count": 1},
                    "$set": {"last_message_at": row.get("created_at") or datetime.utcnow()},
                },
            )
            migrated += 1
        except Exception as e:
            logger.warning(f"[migrate_memories] Failed for row id={row.get('id')}: {e}")

    logger.info(f"[migrate_memories] Migrated: {migrated} messages across {len(user_conv_map)} users")
    return pg_count, migrated


async def migrate_personal_info(
    pg_conn,
    mongo_db,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Migrate personal_info table → MongoDB memories collection.
    Returns (pg_count, migrated_count).
    """
    logger.info("[migrate_personal_info] Fetching from PostgreSQL...")
    rows = pg_fetch_all(pg_conn, "SELECT * FROM personal_info ORDER BY id ASC;")
    pg_count = len(rows)
    logger.info(f"[migrate_personal_info] Found {pg_count} personal info rows")

    if dry_run:
        logger.info(f"[migrate_personal_info] DRY RUN — would migrate {pg_count} facts")
        return pg_count, 0

    migrated = 0
    for row in rows:
        try:
            # Check for existing fact (upsert by user_id + key)
            existing = await mongo_db.memories.find_one(
                {"user_id": row["user_id"], "key": row["key"]}
            )
            if existing:
                # Update if newer
                await mongo_db.memories.update_one(
                    {"user_id": row["user_id"], "key": row["key"]},
                    {
                        "$set": {
                            "value": row["value"],
                            "source_text": row.get("source_text"),
                            "context": row.get("context", "general"),
                            "event_date": row.get("event_date"),
                            "updated_at": row.get("updated_at") or datetime.utcnow(),
                        }
                    },
                )
            else:
                doc = {
                    "memory_id": str(uuid.uuid4()),
                    "user_id": row["user_id"],
                    "key": row["key"],
                    "value": row["value"],
                    "context": row.get("context", "general"),
                    "source_text": row.get("source_text"),
                    "event_date": row.get("event_date"),
                    "created_at": row.get("created_at") or datetime.utcnow(),
                    "updated_at": row.get("updated_at") or datetime.utcnow(),
                }
                await mongo_db.memories.insert_one(doc)
            migrated += 1
        except Exception as e:
            logger.warning(f"[migrate_personal_info] Failed for row id={row.get('id')}: {e}")

    logger.info(f"[migrate_personal_info] Migrated: {migrated} facts")
    return pg_count, migrated


async def migrate_tasks(
    pg_conn,
    mongo_db,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Migrate tasks table → MongoDB tasks collection.
    Returns (pg_count, migrated_count).
    """
    logger.info("[migrate_tasks] Fetching from PostgreSQL...")
    rows = pg_fetch_all(pg_conn, "SELECT * FROM tasks ORDER BY id ASC;")
    pg_count = len(rows)
    logger.info(f"[migrate_tasks] Found {pg_count} tasks")

    if dry_run:
        logger.info(f"[migrate_tasks] DRY RUN — would migrate {pg_count} tasks")
        return pg_count, 0

    migrated = 0
    for row in rows:
        try:
            doc = {
                "task_id": str(uuid.uuid4()),
                "user_id": row["user_id"],
                "title": row["title"],
                "due_date": row.get("due_date"),
                "priority": row.get("priority", "medium"),
                "status": row.get("status", "pending"),
                "source": row.get("source", "manual"),
                "created_at": row.get("created_at") or datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "completed_at": None,
            }
            await mongo_db.tasks.insert_one(doc)
            migrated += 1
        except Exception as e:
            logger.warning(f"[migrate_tasks] Failed for row id={row.get('id')}: {e}")

    logger.info(f"[migrate_tasks] Migrated: {migrated} tasks")
    return pg_count, migrated


async def migrate_activities(
    pg_conn,
    mongo_db,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Migrate activities table → MongoDB activities collection.
    Returns (pg_count, migrated_count).
    """
    logger.info("[migrate_activities] Fetching from PostgreSQL...")
    rows = pg_fetch_all(pg_conn, "SELECT * FROM activities ORDER BY id ASC;")
    pg_count = len(rows)
    logger.info(f"[migrate_activities] Found {pg_count} activities")

    if dry_run:
        logger.info(f"[migrate_activities] DRY RUN — would migrate {pg_count} activities")
        return pg_count, 0

    migrated = 0
    for row in rows:
        try:
            doc = {
                "activity_id": str(uuid.uuid4()),
                "user_id": row["user_id"],
                "raw_text": row.get("raw_text", ""),
                "emotion": row.get("emotion", "neutral") or "neutral",
                "activity": row.get("activity", "") or "",
                "status": row.get("status", "") or "",
                "productivity": row.get("productivity", "") or "",
                "summary": row.get("summary", "") or "",
                "created_at": row.get("created_at") or datetime.utcnow(),
            }
            await mongo_db.activities.insert_one(doc)
            migrated += 1
        except Exception as e:
            logger.warning(f"[migrate_activities] Failed for row id={row.get('id')}: {e}")

    logger.info(f"[migrate_activities] Migrated: {migrated} activities")
    return pg_count, migrated


async def migrate_mood_logs(
    pg_conn,
    mongo_db,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Migrate mood_logs table → MongoDB mood_logs collection.
    Returns (pg_count, migrated_count).
    """
    logger.info("[migrate_mood_logs] Fetching from PostgreSQL...")
    rows = pg_fetch_all(pg_conn, "SELECT * FROM mood_logs ORDER BY id ASC;")
    pg_count = len(rows)
    logger.info(f"[migrate_mood_logs] Found {pg_count} mood logs")

    if dry_run:
        logger.info(f"[migrate_mood_logs] DRY RUN — would migrate {pg_count} mood logs")
        return pg_count, 0

    migrated = 0
    for row in rows:
        try:
            doc = {
                "log_id": str(uuid.uuid4()),
                "user_id": row["user_id"],
                "mood": row.get("mood", "neutral"),
                "mood_score": row.get("mood_score", 5),
                "note": row.get("note", "") or "",
                "day_of_week": row.get("day_of_week", "") or "",
                "hour_of_day": row.get("hour_of_day", 0) or 0,
                "source": row.get("source", "manual"),
                "created_at": row.get("created_at") or datetime.utcnow(),
            }
            await mongo_db.mood_logs.insert_one(doc)
            migrated += 1
        except Exception as e:
            logger.warning(f"[migrate_mood_logs] Failed for row id={row.get('id')}: {e}")

    logger.info(f"[migrate_mood_logs] Migrated: {migrated} mood logs")
    return pg_count, migrated


async def create_mysql_wallets(
    pg_conn,
    sql_repo,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Create MySQL wallets for all users from PostgreSQL.
    Returns (pg_count, created_count).
    """
    logger.info("[create_mysql_wallets] Fetching users from PostgreSQL...")
    rows = pg_fetch_all(pg_conn, "SELECT user_id FROM users ORDER BY id ASC;")
    pg_count = len(rows)
    logger.info(f"[create_mysql_wallets] Found {pg_count} users")

    if dry_run:
        logger.info(f"[create_mysql_wallets] DRY RUN — would create {pg_count} wallets")
        return pg_count, 0

    created = 0
    skipped = 0
    for row in rows:
        user_id = row["user_id"]
        try:
            existing = await sql_repo.get_wallet(user_id)
            if existing:
                skipped += 1
                continue
            await sql_repo.create_wallet(user_id=user_id, currency="INR")
            created += 1
        except Exception as e:
            logger.warning(f"[create_mysql_wallets] Failed for user_id={user_id}: {e}")

    logger.info(f"[create_mysql_wallets] Created: {created} | Skipped (existing): {skipped}")
    return pg_count, created


# ─── Main Migration Runner ────────────────────────────────

async def run_migration(
    dry_run: bool = False,
    tables: Optional[list[str]] = None,
) -> bool:
    """
    Run the full migration from PostgreSQL to MongoDB + MySQL.

    Args:
        dry_run : if True, only count rows without writing
        tables  : list of table names to migrate (None = all)

    Returns:
        True if all migrations succeeded.
    """
    all_tables = ["users", "memories", "personal_info", "tasks", "activities", "mood_logs", "wallets"]
    if tables:
        tables_to_run = [t for t in tables if t in all_tables]
    else:
        tables_to_run = all_tables

    logger.info("=" * 60)
    logger.info(f"SoulSync AI Migration — PostgreSQL → MongoDB + MySQL")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    logger.info(f"Tables: {', '.join(tables_to_run)}")
    logger.info("=" * 60)

    stats = MigrationStats()

    # ── Connect to PostgreSQL ──────────────────────────────
    logger.info("[Migration] Connecting to PostgreSQL...")
    try:
        pg_conn = get_pg_connection()
        logger.info("[Migration] PostgreSQL connected ✅")
    except Exception as e:
        logger.error(f"[Migration] PostgreSQL connection failed: {e}")
        return False

    # ── Connect to MongoDB ─────────────────────────────────
    logger.info("[Migration] Connecting to MongoDB...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from ..config import settings
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongo_db = mongo_client[settings.MONGODB_DB]
        # Test connection
        await mongo_db.command("ping")
        logger.info("[Migration] MongoDB connected ✅")
    except Exception as e:
        logger.error(f"[Migration] MongoDB connection failed: {e}")
        pg_conn.close()
        return False

    # ── Connect to MySQL ───────────────────────────────────
    sql_repo = None
    if "wallets" in tables_to_run:
        logger.info("[Migration] Connecting to MySQL...")
        try:
            from ..mysql.repository import SQLRepository
            from ..mysql.connection import init_mysql_tables
            await init_mysql_tables()
            sql_repo = SQLRepository()
            logger.info("[Migration] MySQL connected ✅")
        except Exception as e:
            logger.warning(f"[Migration] MySQL connection failed: {e} — skipping wallet migration")
            tables_to_run = [t for t in tables_to_run if t != "wallets"]

    # ── Initialize MongoDB indexes ─────────────────────────
    if not dry_run:
        try:
            from ..mongo.connection import init_mongo_indexes
            await init_mongo_indexes()
        except Exception as e:
            logger.warning(f"[Migration] Index init failed: {e}")

    # ── Run migrations ─────────────────────────────────────
    try:
        if "users" in tables_to_run:
            pg_c, mig_c = await migrate_users(pg_conn, mongo_db, dry_run)
            stats.record("users", pg_c, mig_c)

        if "memories" in tables_to_run:
            pg_c, mig_c = await migrate_memories(pg_conn, mongo_db, dry_run)
            stats.record("memories→messages", pg_c, mig_c)

        if "personal_info" in tables_to_run:
            pg_c, mig_c = await migrate_personal_info(pg_conn, mongo_db, dry_run)
            stats.record("personal_info→memories", pg_c, mig_c)

        if "tasks" in tables_to_run:
            pg_c, mig_c = await migrate_tasks(pg_conn, mongo_db, dry_run)
            stats.record("tasks", pg_c, mig_c)

        if "activities" in tables_to_run:
            pg_c, mig_c = await migrate_activities(pg_conn, mongo_db, dry_run)
            stats.record("activities", pg_c, mig_c)

        if "mood_logs" in tables_to_run:
            pg_c, mig_c = await migrate_mood_logs(pg_conn, mongo_db, dry_run)
            stats.record("mood_logs", pg_c, mig_c)

        if "wallets" in tables_to_run and sql_repo:
            pg_c, mig_c = await create_mysql_wallets(pg_conn, sql_repo, dry_run)
            stats.record("wallets (MySQL)", pg_c, mig_c)

    finally:
        pg_conn.close()
        mongo_client.close()
        logger.info("[Migration] Connections closed")

    return stats.print_summary()


# ─── CLI Entry Point ──────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Migrate SoulSync AI from PostgreSQL to MongoDB + MySQL"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count rows without writing to target databases",
    )
    parser.add_argument(
        "--tables",
        type=str,
        default=None,
        help="Comma-separated list of tables to migrate (default: all)",
    )
    args = parser.parse_args()

    tables = [t.strip() for t in args.tables.split(",")] if args.tables else None

    success = asyncio.run(run_migration(dry_run=args.dry_run, tables=tables))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
