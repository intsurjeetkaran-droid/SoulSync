"""
SoulSync AI - Database Schema
Creates all required tables in PostgreSQL:
  - users         : registered users
  - memories      : all conversation memories per user
  - personal_info : structured key/value personal facts (name, goal, etc.)
  - activities    : extracted activity logs
  - tasks         : user tasks
  - mood_logs     : mood tracking
"""

from backend.memory.database import get_connection, get_cursor

# ─── SQL Statements ───────────────────────────────────────

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    user_id     VARCHAR(100) UNIQUE NOT NULL,
    name        VARCHAR(200),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_MEMORIES_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    id                SERIAL PRIMARY KEY,
    user_id           VARCHAR(100) NOT NULL,
    role              VARCHAR(20)  NOT NULL,   -- 'user' or 'assistant'
    message           TEXT         NOT NULL,
    importance_score  INT          DEFAULT 5,  -- 0-15 scale
    created_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

CREATE_INDEX_USER_ID = """
CREATE INDEX IF NOT EXISTS idx_memories_user_id
ON memories(user_id);
"""

CREATE_INDEX_CREATED_AT = """
CREATE INDEX IF NOT EXISTS idx_memories_created_at
ON memories(created_at);
"""

# ─── NEW: Structured personal info table ──────────────────
CREATE_PERSONAL_INFO_TABLE = """
CREATE TABLE IF NOT EXISTS personal_info (
    id          SERIAL PRIMARY KEY,
    user_id     VARCHAR(100) NOT NULL,
    key         VARCHAR(100) NOT NULL,   -- e.g. 'name', 'goal', 'age', 'job'
    value       TEXT         NOT NULL,   -- e.g. 'Rohit'
    source_text TEXT,                    -- original sentence that triggered this
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (user_id, key)
);
"""

CREATE_INDEX_PERSONAL_INFO = """
CREATE INDEX IF NOT EXISTS idx_personal_info_user_key
ON personal_info(user_id, key);
"""

