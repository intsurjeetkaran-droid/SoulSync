"""
SoulSync AI - Database shim (MongoDB-only)
get_connection / get_cursor are no-ops kept for import compatibility.
All real DB work now goes through MongoDB via Motor.
"""

import logging
logger = logging.getLogger("soulsync.db.shim")


def get_mongo_db():
    from backend.db.mongo.connection import get_mongo_db as _get
    return _get()


# ── Legacy shim — nothing uses these for real anymore ─────
def get_connection():
    raise RuntimeError("[DB] PostgreSQL removed. Use MongoDB via get_mongo_db().")

def get_cursor(conn):
    raise RuntimeError("[DB] PostgreSQL removed. Use MongoDB via get_mongo_db().")

def test_connection():
    return False
