from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("CROWDLIKE_DB", "crowdlike.db")

@contextmanager
def connect():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield con
    finally:
        con.close()

def init_db() -> None:
    with connect() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            pass_salt BLOB NOT NULL,
            pass_hash BLOB NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            wallet_address TEXT NOT NULL DEFAULT '',
            accent TEXT NOT NULL DEFAULT '#46A3FF',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        con.commit()
