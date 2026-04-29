"""
SoulSync AI - Database Connection
Manages PostgreSQL connection using psycopg2
Reads config from .env file
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

# ─── DB Config ────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "soulsync_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_connection():
    """
    Create and return a new PostgreSQL connection.
    Returns a connection with RealDictCursor (rows as dicts).
    """
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


def get_cursor(conn):
    """Return a dict-based cursor from an existing connection."""
    return conn.cursor(cursor_factory=RealDictCursor)


def test_connection():
    """Test the database connection. Returns True if successful."""
    try:
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT version();")
        version = cur.fetchone()
        conn.close()
        print(f"[DB] Connected: {version['version'][:50]}...")
        return True
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        return False