CREATE_ACTIVITIES_TABLE = """
CREATE TABLE IF NOT EXISTS activities (
    id          SERIAL PRIMARY KEY,
    user_id     VARCHAR(100) NOT NULL,
    raw_text    TEXT         NOT NULL,
    emotion     VARCHAR(100),
    activity    VARCHAR(200),
    status      VARCHAR(100),
    productivity VARCHAR(50),
    summary     TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

CREATE_INDEX_ACTIVITIES_USER = """
CREATE INDEX IF NOT EXISTS idx_activities_user_id
ON activities(user_id);
"""

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id          SERIAL PRIMARY KEY,
    user_id     VARCHAR(100) NOT NULL,
    title       TEXT         NOT NULL,
    due_date    VARCHAR(100),
    priority    VARCHAR(20)  DEFAULT 'medium',
    status      VARCHAR(20)  DEFAULT 'pending',
    source      VARCHAR(20)  DEFAULT 'manual',
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

CREATE_INDEX_TASKS_USER = """
CREATE INDEX IF NOT EXISTS idx_tasks_user_id
ON tasks(user_id);
"""

CREATE_MOOD_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS mood_logs (
    id           SERIAL PRIMARY KEY,
    user_id      VARCHAR(100) NOT NULL,
    mood         VARCHAR(50)  NOT NULL,
    mood_score   INT          NOT NULL,  -- 1 (very low) to 10 (very high)
    note         TEXT,
    day_of_week  VARCHAR(10),            -- Monday, Tuesday, etc.
    hour_of_day  INT,                    -- 0-23
    source       VARCHAR(20) DEFAULT 'manual',  -- 'manual' or 'auto'
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

CREATE_INDEX_MOOD_USER = """
CREATE INDEX IF NOT EXISTS idx_mood_logs_user_id
ON mood_logs(user_id);
"""

# ─── NEW: Typed memory collections ────────────────────────
CREATE_MEMORY_COLLECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS memory_collections (
    id            SERIAL PRIMARY KEY,
    user_id       VARCHAR(100) NOT NULL,
    collection    VARCHAR(50)  NOT NULL,
    content       TEXT         NOT NULL,
    event_date    DATE,
    importance    INT          DEFAULT 5,
    summary       TEXT,
    extra         JSONB        DEFAULT '{}',
    created_at    TIMESTAMP    DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

CREATE_INDEX_COLLECTIONS_USER = """
CREATE INDEX IF NOT EXISTS idx_mc_user_collection
ON memory_collections(user_id, collection);
"""

CREATE_INDEX_COLLECTIONS_DATE = """
CREATE INDEX IF NOT EXISTS idx_mc_event_date
ON memory_collections(user_id, event_date);
"""

# ─── NEW: Monthly summaries ────────────────────────────────
CREATE_MONTHLY_SUMMARIES_TABLE = """
CREATE TABLE IF NOT EXISTS monthly_summaries (
    id               SERIAL PRIMARY KEY,
    user_id          VARCHAR(100) NOT NULL,
    year_month       VARCHAR(7)   NOT NULL,
    experiences      JSONB        DEFAULT '[]',
    achievements     JSONB        DEFAULT '[]',
    emotions_trend   TEXT,
    key_people       JSONB        DEFAULT '[]',
    tasks_completed  INT          DEFAULT 0,
    dominant_mood    VARCHAR(50),
    full_summary     TEXT,
    created_at       TIMESTAMP    DEFAULT NOW(),
    updated_at       TIMESTAMP    DEFAULT NOW(),

    UNIQUE (user_id, year_month),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

CREATE_INDEX_MONTHLY_USER = """
CREATE INDEX IF NOT EXISTS idx_monthly_user_month
ON monthly_summaries(user_id, year_month);
"""

# ─── Life Timeline ─────────────────────────────────────────
CREATE_LIFE_TIMELINE_TABLE = """
CREATE TABLE IF NOT EXISTS life_timeline (
    id               SERIAL PRIMARY KEY,
    user_id          VARCHAR(100) NOT NULL,
    entry_date       DATE         NOT NULL,
    entry_time       TIME,
    entry_datetime   TIMESTAMP    NOT NULL DEFAULT NOW(),
    content          TEXT         NOT NULL,
    collection_type  VARCHAR(50)  NOT NULL DEFAULT 'conversation',
    significance     INT          NOT NULL DEFAULT 5,
    tags             JSONB        DEFAULT '[]',
    people_involved  JSONB        DEFAULT '[]',
    location         VARCHAR(200),
    mood_at_time     VARCHAR(50),
    source           VARCHAR(20)  DEFAULT 'chat',
    created_at       TIMESTAMP    DEFAULT NOW(),
    updated_at       TIMESTAMP    DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

CREATE_INDEX_TIMELINE_USER_DATE = """
CREATE INDEX IF NOT EXISTS idx_lt_user_date
ON life_timeline(user_id, entry_date);
"""

CREATE_INDEX_TIMELINE_SIGNIFICANCE = """
CREATE INDEX IF NOT EXISTS idx_lt_significance
ON life_timeline(user_id, significance DESC);
"""

CREATE_INDEX_TIMELINE_COLLECTION = """
CREATE INDEX IF NOT EXISTS idx_lt_collection
ON life_timeline(user_id, collection_type);
"""

CREATE_LIFE_TIMELINE_DAYS_TABLE = """
CREATE TABLE IF NOT EXISTS life_timeline_days (
    id                   SERIAL PRIMARY KEY,
    user_id              VARCHAR(100) NOT NULL,
    day_date             DATE         NOT NULL,
    summary              TEXT,
    dominant_emotion     VARCHAR(50),
    significance         FLOAT        DEFAULT 5.0,
    entry_count          INT          DEFAULT 0,
    collections_touched  JSONB        DEFAULT '[]',
    key_events           JSONB        DEFAULT '[]',
    people               JSONB        DEFAULT '[]',
    locations            JSONB        DEFAULT '[]',
    created_at           TIMESTAMP    DEFAULT NOW(),
    updated_at           TIMESTAMP    DEFAULT NOW(),

    UNIQUE (user_id, day_date),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

CREATE_INDEX_TIMELINE_DAYS = """
CREATE INDEX IF NOT EXISTS idx_ltd_user_date
ON life_timeline_days(user_id, day_date);
"""


def create_tables():
    """
    Create all SoulSync tables if they don't exist.
    Safe to run multiple times (uses IF NOT EXISTS).
    """
    conn = get_connection()
    cur  = get_cursor(conn)

    try:
        print("[Schema] Creating tables...")

        cur.execute(CREATE_USERS_TABLE)
        print("[Schema] ✅ users table ready")

        cur.execute(CREATE_MEMORIES_TABLE)
        print("[Schema] ✅ memories table ready")

        # Migration: add importance_score column if missing
        cur.execute("""
            ALTER TABLE memories
            ADD COLUMN IF NOT EXISTS importance_score INT DEFAULT 5;
        """)
        print("[Schema] ✅ importance_score column ready")

        cur.execute(CREATE_INDEX_USER_ID)
        cur.execute(CREATE_INDEX_CREATED_AT)
        print("[Schema] ✅ memory indexes ready")

        cur.execute(CREATE_PERSONAL_INFO_TABLE)
        cur.execute(CREATE_INDEX_PERSONAL_INFO)
        # Migration: add event_date column if missing (for goal/dream date tracking)
        cur.execute("""
            ALTER TABLE personal_info
            ADD COLUMN IF NOT EXISTS event_date DATE;
        """)
        # Migration: add context column for richer metadata
        cur.execute("""
            ALTER TABLE personal_info
            ADD COLUMN IF NOT EXISTS context VARCHAR(50);
        """)
        print("[Schema] ✅ personal_info table ready")

        cur.execute(CREATE_ACTIVITIES_TABLE)
        cur.execute(CREATE_INDEX_ACTIVITIES_USER)
        print("[Schema] ✅ activities table ready")

        cur.execute(CREATE_TASKS_TABLE)
        cur.execute(CREATE_INDEX_TASKS_USER)
        print("[Schema] ✅ tasks table ready")

        cur.execute(CREATE_MOOD_LOGS_TABLE)
        cur.execute(CREATE_INDEX_MOOD_USER)
        print("[Schema] ✅ mood_logs table ready")

        cur.execute(CREATE_MEMORY_COLLECTIONS_TABLE)
        cur.execute(CREATE_INDEX_COLLECTIONS_USER)
        cur.execute(CREATE_INDEX_COLLECTIONS_DATE)
        # Migration: add updated_at if missing
        cur.execute("""
            ALTER TABLE memory_collections
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
        """)
        print("[Schema] ✅ memory_collections table ready")

        cur.execute(CREATE_MONTHLY_SUMMARIES_TABLE)
        cur.execute(CREATE_INDEX_MONTHLY_USER)
        print("[Schema] ✅ monthly_summaries table ready")

        cur.execute(CREATE_LIFE_TIMELINE_TABLE)
        cur.execute(CREATE_INDEX_TIMELINE_USER_DATE)
        cur.execute(CREATE_INDEX_TIMELINE_SIGNIFICANCE)
        cur.execute(CREATE_INDEX_TIMELINE_COLLECTION)
        print("[Schema] ✅ life_timeline table ready")

        cur.execute(CREATE_LIFE_TIMELINE_DAYS_TABLE)
        cur.execute(CREATE_INDEX_TIMELINE_DAYS)
        print("[Schema] ✅ life_timeline_days table ready")

        conn.commit()
        print("[Schema] All tables created successfully.")

    except Exception as e:
        conn.rollback()
        print(f"[Schema] ❌ Error: {e}")
        raise e

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    create_tables()
