from __future__ import annotations

import hashlib
import secrets
from typing import Any, Dict, Optional, Tuple

import streamlit as st

from .storage import load_active_user, load_user, save_active_user, save_user, safe_username
from .security import USERNAME_RE
from .game import ensure_user_schema, grant_xp, add_notification, log_activity, record_active_day


DEFAULT_AVATARS = ["🧊","🦋","🧠","🛰️","🪙","🦊","🦄","🐉","🧿","🪐","🌊","⚡","🫧","🧑‍🚀","🤖","🦈","🐙","🦜"]


def _hash_pin(pin: str, salt: str) -> str:
    pin = (pin or "").strip()
    return hashlib.sha256((salt + ":" + pin).encode("utf-8")).hexdigest()


def _new_user_state(username: str, avatar: str) -> Dict[str, Any]:
    u: Dict[str, Any] = {
        "username": username.strip() or "Member",
        "avatar": avatar or "🧊",
        "bio": "",
    }
    ensure_user_schema(u)
    return u


def _load_into_session(user_id: str, user: Dict[str, Any]) -> None:
    st.session_state["user_id"] = safe_username(user_id)
    st.session_state["user"] = ensure_user_schema(user)
    save_active_user(user_id)


def current_user() -> Optional[Dict[str, Any]]:
    u = st.session_state.get("user")
    if isinstance(u, dict):
        return u
    return None


def current_user_id() -> Optional[str]:
    u = st.session_state.get("user_id")
    if isinstance(u, str) and u.strip():
        return u
    return None


def save_current_user() -> None:
    uid = current_user_id()
    u = current_user()
    if uid and u:
        save_user(uid, u)


def logout() -> None:
    """Clear the current session user."""
    save_active_user(None)
    st.session_state.pop("user", None)
    st.session_state.pop("user_id", None)
    # Keep onboarding state (user may intentionally log out and re-enter as guest)


def require_login(app_name: str = "Crowdlike") -> Dict[str, Any]:
    """Return the current user, creating a session-scoped demo user if needed.

    Many pages call this at import-time. It must never fail due to missing
    local files or Streamlit Cloud's ephemeral filesystem.

    Behavior:
    - If a user exists in st.session_state, reuse it.
    - Otherwise, default to a demo user (Cloud-friendly).
    - For local dev, you can opt into the full login UI by setting
      DEMO_MODE=false in secrets.toml (optional).
    """

    u = current_user()
    if isinstance(u, dict):
        return ensure_user_schema(u)

    # Default to demo-only (safe for Streamlit Cloud). Avoid hard dependency on
    # secrets.toml, since st.secrets access can raise if the file is absent.
    demo_only = True
    try:
        demo_only = str(st.secrets.get("DEMO_MODE", "true")).lower() not in ("0", "false", "no")
    except Exception:
        demo_only = True

    if not demo_only:
        st.markdown(f"## {app_name}")
        _login_inner(app_name)
        st.stop()

    # Create a demo user for this session.
    uid = st.session_state.get("user_id")
    if not isinstance(uid, str) or not uid.strip():
        uid = "demo"

    user = _new_user_state("Demo", "🧑‍🚀")
    user.setdefault("onboarded", False)

    st.session_state["user_id"] = safe_username(uid)
    st.session_state["user"] = user

    # Best-effort: add a lightweight welcome event.
    try:
        if not user.get("_welcomed"):
            user["_welcomed"] = True
            grant_xp(user, 120, "Welcome", "Session started")
            add_notification(user, f"Welcome to {app_name}.", "success")
            record_active_day(user)
    except Exception:
        pass

    return user


def _login_inner(app_name: str) -> None:
    tab_login, tab_create = st.tabs(["Log in", "Create profile"])

    with tab_login:
        st.caption("Quick, local login (no email needed).")
        u = st.text_input("Username", key="auth_login_user")
        pin = st.text_input("PIN (optional)", type="password", key="auth_login_pin")
        cols = st.columns([1, 1, 1])
        with cols[0]:
            do = st.button("Log in", type="primary", key="auth_login_btn")
        with cols[1]:
            demo = st.button("Use demo", key="auth_demo_btn")
        with cols[2]:
            st.write("")

        if demo:
            uid = "demo"
            data = load_user(uid) or _new_user_state("Demo", "🧑‍🚀")
            # Give a tiny welcome reward
            if not data.get("_welcomed"):
                data["_welcomed"] = True
                grant_xp(data, 120, "Welcome", "Demo launch")
                add_notification(data, "Demo profile created on this device.", "success")
            save_user(uid, data)
            _load_into_session(uid, data)
            st.rerun()
        if do:
            raw = (u or "").strip().lower()
            if not USERNAME_RE.match(raw or ""):
                st.error("Username must be 3–20 chars: a–z, 0–9, underscore.")
                return
            uid = safe_username(raw)
            data = load_user(uid)

            if not data:
                st.error("No profile found. Use **Create profile** first.")
            else:
                auth = data.get("auth", {}) if isinstance(data.get("auth"), dict) else {}
                salt = str(auth.get("salt") or "")
                want_hash = str(auth.get("pin_hash") or "")
                if want_hash:
                    if not pin:
                        st.error("This profile has a PIN. Enter it to log in.")
                    else:
                        if _hash_pin(pin, salt) != want_hash:
                            st.error("Wrong PIN.")
                        else:
                            _load_into_session(uid, data)
                            log_activity(data, "Logged in", icon="🔓")
                            save_user(uid, data)
                            st.rerun()
                else:
                    # No PIN required
                    _load_into_session(uid, data)
                    log_activity(data, "Logged in", icon="🔓")
                    save_user(uid, data)
                    st.rerun()

    with tab_create:
        st.caption("Create a profile (saved locally).")
        new_u = st.text_input("Choose a username", key="auth_new_user")
        colA, colB = st.columns([1, 1])
        with colA:
            avatar = st.selectbox("Avatar", DEFAULT_AVATARS, key="auth_avatar")
        with colB:
            new_pin = st.text_input("Set a PIN (optional)", type="password", key="auth_new_pin")
        bio = st.text_area("Bio (optional)", placeholder="What are you building?", key="auth_new_bio")

        create = st.button("Create profile", type="primary", key="auth_create_btn")
        if create:
            raw = (new_u or "").strip().lower()
            if not USERNAME_RE.match(raw or ""):
                st.error("Username must be 3–20 chars: a–z, 0–9, underscore.")
                return
            uid = safe_username(raw)
            if uid in ("member", "admin"):
                st.error("Pick a different username.")
                return

            if load_user(uid):
                st.error("That username already exists on this device. Try logging in instead.")
                return

            data = _new_user_state(raw, avatar)
            data["bio"] = (bio or "").strip()
            # Auth block
            if new_pin.strip():
                salt = secrets.token_hex(8)
                data["auth"] = {"salt": salt, "pin_hash": _hash_pin(new_pin, salt)}
            else:
                data["auth"] = {"salt": "", "pin_hash": ""}

            grant_xp(data, 200, "Welcome", "Profile created")
            add_notification(data, "Profile saved. You can edit it anytime in Profile.", "success")

            save_user(uid, data)
            _load_into_session(uid, data)
            st.rerun()
