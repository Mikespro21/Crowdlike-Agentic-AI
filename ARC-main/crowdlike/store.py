
from __future__ import annotations

import json
import sqlite3
import time
import secrets
import hashlib
from pathlib import Path

from crowdlike.security import clean_username, clean_display_name

DB_PATH = Path(".crowdlike_data") / "crowdlike.db"

def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username   TEXT PRIMARY KEY,
                pin_hash   TEXT,
                created_at INTEGER,
                data_json  TEXT
            )
            """
        )
        conn.commit()

def _hash_pin(pin: str, salt: str) -> str:
    return hashlib.sha256((salt + "|" + pin).encode("utf-8")).hexdigest()

def make_pin_hash(pin: str) -> str:
    pin = (pin or "").strip()
    if pin == "":
        return ""  # no pin set
    salt = secrets.token_hex(16)
    return f"{salt}${_hash_pin(pin, salt)}"

def check_pin_hash(pin: str, stored: str) -> bool:
    pin = (pin or "").strip()
    stored = stored or ""
    if stored == "":
        return pin == ""  # no pin required
    try:
        salt, h = stored.split("$", 1)
    except ValueError:
        return False
    return _hash_pin(pin, salt) == h

def get_user(username: str):
    init_db()
    u = (username or "").strip().lower()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
    if not row:
        return None
    try:
        data = json.loads(row["data_json"] or "{}")
    except Exception:
        data = {}
    return {
        "username": row["username"],
        "pin_hash": row["pin_hash"] or "",
        "created_at": int(row["created_at"] or 0),
        "data": data,
    }

def create_user(username: str, pin: str, data: dict):
    init_db()
    u = clean_username(username)
    if get_user(u):
        return False, "Username already exists."
    pin_hash = make_pin_hash(pin)
    created_at = int(time.time())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO users(username,pin_hash,created_at,data_json) VALUES(?,?,?,?)",
            (u, pin_hash, created_at, json.dumps(data)),
        )
        conn.commit()
    return True, None

def verify_user(username: str, pin: str):
    u = (username or "").strip().lower()
    user = get_user(u)
    if not user:
        return False, "Account not found."
    if not check_pin_hash(pin, user["pin_hash"]):
        return False, "Wrong passcode."
    return True, None

def save_user_data(username: str, data: dict):
    init_db()
    u = (username or "").strip().lower()
    with _conn() as conn:
        conn.execute("UPDATE users SET data_json=? WHERE username=?", (json.dumps(data), u))
        conn.commit()

def leaderboard(limit: int = 10):
    init_db()
    with _conn() as conn:
        rows = conn.execute("SELECT username, data_json FROM users").fetchall()

    board = []
    for r in rows:
        try:
            d = json.loads(r["data_json"] or "{}")
        except Exception:
            d = {}
        stats = d.get("stats") or {}
        profile = d.get("profile") or {}

        nickname = clean_display_name(profile.get("nickname") or r["username"])
        avatar = (profile.get("avatar") or "✨")[:4]

        board.append(
            {
                "username": r["username"],
                "nickname": nickname,
                "avatar": avatar,
                "xp": int(stats.get("xp") or 0),
                "coins": int(stats.get("coins") or 0),
                "streak": int(stats.get("streak") or 0),
            }
        )

    board.sort(key=lambda x: x["xp"], reverse=True)
    return board[: max(1, int(limit))]
