
from __future__ import annotations

import re

# Usernames for accounts + friend handles (prevents injection-looking inputs)
USERNAME_RE = re.compile(r"^[a-z0-9_]{3,20}$")

# Display name: allow letters, numbers, spaces, underscore, hyphen, emoji.
# But remove angle brackets to prevent HTML payloads from ever being stored.
def clean_display_name(name: str, max_len: int = 24) -> str:
    s = (name or "").strip()
    s = s.replace("<", "").replace(">", "")
    s = re.sub(r"[\r\n\t]+", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    return s or "User"

def clean_username(username: str) -> str:
    u = (username or "").strip().lower()
    if not USERNAME_RE.match(u):
        raise ValueError("Use 3–20 chars: a-z, 0-9, underscore.")
    return u

EVM_ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

def is_evm_address(addr: str) -> bool:
    return bool(EVM_ADDR_RE.match((addr or "").strip()))

def normalize_evm_address(addr: str) -> str:
    a = (addr or "").strip()
    if a == "":
        return ""
    if not is_evm_address(a):
        raise ValueError("Not a valid EVM address (must be 0x + 40 hex).")
    return a

def short_addr(addr: str) -> str:
    a = (addr or "").strip()
    if not is_evm_address(a):
        return a[:14] + ("…" if len(a) > 14 else "")
    return f"{a[:6]}…{a[-4:]}"
