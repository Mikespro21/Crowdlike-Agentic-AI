from __future__ import annotations

"""Trustless AI audit log (admin/bot-only visibility).

This is intentionally lightweight for the demo:
- Stored locally in the user's JSON state.
- Written by the orchestrator/coach whenever an agent proposes or executes actions.
"""

import datetime as _dt
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def ensure_audit_schema(user: Dict[str, Any]) -> None:
    user.setdefault("audit_log", [])
    if not isinstance(user.get("audit_log"), list):
        user["audit_log"] = []


def log_audit(
    user: Dict[str, Any],
    *,
    kind: str,
    msg: str,
    severity: str = "info",
    agent_id: Optional[str] = None,
    proposal_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    ensure_audit_schema(user)
    row = {
        "ts": _now_iso(),
        "kind": str(kind),
        "severity": str(severity),
        "msg": str(msg),
    }
    if agent_id is not None:
        row["agent_id"] = str(agent_id)
    if proposal_id is not None:
        row["proposal_id"] = str(proposal_id)
    if isinstance(meta, dict) and meta:
        row["meta"] = meta
    # newest-first
    user["audit_log"].insert(0, row)
    user["audit_log"] = user["audit_log"][:500]
