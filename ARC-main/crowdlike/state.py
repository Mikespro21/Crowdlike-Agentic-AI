from __future__ import annotations
import time
from typing import Dict, Any
import streamlit as st

DEFAULT_STATE: Dict[str, Any] = {
    "xp": 0,
    "coins": 250,
    "gems": 5,
    "streak_days": 0,
    "last_active_day": "",
    "inventory": {},     # item_id -> {"name":..., "kind":..., "ts":...}
    "equipped": {},      # slot -> item_id
    "friends": [],       # usernames
    "trade_portfolio": None,
}

def _today_ymd() -> str:
    return time.strftime("%Y-%m-%d")

def init_state():
    if "user_state" not in st.session_state:
        st.session_state.user_state = dict(DEFAULT_STATE)

def get_state() -> Dict[str, Any]:
    init_state()
    return st.session_state.user_state

def set_state(new_state: Dict[str, Any]) -> None:
    st.session_state.user_state = new_state

def add_xp(amount: int, reason: str = "activity") -> None:
    s = get_state()
    amount = max(0, int(amount))
    s["xp"] = int(s.get("xp", 0)) + amount
    # “coins for activity” pattern similar to your old gamified state approach :contentReference[oaicite:3]{index=3}
    s["coins"] = int(s.get("coins", 0)) + max(0, amount // 10)
    s["last_reason"] = reason
    s["last_xp_gain"] = amount
    set_state(s)

def spend(currency: str, amount: int) -> bool:
    s = get_state()
    amount = int(amount)
    if amount <= 0:
        return True
    if int(s.get(currency, 0)) < amount:
        return False
    s[currency] = int(s.get(currency, 0)) - amount
    set_state(s)
    return True

def earn(currency: str, amount: int) -> None:
    s = get_state()
    s[currency] = int(s.get(currency, 0)) + int(amount)
    set_state(s)

def level_from_xp(xp: int) -> int:
    # simple curve
    xp = max(0, int(xp))
    lvl = 1
    need = 120
    while xp >= need:
        xp -= need
        lvl += 1
        need = int(need * 1.18)
        if lvl > 99:
            break
    return lvl
