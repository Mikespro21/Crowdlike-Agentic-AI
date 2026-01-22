from __future__ import annotations

"""
Cloud-first storage backend (v1.6.0).

Streamlit Community Cloud containers have an ephemeral filesystem. For a demo UX that feels
stable *within a session* (and does not error in cloud), we store user data in Streamlit
session state by default.

This module keeps the same public API as earlier versions (load_user/save_user, etc.)
but no longer reads/writes local files.

If you later want persistence, implement a real backend (Postgres, Redis, etc.) and
swap these functions.
"""

import re
from typing import Any, Dict, Optional
from crowdlike.version import VERSION

try:
    import streamlit as st  # type: ignore
except Exception:  # pragma: no cover
    st = None  # type: ignore


_USERNAME_SAFE = re.compile(r"[^a-zA-Z0-9_\-]+")


def safe_username(name: str) -> str:
    """Normalize user identifiers into safe keys."""
    name = (name or "").strip()
    if not name:
        return "guest"
    name = _USERNAME_SAFE.sub("_", name)
    return name[:64].strip("_") or "guest"


def _store() -> Optional[Dict[str, Any]]:
    """Return the in-session store dict."""
    if st is None:
        return None
    if "_crowdlike_store" not in st.session_state:
        st.session_state["_crowdlike_store"] = {
            "users": {},         # user_id -> user dict
            "active_user": None, # user_id
            "meta": {
                "created_at": None,
            },
        }
    meta = st.session_state["_crowdlike_store"].get("meta") or {}
    if not meta.get("created_at"):
        meta["created_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
        st.session_state["_crowdlike_store"]["meta"] = meta
    return st.session_state["_crowdlike_store"]


def load_user(user_id: str) -> Optional[Dict[str, Any]]:
    s = _store()
    if not s:
        return None
    return (s.get("users") or {}).get(user_id)


def save_user(user_id: str, data: Dict[str, Any]) -> None:
    s = _store()
    if not s:
        return
    users = s.get("users") or {}
    users[user_id] = data
    s["users"] = users


def load_active_user() -> Optional[str]:
    s = _store()
    if not s:
        return None
    return s.get("active_user")


def save_active_user(user_id: Optional[str]) -> None:
    s = _store()
    if not s:
        return
    s["active_user"] = user_id


def export_debug_state() -> Dict[str, Any]:
    """Convenience for support debugging (safe to show in demo)."""
    s = _store() or {}
    users = s.get("users") or {}
    return {
        "active_user": s.get("active_user"),
        "user_count": len(users),
        "keys": sorted(list((s.get("meta") or {}).keys())),
    }
