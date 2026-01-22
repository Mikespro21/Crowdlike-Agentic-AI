
from __future__ import annotations

import time

def _now() -> int:
    return int(time.time())

def ensure(d: dict):
    d.setdefault("ledger", [])
    d.setdefault("activity", [])
    d.setdefault("stats", {})
    d["stats"].setdefault("xp", 0)
    d["stats"].setdefault("coins", 0)
    d["stats"].setdefault("gems", 0)

def add_activity(d: dict, text: str, tone: str = "blue", icon: str = "✨"):
    ensure(d)
    d["activity"].insert(0, {"ts": _now(), "text": text, "tone": tone, "icon": icon})
    d["activity"] = d["activity"][:80]

def change(
    d: dict,
    *,
    dxp: int = 0,
    dcoins: int = 0,
    dgems: int = 0,
    reason: str,
    kind: str = "system",
    tone: str = "blue",
    icon: str = "✨",
    allow_negative: bool = False,
) -> tuple[bool, str | None]:
    """
    Single source of truth for economy changes.
    Prevents 'mystery math' by logging every change with a reason.
    """
    ensure(d)
    s = d["stats"]

    dxp = int(dxp)
    dcoins = int(dcoins)
    dgems = int(dgems)

    # Balance checks
    if not allow_negative:
        if dcoins < 0 and int(s.get("coins", 0)) + dcoins < 0:
            return False, "Not enough coins."
        if dgems < 0 and int(s.get("gems", 0)) + dgems < 0:
            return False, "Not enough gems."

    before = {"xp": int(s.get("xp", 0)), "coins": int(s.get("coins", 0)), "gems": int(s.get("gems", 0))}
    s["xp"] = before["xp"] + dxp
    s["coins"] = before["coins"] + dcoins
    s["gems"] = before["gems"] + dgems

    entry = {
        "ts": _now(),
        "kind": kind,
        "reason": reason,
        "dxp": dxp,
        "dcoins": dcoins,
        "dgems": dgems,
        "after": {"xp": s["xp"], "coins": s["coins"], "gems": s["gems"]},
    }
    d["ledger"].insert(0, entry)
    d["ledger"] = d["ledger"][:200]

    # Friendly activity
    parts = []
    if dxp:
        parts.append(f"{dxp:+d} XP")
    if dcoins:
        parts.append(f"{dcoins:+d} coins")
    if dgems:
        parts.append(f"{dgems:+d} gems")
    if parts:
        add_activity(d, f"{reason} ({', '.join(parts)})", tone=tone, icon=icon)
    else:
        add_activity(d, reason, tone=tone, icon=icon)

    return True, None
